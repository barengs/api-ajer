from typing import TYPE_CHECKING, Any
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import F

# drf-spectacular imports
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import (
    Section, Lesson, LessonProgress, Quiz, QuizQuestion, 
    QuizAttempt, QuizAnswer, LessonComment, LessonNote
)
from .serializers import (
    SectionSerializer, LessonSerializer, LessonDetailSerializer,
    LessonProgressSerializer, QuizSerializer, QuizAttemptSerializer,
    QuizAnswerSerializer, LessonCommentSerializer, LessonNoteSerializer,
    LessonCreateSerializer
)
from courses.models import Course, Enrollment
if TYPE_CHECKING:
    from django.db.models import QuerySet

from courses.permissions import IsEnrolledOrInstructor, IsInstructorOfCourse


@extend_schema(
    tags=['Lessons'],
    summary='Daftar Seksi Kursus',
    description='''
    Mendapatkan semua seksi/section dari sebuah kursus beserta lesson-lessonnya.
    
    **Struktur Data:**
    - Setiap seksi berisi informasi dasar dan daftar lessons
    - Lessons diurutkan berdasarkan sort_order
    - Durasi total dan jumlah lessons per seksi
    
    **Access Control:**
    - Dapat diakses tanpa autentikasi untuk preview
    - Akses penuh memerlukan enrollment
    ''',
    parameters=[
        OpenApiParameter(
            name='course_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID kursus yang akan dilihat seksi-seksinya'
        )
    ],
    responses={
        200: {
            'description': 'Daftar seksi berhasil diambil',
            'content': {
                'application/json': {
                    'example': [
                        {
                            'id': 1,
                            'title': 'Pengenalan Python',
                            'description': 'Dasar-dasar pemrograman Python',
                            'sort_order': 1,
                            'total_lessons': 5,
                            'total_duration': 180,
                            'lessons': [
                                {
                                    'id': 1,
                                    'title': 'Apa itu Python?',
                                    'lesson_type': 'video',
                                    'duration_minutes': 15,
                                    'sort_order': 1,
                                    'is_preview': True
                                }
                            ]
                        }
                    ]
                }
            }
        },
        404: {
            'description': 'Kursus tidak ditemukan'
        }
    }
)
class CourseSectionListView(generics.ListAPIView):
    """List all sections for a course"""
    serializer_class = SectionSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Section.objects.all()
    
    def get_queryset(self) -> 'QuerySet[Section]':  # type: ignore
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id, is_published=True)
        return Section.objects.filter(course=course).prefetch_related('lessons').order_by('sort_order')


