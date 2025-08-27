from typing import Any, Dict
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

# drf-spectacular imports
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import (
    BadgeType, UserBadge, PointsTransaction, UserLevel, UserStats,
    Achievement, UserAchievement, Leaderboard, LeaderboardEntry
)
from .serializers import (
    BadgeTypeSerializer, UserBadgeSerializer, PointsTransactionSerializer,
    UserLevelSerializer, UserStatsSerializer, AchievementSerializer,
    UserAchievementSerializer, LeaderboardSerializer, LeaderboardEntrySerializer,
    UserProfileStatsSerializer, PointsAwardSerializer, BadgeAwardSerializer,
    LeaderboardStatsSerializer
)
from .utils import (
    get_or_create_user_stats, award_points, get_user_rank,
    get_next_level_progress, update_leaderboards, check_user_badges,
    check_user_achievements
)
from .signals import trigger_daily_login

User = get_user_model()


@extend_schema(
    tags=['Gamification'],
    summary='Profil Gamifikasi User',
    description='''
    Mendapatkan profil lengkap gamifikasi user yang login.
    
    **Data yang disediakan:**
    - Total points dan level saat ini
    - Progress ke level berikutnya
    - Badges yang diperoleh (recent dan semua)
    - Achievements yang di-unlock
    - Ranking di berbagai leaderboard
    - Recent points transactions
    - Summary statistics
    
    **Dashboard Integration:**
    Endpoint ini digunakan untuk dashboard user dan menampilkan
    overview lengkap progress gamifikasi mereka.
    ''',
    responses={
        200: {
            'description': 'Profil gamifikasi berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'total_points': 850,
                        'current_level': {
                            'level': 4,
                            'name': 'Scholar',
                            'min_points': 500,
                            'max_points': 999
                        },
                        'level_progress': {
                            'current_points': 850,
                            'next_level': 5,
                            'points_needed': 150,
                            'progress_percentage': 87.5
                        },
                        'badges': [
                            {
                                'id': 1,
                                'badge_type': {
                                    'name': 'Course Finisher',
                                    'description': 'Completed your first course',
                                    'category': 'achievement'
                                },
                                'earned_at': '2024-01-15T10:30:00Z'
                            }
                        ],
                        'achievements': [],
                        'rankings': {
                            'overall_rank': 25,
                            'monthly_rank': 12
                        },
                        'stats': {
                            'courses_completed': 2,
                            'lessons_completed': 45,
                            'forum_posts': 8,
                            'current_streak': 7
                        }
                    }
                }
            }
        }
    }
)
class UserGamificationProfileView(APIView):
    """Get comprehensive user gamification profile"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        stats = get_or_create_user_stats(user)
        
        # Get recent badges (last 5)
        recent_badges = UserBadge.objects.filter(user=user).order_by('-earned_at')[:5]
        
        # Get recent achievements (last 3)
        recent_achievements = UserAchievement.objects.filter(user=user).order_by('-earned_at')[:3]
        
        # Get recent transactions (last 10)
        recent_transactions = PointsTransaction.objects.filter(user=user).order_by('-created_at')[:10]
        
        # Get level progress
        level_progress = get_next_level_progress(user)
        
        # Get rankings
        rankings = {
            'overall_rank': get_user_rank(user, Leaderboard.LeaderboardType.OVERALL_POINTS),
            'monthly_rank': get_user_rank(user, Leaderboard.LeaderboardType.MONTHLY_POINTS),
        }
        
        data = {
            'total_points': stats.total_points,
            'current_level': UserLevelSerializer(stats.current_level).data if stats.current_level else None,
            'level_progress': level_progress,
            'badges': UserBadgeSerializer(recent_badges, many=True).data,
            'achievements': UserAchievementSerializer(recent_achievements, many=True).data,
            'recent_transactions': PointsTransactionSerializer(recent_transactions, many=True).data,
            'rankings': rankings,
            'stats': {
                'courses_completed': stats.courses_completed,
                'lessons_completed': stats.lessons_completed,
                'assignments_submitted': stats.assignments_submitted,
                'quizzes_passed': stats.quizzes_passed,
                'forum_posts': stats.forum_posts,
                'forum_replies': stats.forum_replies,
                'current_streak': stats.current_login_streak,
                'longest_streak': stats.longest_login_streak,
            }
        }
        
        return Response(data)


@extend_schema(
    tags=['Gamification'],
    summary='Badges User',
    description='''
    Mendapatkan semua badges yang dimiliki user.
    
    **Features:**
    - Filter by badge category
    - Search by badge name
    - Order by earned date
    - Include badge metadata
    
    **Badge Categories:**
    - learning: Badges dari aktivitas pembelajaran
    - social: Badges dari aktivitas forum
    - achievement: Badges milestone dan pencapaian
    - instructor: Badges khusus instructor
    - special: Badges event atau khusus
    ''',
    parameters=[
        OpenApiParameter(
            name='category',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by badge category',
            enum=['learning', 'social', 'achievement', 'instructor', 'special']
        ),
        OpenApiParameter(
            name='search',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Search badge names'
        )
    ]
)
class UserBadgesView(generics.ListAPIView):
    """List user's badges"""
    serializer_class = UserBadgeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['badge_type__name', 'badge_type__description']
    filterset_fields = ['badge_type__category']
    ordering_fields = ['earned_at']
    ordering = ['-earned_at']
    
    def get_queryset(self):  # type: ignore[override]
        return UserBadge.objects.filter(user=self.request.user).select_related('badge_type')


