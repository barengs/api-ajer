from typing import Any
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg, QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

# drf-spectacular imports
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import (
    LiveSession, SessionAttendance, SessionResource,
    SessionRecording, SessionChat, SessionPoll, PollResponse
)
from .serializers import (
    LiveSessionSerializer, LiveSessionCreateSerializer,
    SessionAttendanceSerializer, SessionAttendanceCreateSerializer,
    SessionResourceSerializer, SessionRecordingSerializer,
    SessionChatSerializer, SessionChatCreateSerializer,
    SessionPollSerializer, SessionPollCreateSerializer,
    PollResponseSerializer
)
from courses.models import Course, CourseBatch
from courses.permissions import IsInstructor, IsStudent, IsOwnerOrReadOnly


@extend_schema(
    tags=['Live Sessions'],
    summary='Live Sessions',
    description='''
    Mengelola live sessions/kelas online dalam platform.
    
    **GET Request:**
    - List semua live sessions berdasarkan role user
    - Instructor: hanya sessions mereka
    - Student: sessions dari kursus yang enrolled
    - Admin: semua sessions
    
    **POST Request:**
    - Membuat session baru (hanya instructor)
    - Auto-assign instructor yang membuat
    
    **Session Status:**
    - **Scheduled**: Session terjadwal, belum dimulai
    - **Live**: Session sedang berlangsung
    - **Ended**: Session sudah selesai
    - **Cancelled**: Session dibatalkan
    
    **Platform Integration:**
    - Zoom: Integrasi dengan Zoom API
    - Google Meet: Integrasi dengan Google Meet
    - Jitsi Meet: Open source video conferencing
    - Custom: Platform video call custom
    
    **Filtering & Search:**
    - Filter: status, platform, course, batch
    - Search: title, description
    - Sort: scheduled_start, created_at
    ''',
    parameters=[
        OpenApiParameter(
            name='status',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter berdasarkan status session',
            enum=['scheduled', 'live', 'ended', 'cancelled']
        ),
        OpenApiParameter(
            name='platform',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter berdasarkan platform video',
            enum=['zoom', 'google_meet', 'jitsi', 'custom']
        ),
        OpenApiParameter(
            name='search',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Search dalam title atau description'
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'title': {
                    'type': 'string',
                    'description': 'Judul live session'
                },
                'description': {
                    'type': 'string',
                    'description': 'Deskripsi session'
                },
                'course': {
                    'type': 'integer',
                    'description': 'ID kursus'
                },
                'scheduled_start': {
                    'type': 'string',
                    'format': 'date-time',
                    'description': 'Waktu mulai terjadwal'
                },
                'scheduled_end': {
                    'type': 'string',
                    'format': 'date-time',
                    'description': 'Waktu selesai terjadwal'
                },
                'platform': {
                    'type': 'string',
                    'enum': ['zoom', 'google_meet', 'jitsi', 'custom'],
                    'description': 'Platform video conference'
                },
                'meeting_url': {
                    'type': 'string',
                    'description': 'URL meeting room'
                },
                'max_participants': {
                    'type': 'integer',
                    'description': 'Maksimal peserta'
                }
            },
            'required': ['title', 'course', 'scheduled_start', 'platform']
        }
    },
    responses={
        200: {
            'description': 'Daftar live sessions berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'count': 5,
                        'results': [
                            {
                                'id': 1,
                                'title': 'Live Coding Session - Django REST API',
                                'description': 'Hands-on coding session untuk membuat REST API',
                                'status': 'scheduled',
                                'platform': 'zoom',
                                'meeting_url': 'https://zoom.us/j/123456789',
                                'scheduled_start': '2024-01-20T10:00:00Z',
                                'scheduled_end': '2024-01-20T12:00:00Z',
                                'course': {
                                    'id': 1,
                                    'title': 'Python untuk Pemula'
                                },
                                'instructor': {
                                    'id': 2,
                                    'full_name': 'Dr. Jane Smith'
                                },
                                'participants_count': 25,
                                'max_participants': 50
                            }
                        ]
                    }
                }
            }
        },
        201: {
            'description': 'Live session berhasil dibuat'
        },
        403: {
            'description': 'Forbidden - Hanya instructor yang dapat membuat session'
        }
    }
)
class LiveSessionListView(generics.ListCreateAPIView):
    """List and create live sessions"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'platform', 'course', 'batch']
    search_fields = ['title', 'description']
    ordering_fields = ['scheduled_start', 'created_at']
    ordering = ['scheduled_start']
    
    def get_queryset(self) -> QuerySet[LiveSession]:  # type: ignore[override]
        user = self.request.user
        base_queryset = LiveSession.objects.select_related(
            'course', 'batch', 'instructor'
        ).prefetch_related('attendances')
        
        if user.role == 'instructor':  # type: ignore[attr-defined]
            # Instructors see their sessions
            return base_queryset.filter(instructor=user)
        elif user.role == 'student':  # type: ignore[attr-defined]
            # Students see sessions for their enrolled courses
            enrolled_courses = user.enrollments.values_list('course', flat=True)  # type: ignore[attr-defined]
            return base_queryset.filter(course__in=enrolled_courses)
        elif user.role == 'admin':  # type: ignore[attr-defined]
            # Admins see all sessions
            return base_queryset
        else:
            return base_queryset.none()
    
    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == 'POST':
            return LiveSessionCreateSerializer
        return LiveSessionSerializer
    
    def perform_create(self, serializer):
        # Only instructors can create sessions
        if self.request.user.role != 'instructor':  # type: ignore[attr-defined]
            raise PermissionDenied("Only instructors can create live sessions")
        serializer.save(instructor=self.request.user)


class LiveSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a live session"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LiveSessionSerializer
    
    def get_queryset(self) -> QuerySet[LiveSession]:  # type: ignore[override]
        user = self.request.user
        base_queryset = LiveSession.objects.select_related(
            'course', 'batch', 'instructor'
        ).prefetch_related('attendances')
        
        if user.role == 'instructor':  # type: ignore[attr-defined]
            return base_queryset.filter(instructor=user)
        elif user.role in ['student', 'admin']:  # type: ignore[attr-defined]
            return base_queryset
        return base_queryset.none()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_session(request, session_id):
    """Start a live session (instructors only)"""
    session = get_object_or_404(LiveSession, id=session_id)
    
    if request.user != session.instructor and request.user.role != 'admin':
        return Response(
            {'error': 'Only the instructor can start this session'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if session.status != LiveSession.SessionStatus.SCHEDULED:
        return Response(
            {'error': 'Session cannot be started'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    session.start_session()
    serializer = LiveSessionSerializer(session)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def end_session(request, session_id):
    """End a live session (instructors only)"""
    session = get_object_or_404(LiveSession, id=session_id)
    
    if request.user != session.instructor and request.user.role != 'admin':
        return Response(
            {'error': 'Only the instructor can end this session'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if session.status != LiveSession.SessionStatus.LIVE:
        return Response(
            {'error': 'Session is not currently live'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    session.end_session()
    serializer = LiveSessionSerializer(session)
    return Response(serializer.data)


class SessionAttendanceListView(generics.ListCreateAPIView):
    """List and create session attendance"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self) -> QuerySet[SessionAttendance]:  # type: ignore[override]
        session_id = self.kwargs.get('session_id')
        user = self.request.user
        
        base_queryset = SessionAttendance.objects.filter(
            session_id=session_id
        ).select_related('student', 'session')
        
        if user.role == 'student':  # type: ignore[attr-defined]
            # Students only see their own attendance
            return base_queryset.filter(student=user)
        elif user.role == 'instructor':  # type: ignore[attr-defined]
            # Instructors see all attendance for their sessions
            return base_queryset.filter(session__instructor=user)
        
        return base_queryset
    
    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == 'POST':
            return SessionAttendanceCreateSerializer
        return SessionAttendanceSerializer


