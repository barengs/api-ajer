from rest_framework import generics, permissions, status, filters
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import Q, F, Count
from django_filters.rest_framework import DjangoFilterBackend

# drf-spectacular imports
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import (
    Forum, ForumPost, ForumReply, ForumVote, ForumSubscription,
    ForumReportedContent, ForumActivity
)
from .serializers import (
    ForumSerializer, ForumPostSerializer, ForumPostDetailSerializer,
    ForumPostCreateSerializer, ForumReplySerializer, ForumReplyCreateSerializer,
    ForumVoteSerializer, ForumSubscriptionSerializer, ForumReportSerializer
)
from courses.models import Course, Enrollment
from courses.permissions import IsEnrolledOrInstructor
from accounts.models import User


@extend_schema(
    tags=['Forums'],
    summary='Daftar Forum Kursus',
    description='''
    Mendapatkan semua forum yang tersedia untuk kursus tertentu.
    
    **Access Control berdasarkan role:**
    - **Instructor**: Melihat semua forum (termasuk private dan inactive)
    - **Student**: Hanya forum yang aktif dan accessible
    
    **Filter untuk Student:**
    - Harus enrolled di kursus
    - Hanya forum yang is_active=True
    - Private forum hanya jika enrolled
    - Untuk structured course: filtered by batch
    
    **Forum Types:**
    - **Public**: Dapat dilihat semua enrolled student
    - **Private**: Hanya untuk student tertentu atau batch
    - **General**: Forum diskusi umum
    - **Q&A**: Forum tanya jawab
    ''',
    parameters=[
        OpenApiParameter(
            name='course_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID kursus yang akan dilihat forum-nya'
        )
    ],
    responses={
        200: {
            'description': 'Daftar forum berhasil diambil',
            'content': {
                'application/json': {
                    'example': [
                        {
                            'id': 1,
                            'name': 'Diskusi Umum',
                            'description': 'Forum untuk diskusi umum tentang kursus',
                            'forum_type': 'general',
                            'is_private': False,
                            'is_active': True,
                            'sort_order': 1,
                            'posts_count': 25,
                            'latest_post': {
                                'id': 10,
                                'title': 'Pertanyaan tentang Python Functions',
                                'author': {
                                    'full_name': 'John Doe'
                                },
                                'created_at': '2024-01-15T10:30:00Z'
                            },
                            'course': {
                                'id': 1,
                                'title': 'Python untuk Pemula'
                            }
                        }
                    ]
                }
            }
        },
        403: {
            'description': 'Forbidden - Akses terbatas berdasarkan enrollment'
        },
        404: {
            'description': 'Course tidak ditemukan'
        }
    }
)
class CourseForumListView(generics.ListAPIView):
    """List forums for a course"""
    serializer_class = ForumSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore[override]
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        
        # Check if user has access to the course
        if course.instructor == self.request.user:
            # Instructor sees all forums
            queryset = Forum.objects.filter(course=course)
        else:
            # Students see only public forums they have access to
            try:
                enrollment = Enrollment.objects.get(
                    student=self.request.user,
                    course=course,
                    is_active=True
                )
                
                queryset = Forum.objects.filter(course=course, is_active=True)
                
                # Filter by batch for structured courses
                if course.course_type == Course.CourseType.STRUCTURED and enrollment.batch:
                    queryset = queryset.filter(
                        Q(batch=enrollment.batch) | Q(batch__isnull=True)
                    )
                
                # Filter out private forums if not enrolled
                if not enrollment:
                    queryset = queryset.filter(is_private=False)
                
            except Enrollment.DoesNotExist:
                # Not enrolled, only see public forums
                queryset = Forum.objects.filter(course=course, is_active=True, is_private=False)
        
        return queryset.order_by('sort_order', 'name')