@extend_schema(
    tags=['Lessons'],
    summary='Detail Lesson',
    description='''
    Mendapatkan detail lengkap dari sebuah lesson.
    
    **Fitur Access Control:**
    - Preview lessons: dapat diakses tanpa enrollment
    - Paid lessons: memerlukan enrollment aktif
    - Progress tracking: otomatis dicatat untuk user yang login
    
    **Informasi yang disediakan:**
    - Konten lesson (video, text, attachments)
    - Progress tracking data
    - Informasi akses (can_access, time_remaining)
    - Comments dan notes
    
    **Auto Progress Tracking:**
    Sistem akan otomatis mencatat waktu akses terakhir
    untuk keperluan analytics dan progress tracking.
    ''',
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID lesson yang akan dilihat'
        )
    ],
    responses={
        200: {
            'description': 'Detail lesson berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'id': 1,
                        'title': 'Pengenalan Python',
                        'description': 'Video pengenalan bahasa Python',
                        'lesson_type': 'video',
                        'content': 'Konten lesson dalam format text/html',
                        'video_url': 'http://localhost:8000/media/lessons/python_intro.mp4',
                        'duration_minutes': 15,
                        'sort_order': 1,
                        'is_preview': True,
                        'section': {
                            'id': 1,
                            'title': 'Dasar Python',
                            'course': {
                                'id': 1,
                                'title': 'Python untuk Pemula'
                            }
                        },
                        'user_progress': {
                            'completion_percentage': 75.5,
                            'is_completed': False,
                            'time_spent_minutes': 12,
                            'last_accessed_at': '2024-01-15T10:30:00Z'
                        },
                        'can_access': True,
                        'attachments': [
                            {
                                'id': 1,
                                'title': 'Python Cheat Sheet',
                                'file_url': 'http://localhost:8000/media/attachments/python_cheat.pdf',
                                'file_type': 'pdf'
                            }
                        ]
                    }
                }
            }
        },
        403: {
            'description': 'Akses ditolak - Enrollment diperlukan',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'You need to be enrolled to access this lesson'
                    }
                }
            }
        },
        404: {
            'description': 'Lesson tidak ditemukan'
        }
    }
)
class LessonDetailView(generics.RetrieveAPIView):
    """Get lesson details with access control"""
    serializer_class = LessonDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Lesson.objects.all()
    
    def get_queryset(self) -> 'QuerySet[Lesson]':  # type: ignore
        return Lesson.objects.select_related('section__course')
    
    def retrieve(self, request, *args, **kwargs):
        lesson = self.get_object()
        
        # Check access permissions
        if not lesson.can_be_accessed_by_user(request.user):
            return Response(
                {'error': 'You need to be enrolled to access this lesson'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create or update progress tracking
        if request.user.is_authenticated:
            progress, created = LessonProgress.objects.get_or_create(
                student=request.user,
                lesson=lesson,
                defaults={'last_accessed_at': timezone.now()}
            )
            if not created:
                progress.last_accessed_at = timezone.now()
                progress.save(update_fields=['last_accessed_at'])
        
        return super().retrieve(request, *args, **kwargs)


@extend_schema(
    tags=['Lessons'],
    summary='Buat Lesson Baru',
    description='''
    Membuat lesson baru dalam sebuah section/seksi kursus.
    
    **Persyaratan:**
    - User harus login sebagai instructor
    - Harus memiliki akses ke kursus yang bersangkutan
    - Section harus valid dan sudah ada
    
    **Jenis Lesson yang didukung:**
    - Video: Lesson dengan video sebagai konten utama
    - Reading: Lesson berupa text/artikel
    - Quiz: Lesson berupa kuis/test
    
    **Auto Update:**
    Sistem akan otomatis mengupdate total_lessons count pada kursus.
    ''',
    examples=[
        OpenApiExample(
            'Video Lesson',
            value={
                'title': 'Pengenalan Variables Python',
                'description': 'Memahami konsep variables dalam Python',
                'lesson_type': 'video',
                'content': '<p>Video ini menjelaskan konsep variables...</p>',
                'video_url': 'https://youtube.com/watch?v=example',
                'duration_minutes': 20,
                'section': 1,
                'sort_order': 3,
                'is_preview': False,
                'is_mandatory': True
            },
            request_only=True
        ),
        OpenApiExample(
            'Reading Lesson',
            value={
                'title': 'Struktur Data List',
                'description': 'Memahami list dan operasinya',
                'lesson_type': 'reading',
                'content': '<h1>List Python</h1><p>List adalah...</p>',
                'duration_minutes': 15,
                'section': 1,
                'sort_order': 4,
                'is_preview': False,
                'is_mandatory': True
            },
            request_only=True
        )
    ],
    responses={
        201: {
            'description': 'Lesson berhasil dibuat',
            'content': {
                'application/json': {
                    'example': {
                        'id': 5,
                        'title': 'Pengenalan Variables Python',
                        'lesson_type': 'video',
                        'section': {
                            'id': 1,
                            'title': 'Dasar Python'
                        },
                        'created_at': '2024-01-15T10:30:00Z'
                    }
                }
            }
        },
        401: {
            'description': 'Unauthorized - Login diperlukan'
        },
        403: {
            'description': 'Forbidden - Hanya instructor yang dapat membuat lesson'
        },
        400: {
            'description': 'Bad Request - Data tidak valid',
            'content': {
                'application/json': {
                    'example': {
                        'title': ['This field is required.'],
                        'section': ['Invalid pk "999" - object does not exist.']
                    }
                }
            }
        }
    }
)
class LessonCreateView(generics.CreateAPIView):
    """Create new lesson (instructors only)"""
    serializer_class = LessonCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        lesson = serializer.save()
        
        # Update course total lessons count
        course = lesson.section.course
        course.total_lessons = F('total_lessons') + 1
        course.save(update_fields=['total_lessons'])


@extend_schema(
    tags=['Lessons'],
    summary='Kelola Lesson Instructor',
    description='''
    Endpoint untuk instructor mengelola lesson-lesson mereka.
    
    **GET Request:**
    - Mendapatkan semua lesson yang dibuat oleh instructor
    - Data diurutkan berdasarkan section dan sort_order
    - Termasuk informasi section dan course
    
    **POST Request:**
    - Membuat lesson baru dalam course instructor
    - Validasi otomatis bahwa instructor memiliki akses
    
    **Filter & Search:**
    - Otomatis terfilter hanya lesson milik instructor
    - Dapat search berdasarkan title lesson
    ''',
    responses={
        200: {
            'description': 'Daftar lesson instructor berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'count': 25,
                        'next': 'http://localhost:8000/api/v1/lessons/instructor/?page=2',
                        'previous': None,
                        'results': [
                            {
                                'id': 1,
                                'title': 'Pengenalan Python',
                                'lesson_type': 'video',
                                'duration_minutes': 20,
                                'is_preview': False,
                                'section': {
                                    'id': 1,
                                    'title': 'Dasar Python',
                                    'course': {
                                        'id': 1,
                                        'title': 'Python untuk Pemula'
                                    }
                                },
                                'created_at': '2024-01-15T08:00:00Z'
                            }
                        ]
                    }
                }
            }
        },
        403: {
            'description': 'Forbidden - Hanya instructor yang dapat mengakses'
        }
    }
)
class InstructorLessonListView(generics.ListCreateAPIView):
    """Instructor's lesson management"""
    serializer_class = LessonDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Lesson.objects.all()
    
    def get_queryset(self) -> 'QuerySet[Lesson]':  # type: ignore
        if not self.request.user.is_authenticated or getattr(self.request.user, 'role', None) != 'instructor':
            return Lesson.objects.none()
        return Lesson.objects.filter(
            section__course__instructor=self.request.user
        ).select_related('section__course')
    
    def get_serializer_class(self):  # type: ignore
        if self.request.method == 'POST':
            return LessonCreateSerializer
        return LessonDetailSerializer