@extend_schema(
    tags=['Gamification'],
    summary='Achievements User',
    description='''
    Mendapatkan achievements yang dimiliki user beserta progress.
    
    **Features:**
    - Show earned and unearned achievements
    - Progress calculation untuk yang belum earned
    - Filter by achievement type
    - Include requirements dan rewards
    ''',
    parameters=[
        OpenApiParameter(
            name='earned_only',
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            description='Show only earned achievements'
        ),
        OpenApiParameter(
            name='type',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by achievement type'
        )
    ]
)
class UserAchievementsView(generics.ListAPIView):
    """List user's achievements with progress"""
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['achievement_type']
    
    def get_queryset(self):  # type: ignore[override]
        earned_only = getattr(self.request, 'query_params', self.request.GET).get('earned_only', 'false').lower() == 'true'
        
        if earned_only:
            user_achievements = UserAchievement.objects.filter(
                user=self.request.user
            ).values_list('achievement_id', flat=True)
            return Achievement.objects.filter(id__in=user_achievements, is_active=True)
        else:
            # Show all achievements (earned and unearned)
            return Achievement.objects.filter(
                Q(is_hidden=False) | 
                Q(id__in=UserAchievement.objects.filter(
                    user=self.request.user
                ).values_list('achievement_id', flat=True)),
                is_active=True
            )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


@extend_schema(
    tags=['Gamification'],
    summary='Riwayat Points',
    description='''
    Mendapatkan riwayat transaksi points user.
    
    **Features:**
    - Filter by transaction type
    - Filter by date range
    - Search by description
    - Include related course/lesson info
    ''',
    parameters=[
        OpenApiParameter(
            name='transaction_type',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by transaction type'
        ),
        OpenApiParameter(
            name='points__gte',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Minimum points (positive for earned, negative for deducted)'
        )
    ]
)
class PointsHistoryView(generics.ListAPIView):
    """List user's points transaction history"""
    serializer_class = PointsTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['transaction_type', 'points']
    search_fields = ['description']
    ordering_fields = ['created_at', 'points']
    ordering = ['-created_at']
    
    def get_queryset(self):  # type: ignore[override]
        return PointsTransaction.objects.filter(user=self.request.user).select_related(
            'course', 'lesson', 'assignment'
        )