@extend_schema(
    tags=['Forums'],
    summary='Posts Forum',
    description='''
    Mengelola posts dalam forum tertentu (list dan create).
    
    **GET Request:**
    - List semua posts dalam forum
    - Hanya posts yang approved yang ditampilkan
    - Support search, filter, dan sorting
    
    **POST Request:**
    - Membuat post baru dalam forum
    - Auto-subscribe pembuat ke post
    - Track activity untuk analytics
    
    **Post Types:**
    - **Discussion**: Post diskusi umum
    - **Question**: Post tanya jawab
    - **Announcement**: Pengumuman (instructor only)
    
    **Filtering Options:**
    - type: Filter berdasarkan post type
    - status: Untuk questions (resolved/unresolved)
    
    **Search & Ordering:**
    - Search: title, content, author username
    - Order: created_at, last_activity_at, upvotes, view_count
    ''',
    parameters=[
        OpenApiParameter(
            name='forum_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID forum yang akan dilihat posts-nya'
        ),
        OpenApiParameter(
            name='type',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter berdasarkan jenis post',
            enum=['discussion', 'question', 'announcement']
        ),
        OpenApiParameter(
            name='status',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter status untuk questions',
            enum=['resolved', 'unresolved']
        ),
        OpenApiParameter(
            name='search',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Search dalam title, content, atau author'
        ),
        OpenApiParameter(
            name='ordering',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Sorting berdasarkan field tertentu',
            enum=['created_at', '-created_at', 'last_activity_at', '-last_activity_at', 'upvotes', '-upvotes']
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'title': {
                    'type': 'string',
                    'description': 'Judul post',
                    'example': 'Bagaimana cara menggunakan Django ORM?'
                },
                'content': {
                    'type': 'string',
                    'description': 'Konten post dalam HTML',
                    'example': '<p>Saya kesulitan memahami konsep ORM...</p>'
                },
                'post_type': {
                    'type': 'string',
                    'enum': ['discussion', 'question', 'announcement'],
                    'description': 'Jenis post'
                },
                'tags': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Tags untuk kategorisasi'
                }
            },
            'required': ['title', 'content', 'post_type']
        }
    },
    responses={
        200: {
            'description': 'Daftar posts berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'count': 50,
                        'results': [
                            {
                                'id': 1,
                                'title': 'Bagaimana cara menggunakan Django ORM?',
                                'content_preview': 'Saya kesulitan memahami konsep ORM...',
                                'post_type': 'question',
                                'is_pinned': False,
                                'upvotes': 5,
                                'downvotes': 0,
                                'view_count': 25,
                                'replies_count': 3,
                                'is_question_resolved': False,
                                'author': {
                                    'id': 1,
                                    'full_name': 'John Doe',
                                    'profile_picture': 'http://localhost:8000/media/profiles/john.jpg'
                                },
                                'created_at': '2024-01-15T10:30:00Z',
                                'last_activity_at': '2024-01-15T14:30:00Z',
                                'tags': ['django', 'orm', 'database']
                            }
                        ]
                    }
                }
            }
        },
        201: {
            'description': 'Post berhasil dibuat'
        },
        403: {
            'description': 'Forbidden - Tidak memiliki akses ke forum'
        }
    }
)
class ForumPostListView(generics.ListCreateAPIView):
    """List and create forum posts"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content', 'author__username']
    ordering_fields = ['created_at', 'last_activity_at', 'upvotes', 'view_count']
    ordering = ['-is_pinned', '-last_activity_at']
    
    def get_queryset(self):  # type: ignore[override]
        forum_id = self.kwargs.get('forum_id')
        forum = get_object_or_404(Forum, id=forum_id)
        
        # Check access to forum
        if not self._check_forum_access(forum):
            return ForumPost.objects.none()
        
        queryset = ForumPost.objects.filter(forum=forum, is_approved=True).select_related(
            'author', 'forum'
        ).prefetch_related('votes')
        
        # Filter by post type if specified
        post_type = getattr(self.request, 'query_params', self.request.GET).get('type')
        if post_type:
            queryset = queryset.filter(post_type=post_type)
        
        # Filter by status for questions
        if post_type == 'question':
            status_filter = getattr(self.request, 'query_params', self.request.GET).get('status')
            if status_filter == 'resolved':
                queryset = queryset.filter(is_question_resolved=True)
            elif status_filter == 'unresolved':
                queryset = queryset.filter(is_question_resolved=False)
        
        return queryset
    
    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == 'POST':
            return ForumPostCreateSerializer
        return ForumPostSerializer
    
    def perform_create(self, serializer):
        post = serializer.save()
        
        # Track activity
        ForumActivity.objects.create(
            user=self.request.user,
            forum=post.forum,
            activity_type=ForumActivity.ActivityType.POST_CREATED,
            post=post,
            metadata={'post_type': post.post_type}
        )
        
        # Auto-subscribe author to the post
        ForumSubscription.objects.create(
            user=self.request.user,
            post=post
        )
    
    def _check_forum_access(self, forum):
        """Check if user has access to forum"""
        user = self.request.user
        
        if forum.course.instructor == user:
            return True
        
        try:
            enrollment = Enrollment.objects.get(
                student=user,
                course=forum.course,
                is_active=True
            )
            
            # Check batch access for structured courses
            if forum.batch and enrollment.batch and forum.batch != enrollment.batch:
                return False
            
            return not forum.is_private or enrollment is not None
            
        except Enrollment.DoesNotExist:
            return not forum.is_private


class ForumPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Forum post detail view"""
    serializer_class = ForumPostDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore[override]
        return ForumPost.objects.select_related(
            'author', 'forum', 'accepted_answer'
        ).prefetch_related('votes')
    
    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()
        
        # Check forum access
        if not self._check_forum_access(post.forum):
            return Response(
                {'error': 'You do not have access to this forum'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Increment view count
        ForumPost.objects.filter(id=post.id).update(view_count=F('view_count') + 1)
        
        # Track activity
        ForumActivity.objects.create(
            user=request.user,
            forum=post.forum,
            activity_type=ForumActivity.ActivityType.POST_VIEWED,
            post=post
        )
        
        return super().retrieve(request, *args, **kwargs)
    
    def get_object(self):
        obj = super().get_object()
        
        # Check if user can edit
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if not self._can_edit_post(obj):
                raise PermissionDenied("You cannot edit this post")
        
        return obj
    
    def _check_forum_access(self, forum):
        """Check if user has access to forum"""
        user = self.request.user
        
        if forum.course.instructor == user:
            return True
        
        try:
            enrollment = Enrollment.objects.get(
                student=user,
                course=forum.course,
                is_active=True
            )
            return not forum.is_private
        except Enrollment.DoesNotExist:
            return not forum.is_private
    
    def _can_edit_post(self, post):
        """Check if user can edit post"""
        user = self.request.user
        return (post.author == user or 
                post.forum.course.instructor == user or
                getattr(user, 'role', None) == User.UserRole.ADMIN)


class ForumReplyListView(generics.ListCreateAPIView):
    """List and create forum post replies"""
    serializer_class = ForumReplySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore[override]
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(ForumPost, id=post_id)
        
        # Check access
        if not self._check_forum_access(post.forum):
            return ForumReply.objects.none()
        
        return ForumReply.objects.filter(
            post=post,
            is_approved=True,
            parent__isnull=True  # Top-level replies only
        ).select_related('author').order_by('-is_answer', 'created_at')
    
    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == 'POST':
            return ForumReplyCreateSerializer
        return ForumReplySerializer
    
    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(ForumPost, id=post_id)
        
        # Check access
        if not self._check_forum_access(post.forum):
            raise PermissionDenied("You do not have access to this forum")
        
        reply = serializer.save(context={'post': post, 'request': self.request})
        
        # Track activity
        ForumActivity.objects.create(
            user=self.request.user,
            forum=post.forum,
            activity_type=ForumActivity.ActivityType.REPLY_CREATED,
            post=post,
            reply=reply
        )
        
        # Update post activity timestamp
        post.update_activity()
    
    def _check_forum_access(self, forum):
        """Check if user has access to forum"""
        user = self.request.user
        
        if forum.course.instructor == user:
            return True
        
        try:
            Enrollment.objects.get(
                student=user,
                course=forum.course,
                is_active=True
            )
            return True
        except Enrollment.DoesNotExist:
            return not forum.is_private


class ForumReplyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Forum reply detail view"""
    serializer_class = ForumReplySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore[override]
        return ForumReply.objects.select_related('author', 'post__forum')
    
    def get_object(self):
        obj = super().get_object()
        
        # Check access
        if not self._check_forum_access(obj.post.forum):
            raise PermissionDenied("You do not have access to this forum")
        
        # Check if user can edit
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if not self._can_edit_reply(obj):
                raise PermissionDenied("You cannot edit this reply")
        
        return obj
    
    def _check_forum_access(self, forum):
        """Check if user has access to forum"""
        user = self.request.user
        
        if forum.course.instructor == user:
            return True
        
        try:
            Enrollment.objects.get(
                student=user,
                course=forum.course,
                is_active=True
            )
            return True
        except Enrollment.DoesNotExist:
            return not forum.is_private
    
    def _can_edit_reply(self, reply):
        """Check if user can edit reply"""
        user = self.request.user
        return (reply.author == user or 
                reply.post.forum.course.instructor == user or
                getattr(user, 'role', None) == User.UserRole.ADMIN)


@extend_schema(
    tags=['Forums'],
    summary='Vote Post Forum',
    description='''
    Memberikan vote (upvote/downvote) pada forum post.
    
    **Vote Types:**
    - **upvote**: Mendukung/menyukai post
    - **downvote**: Tidak mendukung post
    
    **Vote Logic:**
    - User dapat mengubah vote yang sudah ada
    - Vote yang sama akan membatalkan vote
    - Vote berbeda akan mengganti vote sebelumnya
    
    **Access Control:**
    - Memerlukan enrollment aktif di kursus
    - Tidak dapat vote post sendiri
    - Instructor dapat vote semua posts
    
    **Activity Tracking:**
    Sistem akan mencatat aktivitas voting untuk analytics.
    ''',
    parameters=[
        OpenApiParameter(
            name='post_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID post yang akan di-vote'
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'vote_type': {
                    'type': 'string',
                    'enum': ['upvote', 'downvote'],
                    'description': 'Jenis vote yang diberikan'
                }
            },
            'required': ['vote_type']
        }
    },
    examples=[
        OpenApiExample(
            'Upvote Post',
            value={'vote_type': 'upvote'},
            request_only=True
        ),
        OpenApiExample(
            'Downvote Post',
            value={'vote_type': 'downvote'},
            request_only=True
        )
    ],
    responses={
        200: {
            'description': 'Vote berhasil dicatat',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Vote recorded successfully'
                    }
                }
            }
        },
        403: {
            'description': 'Forbidden - Tidak memiliki akses ke forum'
        },
        400: {
            'description': 'Bad Request - Vote type tidak valid'
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def vote_post(request, post_id):
    """Vote on a forum post"""
    post = get_object_or_404(ForumPost, id=post_id)
    
    # Check access
    if post.forum.course.instructor != request.user:
        try:
            Enrollment.objects.get(
                student=request.user,
                course=post.forum.course,
                is_active=True
            )
        except Enrollment.DoesNotExist:
            if post.forum.is_private:
                return Response(
                    {'error': 'You do not have access to this forum'},
                    status=status.HTTP_403_FORBIDDEN
                )
    
    serializer = ForumVoteSerializer(
        data=request.data,
        context={'request': request, 'post': post}
    )
    serializer.is_valid(raise_exception=True)
    vote_data = serializer.save()
    
    # Track activity - get vote_type from request data since validation passed
    vote_type = request.data.get('vote_type', 'unknown')
    ForumActivity.objects.create(
        user=request.user,
        forum=post.forum,
        activity_type=ForumActivity.ActivityType.VOTE_CAST,
        post=post,
        metadata={'vote_type': vote_type}
    )
    
    return Response({'message': 'Vote recorded successfully'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def vote_reply(request, reply_id):
    """Vote on a forum reply"""
    reply = get_object_or_404(ForumReply, id=reply_id)
    
    # Check access
    if reply.post.forum.course.instructor != request.user:
        try:
            Enrollment.objects.get(
                student=request.user,
                course=reply.post.forum.course,
                is_active=True
            )
        except Enrollment.DoesNotExist:
            if reply.post.forum.is_private:
                return Response(
                    {'error': 'You do not have access to this forum'},
                    status=status.HTTP_403_FORBIDDEN
                )
    
    serializer = ForumVoteSerializer(
        data=request.data,
        context={'request': request, 'reply': reply}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    
    return Response({'message': 'Vote recorded successfully'})


@extend_schema(
    tags=['Forums'],
    summary='Terima Jawaban',
    description='''
    Menandai reply sebagai jawaban yang diterima untuk question post.
    
    **Siapa yang dapat menerima jawaban:**
    - Author dari question post
    - Instructor dari kursus
    
    **Efek dari accept answer:**
    1. Reply ditandai sebagai is_answer=True
    2. Post question ditandai resolved
    3. Post mendapat accepted_answer reference
    4. Reply author mendapat reputation points
    
    **Validasi:**
    - Hanya dapat digunakan untuk post type 'question'
    - Hanya dapat accept satu jawaban per question
    - Accept answer baru akan replace yang lama
    ''',
    parameters=[
        OpenApiParameter(
            name='reply_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID reply yang akan diterima sebagai jawaban'
        )
    ],
    responses={
        200: {
            'description': 'Jawaban berhasil diterima',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Answer accepted successfully'
                    }
                }
            }
        },
        403: {
            'description': 'Forbidden - Hanya author question atau instructor',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'Only question author or instructor can accept answers'
                    }
                }
            }
        },
        400: {
            'description': 'Bad Request - Bukan question post',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'Can only accept answers for questions'
                    }
                }
            }
        },
        404: {
            'description': 'Reply tidak ditemukan'
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def accept_answer(request, reply_id):
    """Accept reply as answer (question author or instructor only)"""
    reply = get_object_or_404(ForumReply, id=reply_id)
    post = reply.post
    
    # Check if user can accept answer
    if (post.author != request.user and 
        post.forum.course.instructor != request.user):
        return Response(
            {'error': 'Only question author or instructor can accept answers'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if it's a question
    if post.post_type != ForumPost.PostType.QUESTION:
        return Response(
            {'error': 'Can only accept answers for questions'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Mark reply as accepted answer
    reply.is_answer = True
    reply.save()
    
    # Update post
    post.accepted_answer = reply
    post.is_question_resolved = True
    post.save()
    
    return Response({'message': 'Answer accepted successfully'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def subscribe_to_post(request, post_id):
    """Subscribe to forum post notifications"""
    post = get_object_or_404(ForumPost, id=post_id)
    
    # Check access
    if post.forum.course.instructor != request.user:
        try:
            Enrollment.objects.get(
                student=request.user,
                course=post.forum.course,
                is_active=True
            )
        except Enrollment.DoesNotExist:
            if post.forum.is_private:
                return Response(
                    {'error': 'You do not have access to this forum'},
                    status=status.HTTP_403_FORBIDDEN
                )
    
    subscription, created = ForumSubscription.objects.get_or_create(
        user=request.user,
        post=post
    )
    
    if created:
        # Track activity
        ForumActivity.objects.create(
            user=request.user,
            forum=post.forum,
            activity_type=ForumActivity.ActivityType.POST_SUBSCRIBED,
            post=post
        )
        return Response({'message': 'Subscribed to post notifications'})
    else:
        subscription.delete()
        return Response({'message': 'Unsubscribed from post notifications'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def report_content(request, content_type, content_id):
    """Report inappropriate content"""
    if content_type not in ['post', 'reply']:
        return Response(
            {'error': 'Invalid content type'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if content_type == 'post':
        content_obj = get_object_or_404(ForumPost, id=content_id)
        context = {'post': content_obj}
    else:
        content_obj = get_object_or_404(ForumReply, id=content_id)
        context = {'reply': content_obj}
    
    serializer = ForumReportSerializer(
        data=request.data,
        context=dict(context, request=request)
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    
    return Response({'message': 'Content reported successfully'})


class UserForumSubscriptionListView(generics.ListAPIView):
    """User's forum subscriptions"""
    serializer_class = ForumSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore[override]
        return ForumSubscription.objects.filter(
            user=self.request.user
        ).select_related('post__forum__course').order_by('-created_at')


@extend_schema(
    tags=['Forums'],
    summary='Pencarian Forum',
    description='''
    Mencari posts di seluruh forum yang dapat diakses user.
    
    **Scope Pencarian:**
    - Mencari dalam title dan content posts
    - Hanya forum dari kursus yang user miliki akses
    - Instructor: dapat search di kursus yang diajar
    - Student: dapat search di kursus yang enrolled
    
    **Search Results:**
    - Maksimal 20 hasil terbaru
    - Include snippet content (200 karakter pertama)
    - Include context info (author, forum, course)
    
    **Use Cases:**
    - Global search di student dashboard
    - Quick access ke discussions relevan
    - Knowledge base search
    ''',
    parameters=[
        OpenApiParameter(
            name='q',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Query pencarian untuk posts',
            required=True
        )
    ],
    responses={
        200: {
            'description': 'Hasil pencarian berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'results': [
                            {
                                'type': 'post',
                                'id': 1,
                                'title': 'Bagaimana cara menggunakan Django ORM?',
                                'content_snippet': 'Saya kesulitan memahami konsep ORM dalam Django. Apakah ada tutorial yang bagus untuk dipelajari?...',
                                'author': 'John Doe',
                                'forum': 'Q&A Python',
                                'course': 'Python untuk Pemula',
                                'created_at': '2024-01-15T10:30:00Z'
                            },
                            {
                                'type': 'post',
                                'id': 5,
                                'title': 'Tips optimasi Django query',
                                'content_snippet': 'Berikut beberapa tips untuk mengoptimalkan query Django ORM yang sering diabaikan...',
                                'author': 'Dr. Jane Smith',
                                'forum': 'Diskusi Umum',
                                'course': 'Advanced Django',
                                'created_at': '2024-01-14T15:20:00Z'
                            }
                        ]
                    }
                }
            }
        },
        400: {
            'description': 'Bad Request - Query kosong',
            'content': {
                'application/json': {
                    'example': {
                        'results': []
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def forum_search(request):
    """Search across forums and posts"""
    query = getattr(request, 'query_params', request.GET).get('q', '')
    if not query:
        return Response({'results': []})
    
    # Get courses user has access to
    user_courses = set()
    
    # Add instructor courses
    if getattr(request.user, 'role', None) == User.UserRole.INSTRUCTOR:
        user_courses.update(
            Course.objects.filter(instructor=request.user).values_list('id', flat=True)
        )
    
    # Add enrolled courses
    user_courses.update(
        Enrollment.objects.filter(
            student=request.user,
            is_active=True
        ).values_list('course_id', flat=True)
    )
    
    # Search posts
    posts = ForumPost.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query),
        forum__course_id__in=user_courses,
        is_approved=True
    ).select_related('author', 'forum')[:20]
    
    results = [{
        'type': 'post',
        'id': post.pk,
        'title': post.title,
        'content_snippet': post.content[:200] + '...' if len(post.content) > 200 else post.content,
        'author': post.author.full_name or post.author.username,
        'forum': post.forum.name,
        'course': post.forum.course.title,
        'created_at': post.created_at
    } for post in posts]
    
    return Response({'results': results})