@extend_schema(
    tags=['Lessons'],
    summary='Update Progress Lesson',
    description='''
    Mengupdate progress pembelajaran untuk sebuah lesson.
    
    **Proses Update:**
    1. Validasi akses user ke lesson
    2. Buat/ambil progress record yang ada
    3. Update completion_percentage dan time_spent
    4. Auto-complete jika mencapai 100%
    
    **Field yang dapat diupdate:**
    - completion_percentage: Persentase penyelesaian (0-100)
    - time_spent_minutes: Total waktu yang dihabiskan
    - last_accessed_at: Otomatis diupdate
    
    **Auto Completion:**
    Jika completion_percentage >= 100%, lesson akan otomatis
    ditandai sebagai completed dengan timestamp.
    ''',
    parameters=[
        OpenApiParameter(
            name='lesson_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID lesson yang akan diupdate progressnya'
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'completion_percentage': {
                    'type': 'number',
                    'minimum': 0,
                    'maximum': 100,
                    'description': 'Persentase penyelesaian lesson'
                },
                'time_spent_minutes': {
                    'type': 'integer',
                    'minimum': 0,
                    'description': 'Total waktu dalam menit'
                }
            },
            'required': ['completion_percentage']
        }
    },
    examples=[
        OpenApiExample(
            'Update Progress 75%',
            value={
                'completion_percentage': 75.5,
                'time_spent_minutes': 12
            },
            request_only=True
        )
    ],
    responses={
        200: {
            'description': 'Progress berhasil diupdate',
            'content': {
                'application/json': {
                    'example': {
                        'id': 1,
                        'completion_percentage': 75.5,
                        'time_spent_minutes': 12,
                        'is_completed': False,
                        'last_accessed_at': '2024-01-15T10:30:00Z',
                        'lesson': {
                            'id': 1,
                            'title': 'Pengenalan Python'
                        }
                    }
                }
            }
        },
        403: {
            'description': 'Akses ditolak - Enrollment diperlukan'
        },
        404: {
            'description': 'Lesson tidak ditemukan'
        }
    }
)
class LessonProgressUpdateView(generics.UpdateAPIView):
    """Update lesson progress"""
    serializer_class = LessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = LessonProgress.objects.all()
    
    def get_object(self) -> Any:
        lesson_id = self.kwargs.get('lesson_id')
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Check if user can access this lesson
        if not lesson.can_be_accessed_by_user(self.request.user):
            raise PermissionDenied("You are not enrolled in this course")
        
        progress, created = LessonProgress.objects.get_or_create(
            student=self.request.user,
            lesson=lesson
        )
        return progress
    
    def perform_update(self, serializer):
        progress = serializer.save()
        
        # Auto-mark as completed if 100% progress
        if (progress.completion_percentage >= 100 and 
            not progress.is_completed):
            progress.mark_completed()