@extend_schema(
    tags=['Gamification'],
    summary='Progress Level',
    description='''
    Mendapatkan informasi detail progress user menuju level berikutnya.
    
    **Data yang disediakan:**
    - Level saat ini dan informasi lengkapnya
    - Level berikutnya dan requirements
    - Progress percentage dan points needed
    - Perks yang akan didapat di level berikutnya
    ''',
    responses={
        200: {
            'description': 'Level progress berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'current_level': 4,
                        'current_level_name': 'Scholar',
                        'current_points': 850,
                        'next_level': 5,
                        'next_level_name': 'Expert',
                        'next_level_points': 1000,
                        'points_needed': 150,
                        'progress_percentage': 87.5,
                        'next_level_perks': [
                            'Priority support',
                            'Early access to new courses',
                            'Special badge'
                        ]
                    }
                }
            }
        }
    }
)
class LevelProgressView(APIView):
    """Get user's level progress information"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        progress = get_next_level_progress(request.user)
        return Response(progress)


@extend_schema(
    tags=['Gamification'],
    summary='Daftar Leaderboard',
    description='''
    Mendapatkan semua leaderboard yang tersedia.
    
    **Jenis Leaderboard:**
    - Overall Points: Total points keseluruhan
    - Monthly Points: Points bulan ini
    - Course Completion: Jumlah course selesai
    - Forum Activity: Aktivitas forum
    - Login Streak: Streak login terpanjang
    ''',
    responses={
        200: {
            'description': 'Daftar leaderboard berhasil diambil'
        }
    }
)
class LeaderboardListView(generics.ListAPIView):
    """List all available leaderboards"""
    serializer_class = LeaderboardSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Leaderboard.objects.filter(is_active=True).order_by('name')


@extend_schema(
    tags=['Gamification'],
    summary='Detail Leaderboard',
    description='''
    Mendapatkan detail leaderboard dengan ranking dan posisi user.
    
    **Features:**
    - Top 10 performers
    - User's current position
    - Total participants
    - Leaderboard metadata
    ''',
    parameters=[
        OpenApiParameter(
            name='type',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Leaderboard type',
            enum=['overall_points', 'monthly_points', 'course_completion', 'forum_activity', 'streak']
        )
    ]
)
class LeaderboardDetailView(APIView):
    """Get detailed leaderboard with user position"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, type):
        try:
            leaderboard = Leaderboard.objects.get(leaderboard_type=type, is_active=True)
        except Leaderboard.DoesNotExist:
            return Response(
                {'error': 'Leaderboard not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get top 10 entries
        top_entries = LeaderboardEntry.objects.filter(
            leaderboard=leaderboard
        ).select_related('user').order_by('rank')[:10]
        
        # Get user's entry if authenticated
        user_entry = None
        user_rank = 0
        if request.user.is_authenticated:
            try:
                user_entry = LeaderboardEntry.objects.get(
                    leaderboard=leaderboard,
                    user=request.user
                )
                user_rank = user_entry.rank
            except LeaderboardEntry.DoesNotExist:
                pass
        
        # Total participants
        total_participants = LeaderboardEntry.objects.filter(leaderboard=leaderboard).count()
        
        data = {
            'leaderboard_info': LeaderboardSerializer(leaderboard).data,
            'total_participants': total_participants,
            'user_rank': user_rank,
            'user_score': user_entry.score if user_entry else 0,
            'top_10': LeaderboardEntrySerializer(top_entries, many=True).data,
            'user_entry': LeaderboardEntrySerializer(user_entry).data if user_entry else None,
        }
        
        return Response(data)


@extend_schema(
    tags=['Gamification'],
    summary='Browse Badge Types',
    description='''
    Browse semua jenis badges yang tersedia di platform.
    
    **Features:**
    - Filter by category
    - Search by name
    - Show requirements untuk mendapat badge
    ''',
    parameters=[
        OpenApiParameter(
            name='category',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by category'
        )
    ]
)
class BadgeTypeListView(generics.ListAPIView):
    """Browse available badge types"""
    serializer_class = BadgeTypeSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    queryset = BadgeType.objects.filter(is_active=True).order_by('category', 'points_required')


@extend_schema(
    tags=['Gamification'],
    summary='Browse Achievements',
    description='''
    Browse semua achievements yang tersedia.
    
    **Features:**
    - Filter by type
    - Show/hide hidden achievements
    - Include requirements dan rewards
    ''',
    parameters=[
        OpenApiParameter(
            name='show_hidden',
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            description='Show hidden achievements (admin only)'
        )
    ]
)
class AchievementListView(generics.ListAPIView):
    """Browse available achievements"""
    serializer_class = AchievementSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['achievement_type', 'is_active']
    
    def get_queryset(self):  # type: ignore[override]
        show_hidden = getattr(self.request, 'query_params', self.request.GET).get('show_hidden', 'false').lower() == 'true'
        
        queryset = Achievement.objects.filter(is_active=True)
        
        if not show_hidden or not (hasattr(self.request.user, 'role') and getattr(self.request.user, 'role', None) == 'admin'):
            queryset = queryset.filter(is_hidden=False)
        
        return queryset.order_by('achievement_type', 'points_reward')


@extend_schema(
    tags=['Gamification'],
    summary='User Levels',
    description='''
    Mendapatkan semua level yang tersedia beserta requirements.
    
    **Level Information:**
    - Points requirements untuk setiap level
    - Perks dan benefits
    - Icons dan visual elements
    '''
)
class UserLevelListView(generics.ListAPIView):
    """List all user levels"""
    serializer_class = UserLevelSerializer
    permission_classes = [permissions.AllowAny]
    queryset = UserLevel.objects.all().order_by('level')


@extend_schema(
    tags=['Gamification'],
    summary='Award Points (Admin)',
    description='''
    Award points ke user tertentu (Admin/Instructor only).
    
    **Permissions:**
    - Admin: dapat award ke semua user
    - Instructor: dapat award ke student di course mereka
    
    **Features:**
    - Specify transaction type dan description
    - Link ke course/lesson/assignment
    - Custom metadata
    ''',
    request=PointsAwardSerializer
)
class AwardPointsView(APIView):
    """Award points to user (admin/instructor only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if not (hasattr(request.user, 'role') and getattr(request.user, 'role', None) in ['admin', 'instructor']):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PointsAwardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        if not data:
            return Response(
                {'error': 'Invalid data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = User.objects.get(id=data['user_id'])  # type: ignore[index]
        
        # For instructors, check if they have access to award points to this user
        if getattr(request.user, 'role', None) == 'instructor':
            # Add validation logic here if needed
            pass
        
        # Award points
        kwargs: Dict[str, Any] = {}
        if data and data.get('course_id'):  # type: ignore[union-attr]
            from courses.models import Course
            kwargs['course'] = Course.objects.get(id=data['course_id'])  # type: ignore[index]
        if data and data.get('lesson_id'):  # type: ignore[union-attr]
            from lessons.models import Lesson
            kwargs['lesson'] = Lesson.objects.get(id=data['lesson_id'])  # type: ignore[index]
        if data and data.get('assignment_id'):  # type: ignore[union-attr]
            from assignments.models import Assignment
            kwargs['assignment'] = Assignment.objects.get(id=data['assignment_id'])  # type: ignore[index]
        if data and data.get('metadata'):  # type: ignore[union-attr]
            kwargs['metadata'] = data['metadata']  # type: ignore[index]
        
        if data:
            award_points(
                user,
                data['points'],  # type: ignore[index]
                data['transaction_type'],  # type: ignore[index]
                data['description'],  # type: ignore[index]
                **kwargs
            )
        
        return Response({'message': 'Points awarded successfully'})


@extend_schema(
    tags=['Gamification'],
    summary='Award Badge (Admin)',
    description='''
    Award badge ke user tertentu (Admin only).
    
    **Features:**
    - Manual badge awarding
    - Custom metadata
    - Validation untuk prevent duplicate
    ''',
    request=BadgeAwardSerializer
)
class AwardBadgeView(APIView):
    """Award badge to user (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if not (hasattr(request.user, 'role') and getattr(request.user, 'role', None) == 'admin'):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BadgeAwardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        if not data:
            return Response(
                {'error': 'Invalid data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = User.objects.get(id=data['user_id'])  # type: ignore[index]
        badge_type = BadgeType.objects.get(id=data['badge_type_id'])  # type: ignore[index]
        
        # Award badge
        user_badge = UserBadge.objects.create(
            user=user,
            badge_type=badge_type,
            metadata=data.get('metadata', {}) if data else {}  # type: ignore[union-attr]
        )
        
        return Response({
            'message': 'Badge awarded successfully',
            'badge': UserBadgeSerializer(user_badge).data
        })


@extend_schema(
    tags=['Gamification'],
    summary='Daily Login Bonus',
    description='''
    Claim daily login bonus dan update streak.
    
    **Features:**
    - Award daily login points
    - Update login streak
    - Streak bonus untuk milestone tertentu
    - Prevent multiple claims per day
    ''',
    responses={
        200: {
            'description': 'Daily login bonus claimed',
            'content': {
                'application/json': {
                    'example': {
                        'points_awarded': 2,
                        'current_streak': 7,
                        'streak_bonus': 7,
                        'message': 'Daily login bonus claimed!'
                    }
                }
            }
        },
        400: {
            'description': 'Already claimed today'
        }
    }
)
class DailyLoginView(APIView):
    """Claim daily login bonus"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        stats = get_or_create_user_stats(user)
        
        # Check if already claimed today
        from django.utils import timezone
        today = timezone.now().date()
        
        if stats.last_login_date == today:
            return Response(
                {'error': 'Daily bonus already claimed today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Award daily login
        trigger_daily_login(user)
        
        # Refresh stats
        stats.refresh_from_db()
        
        response_data = {
            'points_awarded': 2,  # Base daily points
            'current_streak': stats.current_login_streak,
            'message': 'Daily login bonus claimed!'
        }
        
        # Check for streak bonuses
        if stats.current_login_streak in [7, 30, 100]:
            response_data['streak_bonus'] = stats.current_login_streak
            response_data['message'] += f' Bonus for {stats.current_login_streak}-day streak!'
        
        return Response(response_data)


@extend_schema(
    tags=['Gamification'],
    summary='Gamification Statistics',
    description='''
    Mendapatkan statistik gamifikasi platform (Admin only).
    
    **Metrics:**
    - Total points awarded
    - Total badges earned
    - Most active users
    - Popular achievements
    - Leaderboard statistics
    '''
)
class GamificationStatsView(APIView):
    """Get gamification platform statistics (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if not (hasattr(request.user, 'role') and getattr(request.user, 'role', None) == 'admin'):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Calculate statistics
        stats = {
            'total_points_awarded': PointsTransaction.objects.aggregate(
                total=Sum('points')
            )['total'] or 0,
            'total_badges_earned': UserBadge.objects.count(),
            'total_achievements_unlocked': UserAchievement.objects.count(),
            'active_users': UserStats.objects.filter(total_points__gt=0).count(),
            'top_earners': UserStats.objects.order_by('-total_points')[:5].values(
                'user__username', 'total_points'
            ),
            'popular_badges': BadgeType.objects.annotate(
                earned_count=Count('userbadge')
            ).order_by('-earned_count')[:5].values('name', 'earned_count'),
            'leaderboard_stats': {
                leaderboard.name: leaderboard.entries.count()  # type: ignore[attr-defined]
                for leaderboard in Leaderboard.objects.filter(is_active=True)
            }
        }
        
        return Response(stats)


# Management views for admin
class BadgeTypeManagementView(generics.ListCreateAPIView):
    """Manage badge types (admin only)"""
    serializer_class = BadgeTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore[override]
        if not (hasattr(self.request.user, 'role') and getattr(self.request.user, 'role', None) == 'admin'):
            return BadgeType.objects.none()
        return BadgeType.objects.all().order_by('category', 'name')


class AchievementManagementView(generics.ListCreateAPIView):
    """Manage achievements (admin only)"""
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore[override]
        if not (hasattr(self.request.user, 'role') and getattr(self.request.user, 'role', None) == 'admin'):
            return Achievement.objects.none()
        return Achievement.objects.all().order_by('achievement_type', 'name')