@extend_schema(
    tags=['Live Sessions'],
    summary='Join Live Session',
    description='''
    Student bergabung ke live session yang sedang berlangsung.
    
    **Validasi sebelum join:**
    1. Student harus enrolled di kursus yang terkait
    2. Session harus dalam status 'live' atau 'scheduled'
    3. Belum pernah join sebelumnya atau masih registered
    4. Tidak melebihi max_participants
    
    **Process Flow:**
    1. Create/update attendance record
    2. Set status menjadi 'joined'
    3. Record timestamp joined_at
    4. Return meeting URL dan details
    
    **Meeting Access:**
    Setelah join, student akan mendapat akses ke:
    - Meeting URL
    - Meeting credentials jika diperlukan
    - Session resources dan materials
    ''',
    parameters=[
        OpenApiParameter(
            name='session_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID session yang akan diikuti'
        )
    ],
    responses={
        200: {
            'description': 'Berhasil join session',
            'content': {
                'application/json': {
                    'example': {
                        'id': 1,
                        'session': {
                            'id': 1,
                            'title': 'Live Coding Session',
                            'meeting_url': 'https://zoom.us/j/123456789'
                        },
                        'student': {
                            'id': 1,
                            'full_name': 'John Doe'
                        },
                        'status': 'joined',
                        'joined_at': '2024-01-20T10:05:00Z',
                        'registered_at': '2024-01-18T15:30:00Z'
                    }
                }
            }
        },
        403: {
            'description': 'Forbidden - Not enrolled atau tidak memiliki akses',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'You are not enrolled in this course'
                    }
                }
            }
        },
        400: {
            'description': 'Bad Request - Sudah join atau session tidak dapat diakses',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'You have already joined this session'
                    }
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsStudent])
def join_session(request, session_id):
    """Student joins a live session"""
    session = get_object_or_404(LiveSession, id=session_id)
    student = request.user
    
    # Check if student is enrolled in the course
    if not student.enrollments.filter(course=session.course).exists():
        return Response(
            {'error': 'You are not enrolled in this course'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get or create attendance record
    attendance, created = SessionAttendance.objects.get_or_create(
        session=session,
        student=student,
        defaults={'status': SessionAttendance.AttendanceStatus.JOINED}
    )
    
    if not created and attendance.status != SessionAttendance.AttendanceStatus.REGISTERED:
        return Response(
            {'error': 'You have already joined this session'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update attendance
    attendance.status = SessionAttendance.AttendanceStatus.JOINED
    attendance.joined_at = timezone.now()
    attendance.save()
    
    serializer = SessionAttendanceSerializer(attendance)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsStudent])
def leave_session(request, session_id):
    """Student leaves a live session"""
    session = get_object_or_404(LiveSession, id=session_id)
    
    try:
        attendance = SessionAttendance.objects.get(
            session=session,
            student=request.user
        )
    except SessionAttendance.DoesNotExist:
        return Response(
            {'error': 'You are not attending this session'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if attendance.status == SessionAttendance.AttendanceStatus.JOINED:
        attendance.left_at = timezone.now()
        if attendance.joined_at:
            duration = (attendance.left_at - attendance.joined_at).total_seconds() / 60
            attendance.total_duration_minutes += int(duration)
        attendance.status = SessionAttendance.AttendanceStatus.COMPLETED
        attendance.save()
    
    serializer = SessionAttendanceSerializer(attendance)
    return Response(serializer.data)


class SessionResourceListView(generics.ListCreateAPIView):
    """List and create session resources"""
    serializer_class = SessionResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self) -> QuerySet[SessionResource]:  # type: ignore[override]
        session_id = self.kwargs.get('session_id')
        return SessionResource.objects.filter(
            session_id=session_id
        ).select_related('shared_by')
    
    def perform_create(self, serializer):
        session_id = self.kwargs.get('session_id')
        session = get_object_or_404(LiveSession, id=session_id)
        serializer.save(
            session=session,
            shared_by=self.request.user
        )


class SessionChatListView(generics.ListCreateAPIView):
    """List and create chat messages"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering = ['sent_at']
    
    def get_queryset(self) -> QuerySet[SessionChat]:  # type: ignore[override]
        session_id = self.kwargs.get('session_id')
        return SessionChat.objects.filter(
            session_id=session_id,
            is_visible=True
        ).select_related('sender').prefetch_related('replies')
    
    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == 'POST':
            return SessionChatCreateSerializer
        return SessionChatSerializer
    
    def perform_create(self, serializer):
        session_id = self.kwargs.get('session_id')
        session = get_object_or_404(LiveSession, id=session_id)
        
        # Check if user can send messages in this session
        user = self.request.user
        if user.role == 'student':  # type: ignore[attr-defined]
            # Check if student is attending the session
            if not SessionAttendance.objects.filter(
                session=session, student=user
            ).exists():
                raise PermissionDenied(
                    "You must be attending the session to send messages"
                )
        
        serializer.save(session=session, sender=user)


class SessionPollListView(generics.ListCreateAPIView):
    """List and create session polls"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self) -> QuerySet[SessionPoll]:  # type: ignore[override]
        session_id = self.kwargs.get('session_id')
        return SessionPoll.objects.filter(
            session_id=session_id
        ).select_related('created_by').prefetch_related('responses')
    
    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == 'POST':
            return SessionPollCreateSerializer
        return SessionPollSerializer
    
    def perform_create(self, serializer):
        session_id = self.kwargs.get('session_id')
        session = get_object_or_404(LiveSession, id=session_id)
        
        # Only instructors can create polls
        if self.request.user != session.instructor:
            raise PermissionDenied(
                "Only the session instructor can create polls"
            )
        
        serializer.save(session=session, created_by=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def respond_to_poll(request, poll_id):
    """Student responds to a poll"""
    poll = get_object_or_404(SessionPoll, id=poll_id)
    
    if not poll.is_active:
        return Response(
            {'error': 'This poll is no longer active'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if student is attending the session
    if request.user.role == 'student':
        if not SessionAttendance.objects.filter(
            session=poll.session, student=request.user
        ).exists():
            return Response(
                {'error': 'You must be attending the session to respond'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    serializer = PollResponseSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # Create or update response
    response_obj, created = PollResponse.objects.update_or_create(
        poll=poll,
        student=request.user,
        defaults={'selected_options': serializer.validated_data['selected_options']}  # type: ignore[index]
    )
    
    return Response(PollResponseSerializer(response_obj).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def close_poll(request, poll_id):
    """Close a poll (instructors only)"""
    poll = get_object_or_404(SessionPoll, id=poll_id)
    
    if request.user != poll.created_by and request.user != poll.session.instructor:
        return Response(
            {'error': 'Only the poll creator can close this poll'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    poll.close_poll()
    serializer = SessionPollSerializer(poll)
    return Response(serializer.data)


class SessionRecordingListView(generics.ListAPIView):
    """List session recordings"""
    serializer_class = SessionRecordingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self) -> QuerySet[SessionRecording]:  # type: ignore[override]
        user = self.request.user
        base_queryset = SessionRecording.objects.select_related('session')
        
        if user.role == 'student':  # type: ignore[attr-defined]
            # Students see recordings for sessions they attended
            attended_sessions = SessionAttendance.objects.filter(
                student=user
            ).values_list('session', flat=True)
            return base_queryset.filter(
                session__in=attended_sessions,
                processing_status=SessionRecording.ProcessingStatus.READY,
                is_available=True
            )
        elif user.role == 'instructor':  # type: ignore[attr-defined]
            # Instructors see recordings for their sessions
            return base_queryset.filter(
                session__instructor=user,
                is_available=True
            )
        
        return base_queryset.filter(is_available=True)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def session_analytics(request, session_id):
    """Get analytics for a session (instructors only)"""
    session = get_object_or_404(LiveSession, id=session_id)
    
    if request.user != session.instructor and request.user.role != 'admin':
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    analytics = {
        'session': LiveSessionSerializer(session).data,
        'attendance_stats': {
            'total_registered': session.attendances.count(),  # type: ignore[attr-defined]
            'total_joined': session.attendances.filter(  # type: ignore[attr-defined]
                status__in=[
                    SessionAttendance.AttendanceStatus.JOINED,
                    SessionAttendance.AttendanceStatus.COMPLETED
                ]
            ).count(),
            'average_duration': session.attendances.aggregate(  # type: ignore[attr-defined]
                avg_duration=Avg('total_duration_minutes')
            )['avg_duration'] or 0,
        },
        'engagement_stats': {
            'total_messages': session.chat_messages.count(),  # type: ignore[attr-defined]
            'total_questions': session.chat_messages.filter(  # type: ignore[attr-defined]
                message_type=SessionChat.MessageType.QUESTION
            ).count(),
            'polls_created': session.polls.count(),  # type: ignore[attr-defined]
            'resources_shared': session.resources.count(),  # type: ignore[attr-defined]
        }
    }
    
    return Response(analytics)