@extend_schema(
    tags=['Lessons'],
    summary='Tandai Lesson Selesai',
    description='''
    Menandai sebuah lesson sebagai completed untuk user yang login.
    
    **Proses yang terjadi:**
    1. Validasi akses user ke lesson
    2. Buat/update progress record
    3. Set completion timestamp
    4. Update completion percentage menjadi 100%
    5. Trigger progress calculation untuk course
    
    **Efek sampingan:**
    - Course progress akan diupdate otomatis
    - Badge/achievement mungkin akan di-unlock
    - Notifikasi completion akan dikirim
    ''',
    parameters=[
        OpenApiParameter(
            name='lesson_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID lesson yang akan ditandai selesai'
        )
    ],
    responses={
        200: {
            'description': 'Lesson berhasil ditandai selesai',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Lesson marked as completed',
                        'progress': {
                            'id': 1,
                            'completion_percentage': 100.0,
                            'is_completed': True,
                            'completed_at': '2024-01-15T10:30:00Z',
                            'time_spent_minutes': 15
                        }
                    }
                }
            }
        },
        403: {
            'description': 'Akses ditolak - Enrollment diperlukan',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'You are not enrolled in this course'
                    }
                }
            }
        },
        401: {
            'description': 'Unauthorized - Login diperlukan'
        },
        404: {
            'description': 'Lesson tidak ditemukan'
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_lesson_complete(request, lesson_id):
    """Mark lesson as completed"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    # Check access
    if not lesson.can_be_accessed_by_user(request.user):
        return Response(
            {'error': 'You are not enrolled in this course'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get or create progress
    progress, created = LessonProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson
    )
    
    # Mark as completed
    progress.mark_completed()
    
    return Response({
        'message': 'Lesson marked as completed',
        'progress': LessonProgressSerializer(progress).data
    })


@extend_schema(
    tags=['Lessons'],
    summary='Detail Quiz',
    description='''
    Mendapatkan detail lengkap dari sebuah quiz beserta pertanyaan-pertanyaannya.
    
    **Akses Control:**
    - Memerlukan enrollment aktif pada kursus
    - Quiz hanya dapat diakses jika lesson dapat diakses
    
    **Informasi Quiz:**
    - Metadata quiz (judul, deskripsi, durasi)
    - Daftar pertanyaan dengan opsi jawaban
    - Aturan attempt dan scoring
    - Riwayat attempt user (jika ada)
    
    **Keamanan:**
    - Jawaban benar tidak ditampilkan sebelum attempt
    - Hanya pertanyaan dan opsi yang ditampilkan
    ''',
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID quiz yang akan dilihat'
        )
    ],
    responses={
        200: {
            'description': 'Detail quiz berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'id': 1,
                        'title': 'Quiz Python Basics',
                        'description': 'Test pemahaman dasar Python',
                        'time_limit_minutes': 30,
                        'max_attempts': 3,
                        'passing_score': 70,
                        'total_questions': 10,
                        'lesson': {
                            'id': 1,
                            'title': 'Pengenalan Python',
                            'section': {
                                'id': 1,
                                'title': 'Dasar Python'
                            }
                        },
                        'questions': [
                            {
                                'id': 1,
                                'question_text': 'Apa ekstensi file Python?',
                                'question_type': 'multiple_choice',
                                'points': 10,
                                'options': [
                                    {'text': '.py', 'is_correct': False},
                                    {'text': '.python', 'is_correct': False},
                                    {'text': '.pyt', 'is_correct': False}
                                ]
                            }
                        ],
                        'user_attempts': 2,
                        'can_attempt': True
                    }
                }
            }
        },
        403: {
            'description': 'Akses ditolak - Enrollment diperlukan',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'You need to be enrolled to access this quiz'
                    }
                }
            }
        },
        404: {
            'description': 'Quiz tidak ditemukan'
        }
    }
)
class QuizDetailView(generics.RetrieveAPIView):
    """Get quiz details"""
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Quiz.objects.all()
    
    def get_queryset(self) -> 'QuerySet[Quiz]':  # type: ignore
        return Quiz.objects.select_related('lesson__section__course').prefetch_related('questions')
    
    def retrieve(self, request, *args, **kwargs):
        quiz = self.get_object()
        
        # Check if user can access the lesson
        if not quiz.lesson.can_be_accessed_by_user(request.user):
            return Response(
                {'error': 'You need to be enrolled to access this quiz'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().retrieve(request, *args, **kwargs)


@extend_schema(
    tags=['Lessons'],
    summary='Mulai Attempt Quiz',
    description='''
    Membuat attempt baru untuk mengerjakan quiz.
    
    **Validasi sebelum attempt:**
    1. User harus memiliki akses ke lesson/quiz
    2. Belum mencapai batas maksimum attempt
    3. Quiz masih dalam periode aktif (jika ada)
    
    **Data attempt yang dibuat:**
    - Attempt number berdasarkan urutan
    - Total questions dan points dari quiz
    - Timestamp mulai attempt
    - Status IN_PROGRESS
    
    **Batas Attempt:**
    Setiap quiz memiliki max_attempts. Jika sudah mencapai
    batas, user tidak dapat membuat attempt baru.
    ''',
    parameters=[
        OpenApiParameter(
            name='quiz_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID quiz yang akan dikerjakan'
        )
    ],
    responses={
        201: {
            'description': 'Attempt quiz berhasil dibuat',
            'content': {
                'application/json': {
                    'example': {
                        'id': 1,
                        'attempt_number': 1,
                        'status': 'in_progress',
                        'started_at': '2024-01-15T10:30:00Z',
                        'total_questions': 10,
                        'total_points': 100,
                        'quiz': {
                            'id': 1,
                            'title': 'Quiz Python Basics',
                            'time_limit_minutes': 30
                        },
                        'student': {
                            'id': 1,
                            'full_name': 'John Doe'
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Bad Request - Batas attempt tercapai',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'Maximum attempts (3) reached'
                    }
                }
            }
        },
        403: {
            'description': 'Akses ditolak - Enrollment diperlukan',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'You are not enrolled in this course'
                    }
                }
            }
        },
        404: {
            'description': 'Quiz tidak ditemukan'
        }
    }
)
class QuizAttemptCreateView(generics.CreateAPIView):
    """Start new quiz attempt"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Check access
        if not quiz.lesson.can_be_accessed_by_user(request.user):
            return Response(
                {'error': 'You are not enrolled in this course'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check attempt limits
        existing_attempts = QuizAttempt.objects.filter(
            student=request.user, 
            quiz=quiz
        ).count()
        
        if existing_attempts >= quiz.max_attempts:
            return Response(
                {'error': f'Maximum attempts ({quiz.max_attempts}) reached'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new attempt
        attempt = QuizAttempt.objects.create(
            student=request.user,
            quiz=quiz,
            attempt_number=existing_attempts + 1,
            total_questions=quiz.total_questions,
            total_points=sum(q.points for q in quiz.questions.all())  # type: ignore[attr-defined]
        )
        
        serializer = QuizAttemptSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Lessons'],
    summary='Submit Jawaban Quiz',
    description='''
    Submit jawaban untuk quiz attempt yang sedang berlangsung.
    
    **Proses submission:**
    1. Validasi attempt masih IN_PROGRESS
    2. Process setiap jawaban yang dikirim
    3. Evaluasi jawaban (benar/salah)
    4. Hitung score dan persentase
    5. Update status attempt menjadi COMPLETED
    6. Auto-complete lesson jika quiz passed
    
    **Format jawaban:**
    - Multiple choice: array selected_options
    - True/False: answer_text (true/false)
    - Short answer: answer_text (string)
    - Essay: answer_text (akan di-review manual)
    
    **Auto Lesson Completion:**
    Jika quiz passed (score >= passing_score), lesson
    akan otomatis ditandai sebagai completed.
    ''',
    parameters=[
        OpenApiParameter(
            name='attempt_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID attempt quiz yang akan di-submit'
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'answers': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'question': {
                                'type': 'integer',
                                'description': 'ID pertanyaan'
                            },
                            'answer_text': {
                                'type': 'string',
                                'description': 'Jawaban text (untuk true/false, short answer, essay)'
                            },
                            'selected_options': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'description': 'Opsi yang dipilih (untuk multiple choice)'
                            }
                        }
                    }
                }
            },
            'required': ['answers']
        }
    },
    examples=[
        OpenApiExample(
            'Submit Quiz Answers',
            value={
                'answers': [
                    {
                        'question': 1,
                        'selected_options': ['.py']
                    },
                    {
                        'question': 2,
                        'answer_text': 'true'
                    },
                    {
                        'question': 3,
                        'answer_text': 'print'
                    }
                ]
            },
            request_only=True
        )
    ],
    responses={
        200: {
            'description': 'Quiz berhasil di-submit',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Quiz submitted successfully',
                        'result': {
                            'id': 1,
                            'attempt_number': 1,
                            'status': 'completed',
                            'correct_answers': 8,
                            'total_questions': 10,
                            'earned_points': 80,
                            'total_points': 100,
                            'percentage_score': 80.0,
                            'is_passed': True,
                            'completed_at': '2024-01-15T11:00:00Z'
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Bad Request - Attempt sudah selesai atau tidak valid'
        },
        403: {
            'description': 'Forbidden - Bukan attempt milik user'
        },
        404: {
            'description': 'Attempt tidak ditemukan'
        }
    }
)
class QuizSubmissionView(generics.CreateAPIView):
    """Submit quiz answers"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, attempt_id):
        attempt = get_object_or_404(
            QuizAttempt, 
            id=attempt_id, 
            student=request.user,
            status=QuizAttempt.AttemptStatus.IN_PROGRESS
        )
        
        answers_data = request.data.get('answers', [])
        
        # Process each answer
        correct_count = 0
        earned_points = 0
        
        for answer_data in answers_data:
            question_id = answer_data.get('question')
            question = get_object_or_404(QuizQuestion, id=question_id, quiz=attempt.quiz)
            
            # Create answer record
            answer = QuizAnswer.objects.create(
                attempt=attempt,
                question=question,
                answer_text=answer_data.get('answer_text', ''),
                selected_options=answer_data.get('selected_options', [])
            )
            
            # Check if answer is correct
            is_correct = self._check_answer_correctness(question, answer)
            answer.is_correct = is_correct
            answer.points_earned = question.points if is_correct else 0
            answer.save()
            
            if is_correct:
                correct_count += 1
                earned_points += question.points
        
        # Update attempt
        attempt.status = QuizAttempt.AttemptStatus.COMPLETED
        attempt.correct_answers = correct_count
        attempt.earned_points = earned_points
        attempt.percentage_score = (earned_points / attempt.total_points) * 100 if attempt.total_points > 0 else 0
        attempt.completed_at = timezone.now()
        attempt.save()
        
        # Update lesson progress if quiz is passed
        if attempt.is_passed:
            progress, created = LessonProgress.objects.get_or_create(
                student=request.user,
                lesson=attempt.quiz.lesson
            )
            if not progress.is_completed:
                progress.mark_completed()
        
        return Response({
            'message': 'Quiz submitted successfully',
            'result': QuizAttemptSerializer(attempt).data
        })
    
    def _check_answer_correctness(self, question, answer):
        """Check if the answer is correct"""
        if question.question_type == QuizQuestion.QuestionType.MULTIPLE_CHOICE:
            correct_options = [opt['text'] for opt in question.options if opt.get('is_correct')]
            return set(answer.selected_options) == set(correct_options)
        
        elif question.question_type == QuizQuestion.QuestionType.TRUE_FALSE:
            return answer.answer_text.lower() == question.correct_answer.lower()
        
        elif question.question_type == QuizQuestion.QuestionType.SHORT_ANSWER:
            return answer.answer_text.lower().strip() == question.correct_answer.lower().strip()
        
        # Essay questions require manual grading
        return False


@extend_schema(
    tags=['Lessons'],
    summary='Komentar Lesson',
    description='''
    Mengelola komentar pada lesson tertentu.
    
    **GET Request:**
    - Mendapatkan semua komentar top-level (bukan reply)
    - Hanya komentar yang sudah diapprove yang ditampilkan
    - Diurutkan berdasarkan tanggal terbaru
    
    **POST Request:**
    - Membuat komentar baru pada lesson
    - Memerlukan enrollment aktif pada kursus
    - Komentar perlu approval sebelum ditampilkan
    
    **Moderasi:**
    Komentar akan melalui proses moderasi dan hanya
    yang approved yang akan ditampilkan secara publik.
    ''',
    parameters=[
        OpenApiParameter(
            name='lesson_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID lesson yang akan dilihat komentarnya'
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'content': {
                    'type': 'string',
                    'description': 'Isi komentar',
                    'example': 'Penjelasan yang sangat bagus! Terima kasih.'
                }
            },
            'required': ['content']
        }
    },
    responses={
        200: {
            'description': 'Daftar komentar berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'count': 5,
                        'results': [
                            {
                                'id': 1,
                                'content': 'Penjelasan yang sangat bagus!',
                                'user': {
                                    'id': 1,
                                    'full_name': 'John Doe',
                                    'profile_picture': 'http://localhost:8000/media/profiles/john.jpg'
                                },
                                'created_at': '2024-01-15T10:30:00Z',
                                'replies_count': 2,
                                'is_approved': True
                            }
                        ]
                    }
                }
            }
        },
        201: {
            'description': 'Komentar berhasil dibuat',
            'content': {
                'application/json': {
                    'example': {
                        'id': 2,
                        'content': 'Komentar baru',
                        'is_approved': False,
                        'created_at': '2024-01-15T10:35:00Z',
                        'message': 'Comment submitted for approval'
                    }
                }
            }
        },
        403: {
            'description': 'Akses ditolak - Enrollment diperlukan'
        }
    }
)
class LessonCommentListView(generics.ListCreateAPIView):
    """List and create lesson comments"""
    serializer_class = LessonCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = LessonComment.objects.all()
    
    def get_queryset(self) -> 'QuerySet[LessonComment]':  # type: ignore
        lesson_id = self.kwargs.get('lesson_id')
        return LessonComment.objects.filter(
            lesson_id=lesson_id,
            is_approved=True,
            parent__isnull=True  # Top-level comments only
        ).select_related('user').order_by('-created_at')
    
    def perform_create(self, serializer):
        lesson_id = self.kwargs.get('lesson_id')
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Check access
        if not lesson.can_be_accessed_by_user(self.request.user):
            raise PermissionDenied("You are not enrolled in this course")
        
        serializer.save(user=self.request.user, lesson=lesson)


@extend_schema(
    tags=['Lessons'],
    summary='Reply Komentar Lesson',
    description='''
    Membuat reply/balasan untuk komentar lesson yang sudah ada.
    
    **Fitur Reply:**
    - Reply akan terhubung ke parent comment
    - Dapat reply ke komentar manapun yang approved
    - Memerlukan akses ke lesson yang sama
    
    **Hierarki Komentar:**
    Sistem mendukung nested comments dengan struktur:
    - Parent comment (top-level)
    - Reply comments (child level)
    
    **Notifikasi:**
    Sistem akan mengirim notifikasi ke pemilik parent comment
    ketika ada reply baru.
    ''',
    parameters=[
        OpenApiParameter(
            name='comment_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID parent comment yang akan di-reply'
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'content': {
                    'type': 'string',
                    'description': 'Isi reply',
                    'example': 'Saya setuju dengan pendapat Anda.'
                }
            },
            'required': ['content']
        }
    },
    responses={
        201: {
            'description': 'Reply berhasil dibuat',
            'content': {
                'application/json': {
                    'example': {
                        'id': 3,
                        'content': 'Saya setuju dengan pendapat Anda.',
                        'parent': {
                            'id': 1,
                            'content': 'Penjelasan yang sangat bagus!'
                        },
                        'user': {
                            'id': 2,
                            'full_name': 'Jane Smith'
                        },
                        'created_at': '2024-01-15T10:40:00Z',
                        'is_approved': False
                    }
                }
            }
        },
        403: {
            'description': 'Akses ditolak - Enrollment diperlukan'
        },
        404: {
            'description': 'Parent comment tidak ditemukan'
        }
    }
)
class LessonCommentReplyView(generics.CreateAPIView):
    """Reply to lesson comment"""
    serializer_class = LessonCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        parent_id = self.kwargs.get('comment_id')
        parent_comment = get_object_or_404(LessonComment, id=parent_id)
        
        # Check access to lesson
        if not parent_comment.lesson.can_be_accessed_by_user(self.request.user):
            raise PermissionDenied("You are not enrolled in this course")
        
        serializer.save(
            user=self.request.user, 
            lesson=parent_comment.lesson,
            parent=parent_comment
        )


@extend_schema(
    tags=['Lessons'],
    summary='Catatan Student',
    description='''
    Mengelola catatan pribadi student untuk lesson tertentu.
    
    **GET Request:**
    - Mendapatkan semua catatan student untuk lesson
    - Diurutkan berdasarkan timestamp dalam video
    - Hanya catatan milik student yang login
    
    **POST Request:**
    - Membuat catatan baru pada timestamp tertentu
    - Catatan bersifat pribadi (hanya terlihat oleh pembuat)
    - Dapat dikaitkan dengan timestamp video tertentu
    
    **Fitur Catatan:**
    - Time-stamped notes: catatan pada detik tertentu dalam video
    - Rich text content: mendukung formatting text
    - Private & searchable: hanya terlihat oleh pemilik
    ''',
    parameters=[
        OpenApiParameter(
            name='lesson_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID lesson yang akan dilihat catatannya'
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'content': {
                    'type': 'string',
                    'description': 'Isi catatan',
                    'example': 'Poin penting: Python menggunakan indentasi untuk blok kode'
                },
                'timestamp_seconds': {
                    'type': 'integer',
                    'description': 'Detik ke berapa dalam video (opsional)',
                    'example': 300
                }
            },
            'required': ['content']
        }
    },
    responses={
        200: {
            'description': 'Daftar catatan berhasil diambil',
            'content': {
                'application/json': {
                    'example': [
                        {
                            'id': 1,
                            'content': 'Poin penting: Python menggunakan indentasi',
                            'timestamp_seconds': 300,
                            'created_at': '2024-01-15T10:30:00Z',
                            'updated_at': '2024-01-15T10:30:00Z',
                            'lesson': {
                                'id': 1,
                                'title': 'Pengenalan Python'
                            }
                        }
                    ]
                }
            }
        },
        201: {
            'description': 'Catatan berhasil dibuat',
            'content': {
                'application/json': {
                    'example': {
                        'id': 2,
                        'content': 'Catatan baru',
                        'timestamp_seconds': 450,
                        'created_at': '2024-01-15T10:35:00Z'
                    }
                }
            }
        },
        403: {
            'description': 'Akses ditolak - Enrollment diperlukan'
        }
    }
)
class StudentNoteListView(generics.ListCreateAPIView):
    """Student's lesson notes"""
    serializer_class = LessonNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = LessonNote.objects.all()
    
    def get_queryset(self) -> 'QuerySet[LessonNote]':  # type: ignore
        lesson_id = self.kwargs.get('lesson_id')
        return LessonNote.objects.filter(
            student=self.request.user,
            lesson_id=lesson_id
        ).order_by('timestamp_seconds', 'created_at')
    
    def perform_create(self, serializer):
        lesson_id = self.kwargs.get('lesson_id')
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Check access
        if not lesson.can_be_accessed_by_user(self.request.user):
            raise PermissionDenied("You are not enrolled in this course")
        
        serializer.save(student=self.request.user, lesson=lesson)


@extend_schema(
    tags=['Lessons'],
    summary='Detail Catatan Student',
    description='''
    Mengelola catatan individual student (view, edit, delete).
    
    **GET Request:**
    - Mendapatkan detail catatan spesifik
    - Hanya catatan milik student yang login
    
    **PUT/PATCH Request:**
    - Edit catatan yang sudah ada
    - Dapat mengubah content dan timestamp
    
    **DELETE Request:**
    - Hapus catatan secara permanen
    - Tidak dapat di-restore setelah dihapus
    
    **Keamanan:**
    Student hanya dapat mengelola catatan mereka sendiri.
    ''',
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID catatan yang akan dikelola'
        )
    ],
    responses={
        200: {
            'description': 'Detail catatan berhasil diambil/diupdate',
            'content': {
                'application/json': {
                    'example': {
                        'id': 1,
                        'content': 'Catatan yang sudah diupdate',
                        'timestamp_seconds': 300,
                        'created_at': '2024-01-15T10:30:00Z',
                        'updated_at': '2024-01-15T10:45:00Z',
                        'lesson': {
                            'id': 1,
                            'title': 'Pengenalan Python'
                        },
                        'student': {
                            'id': 1,
                            'full_name': 'John Doe'
                        }
                    }
                }
            }
        },
        204: {
            'description': 'Catatan berhasil dihapus'
        },
        403: {
            'description': 'Forbidden - Hanya pemilik catatan yang dapat mengelola'
        },
        404: {
            'description': 'Catatan tidak ditemukan'
        }
    }
)
class StudentNoteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Individual note management"""
    serializer_class = LessonNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = LessonNote.objects.all()
    
    def get_queryset(self) -> 'QuerySet[LessonNote]':  # type: ignore
        return LessonNote.objects.filter(student=self.request.user)


@extend_schema(
    tags=['Lessons'],
    summary='Overview Progress Student',
    description='''
    Mendapatkan ringkasan lengkap progress pembelajaran student untuk kursus tertentu.
    
    **Data yang disediakan:**
    - Informasi enrollment (tanggal daftar, status, progress percentage)
    - Progress lesson (total, completed, persentase completion)
    - Statistik quiz attempts
    - Aktivitas pembelajaran terkini
    
    **Perhitungan Progress:**
    - Hanya lesson mandatory yang dihitung dalam progress
    - Completion percentage dihitung dari lesson yang diselesaikan
    - Quiz attempts menunjukkan aktivitas assessment
    
    **Analytics Value:**
    Endpoint ini berguna untuk dashboard student dan
    instructor analytics tentang engagement student.
    ''',
    parameters=[
        OpenApiParameter(
            name='course_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID kursus yang akan dilihat progressnya'
        )
    ],
    responses={
        200: {
            'description': 'Overview progress berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'enrollment': {
                            'enrolled_at': '2024-01-10T09:00:00Z',
                            'progress_percentage': 65.5,
                            'status': 'active'
                        },
                        'lesson_progress': {
                            'total_lessons': 20,
                            'completed_lessons': 13,
                            'completion_percentage': 65.0
                        },
                        'quiz_attempts': 8,
                        'recent_activity': [
                            {
                                'id': 1,
                                'lesson': {
                                    'id': 5,
                                    'title': 'Python Variables'
                                },
                                'completion_percentage': 100.0,
                                'is_completed': True,
                                'last_accessed_at': '2024-01-15T10:30:00Z',
                                'time_spent_minutes': 25
                            }
                        ]
                    }
                }
            }
        },
        403: {
            'description': 'Akses ditolak - Enrollment diperlukan',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'You are not enrolled in this course'
                    }
                }
            }
        },
        404: {
            'description': 'Kursus tidak ditemukan'
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def student_progress_overview(request, course_id):
    """Get student's progress overview for a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check enrollment
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        return Response(
            {'error': 'You are not enrolled in this course'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get progress data
    total_lessons = Lesson.objects.filter(section__course=course, is_mandatory=True).count()
    completed_lessons = LessonProgress.objects.filter(
        student=request.user,
        lesson__section__course=course,
        lesson__is_mandatory=True,
        is_completed=True
    ).count()
    
    # Get quiz attempts
    quiz_attempts = QuizAttempt.objects.filter(
        student=request.user,
        quiz__lesson__section__course=course,
        status=QuizAttempt.AttemptStatus.COMPLETED
    ).count()
    
    # Recent activity
    recent_progress = LessonProgress.objects.filter(
        student=request.user,
        lesson__section__course=course
    ).order_by('-last_accessed_at')[:5]
    
    return Response({
        'enrollment': {
            'enrolled_at': enrollment.enrolled_at,
            'progress_percentage': float(enrollment.progress_percentage),
            'status': enrollment.status
        },
        'lesson_progress': {
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'completion_percentage': (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        },
        'quiz_attempts': quiz_attempts,
        'recent_activity': LessonProgressSerializer(recent_progress, many=True).data
    })