from typing import Any, Optional, TYPE_CHECKING
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Avg, Count, QuerySet

# drf-spectacular imports
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

if TYPE_CHECKING:
    from django.db.models import QuerySet as QS

from .models import (
    Assignment, AssignmentSubmission, AssignmentFile, AssignmentGroup,
    AssignmentGroupMember, AssignmentRubric, RubricGrade, PeerReview,
    PeerReviewAssignment, PeerReviewSubmission
)
from .serializers import (
    AssignmentSerializer, AssignmentDetailSerializer, AssignmentCreateSerializer,
    AssignmentSubmissionSerializer, AssignmentSubmissionDetailSerializer,
    AssignmentSubmissionCreateSerializer, AssignmentGradeSerializer,
    AssignmentGroupSerializer, AssignmentRubricSerializer, RubricGradeSerializer,
    PeerReviewSerializer, PeerReviewSubmissionSerializer
)
from courses.models import Course, Enrollment
from courses.permissions import IsInstructorOfCourse, IsEnrolledOrInstructor


@extend_schema(
    tags=['Assignments'],
    summary='Daftar Assignment Kursus',
    description='''
    Mendapatkan semua assignment untuk kursus tertentu.
    
    **Access Control berdasarkan role:**
    - **Instructor**: Melihat semua assignment (termasuk draft)
    - **Student**: Hanya assignment yang published dan sesuai batch
    
    **Filter untuk Student:**
    - Harus enrolled di kursus
    - Hanya assignment yang published
    - Untuk structured course: filtered by batch
    
    **Sorting:**
    - Instructor: berdasarkan tanggal dibuat (terbaru)
    - Student: berdasarkan tanggal assigned (terbaru)
    ''',
    parameters=[
        OpenApiParameter(
            name='course_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID kursus yang akan dilihat assignment-nya'
        )
    ],
    responses={
        200: {
            'description': 'Daftar assignment berhasil diambil',
            'content': {
                'application/json': {
                    'example': [
                        {
                            'id': 1,
                            'title': 'Project Akhir Python',
                            'description': 'Buat aplikasi web sederhana menggunakan Django',
                            'assignment_type': 'individual',
                            'max_points': 100,
                            'assigned_date': '2024-01-15T09:00:00Z',
                            'due_date': '2024-01-30T23:59:59Z',
                            'is_published': True,
                            'course': {
                                'id': 1,
                                'title': 'Python untuk Pemula'
                            },
                            'submission_status': 'not_submitted',
                            'is_overdue': False
                        }
                    ]
                }
            }
        },
        403: {
            'description': 'Forbidden - Enrollment diperlukan',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'You are not enrolled in this course'
                    }
                }
            }
        },
        404: {
            'description': 'Course tidak ditemukan'
        }
    }
)
class CourseAssignmentListView(generics.ListAPIView):
    """List assignments for a course"""
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore[override]
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        
        # Check if user has access to the course
        if course.instructor == self.request.user:
            # Instructor sees all assignments
            return Assignment.objects.filter(course=course).order_by('-created_at')
        else:
            # Students see only published assignments they're enrolled in
            try:
                enrollment = Enrollment.objects.get(
                    student=self.request.user, 
                    course=course,
                    is_active=True
                )
                queryset = Assignment.objects.filter(
                    course=course,
                    is_published=True
                )
                
                # Filter by batch if it's a structured course
                if course.course_type == Course.CourseType.STRUCTURED and enrollment.batch:
                    queryset = queryset.filter(batch=enrollment.batch)
                
                return queryset.order_by('-assigned_date')
                
            except Enrollment.DoesNotExist:
                return Assignment.objects.none()


@extend_schema(
    tags=['Assignments'],
    summary='Detail Assignment',
    description='''
    Mendapatkan detail lengkap dari sebuah assignment.
    
    **Informasi yang disediakan:**
    - Deskripsi lengkap assignment
    - Instructions dan requirements
    - File attachments
    - Rubric grading (jika ada)
    - Submission information
    
    **Access Control:**
    - Instructor: Full access ke semua assignment
    - Student: Hanya assignment yang published dan accessible
    
    **Batch Validation:**
    Untuk structured course, assignment hanya dapat diakses
    oleh student yang terdaftar di batch yang sesuai.
    ''',
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID assignment yang akan dilihat'
        )
    ],
    responses={
        200: {
            'description': 'Detail assignment berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'id': 1,
                        'title': 'Project Akhir Python',
                        'description': 'Buat aplikasi web sederhana menggunakan Django...',
                        'instructions': '<h2>Instruksi Lengkap</h2><p>1. Buat virtual environment...</p>',
                        'assignment_type': 'individual',
                        'max_points': 100,
                        'assigned_date': '2024-01-15T09:00:00Z',
                        'due_date': '2024-01-30T23:59:59Z',
                        'allow_late_submission': True,
                        'late_penalty_per_day': 5.0,
                        'course': {
                            'id': 1,
                            'title': 'Python untuk Pemula',
                            'instructor': {
                                'id': 2,
                                'full_name': 'Dr. Jane Smith'
                            }
                        },
                        'files': [
                            {
                                'id': 1,
                                'name': 'requirements.txt',
                                'file_url': 'http://localhost:8000/media/assignments/requirements.txt'
                            }
                        ],
                        'rubric': {
                            'id': 1,
                            'criteria': [
                                {
                                    'name': 'Code Quality',
                                    'max_points': 40,
                                    'description': 'Clean, readable, well-documented code'
                                }
                            ]
                        },
                        'user_submission': None,
                        'can_submit': True,
                        'time_remaining': '15 days, 2 hours'
                    }
                }
            }
        },
        403: {
            'description': 'Akses ditolak - berbagai kondisi',
            'content': {
                'application/json': {
                    'examples': {
                        'not_published': {
                            'summary': 'Assignment belum dipublish',
                            'value': {'error': 'Assignment not published yet'}
                        },
                        'wrong_batch': {
                            'summary': 'Batch tidak sesuai',
                            'value': {'error': 'Assignment not available for your batch'}
                        },
                        'not_enrolled': {
                            'summary': 'Belum enrollment',
                            'value': {'error': 'You are not enrolled in this course'}
                        }
                    }
                }
            }
        }
    }
)
class AssignmentDetailView(generics.RetrieveAPIView):
    """Get assignment details"""
    serializer_class = AssignmentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore[override]
        return Assignment.objects.select_related('course', 'batch')
    
    def retrieve(self, request, *args, **kwargs):
        assignment = self.get_object()
        
        # Check access permissions
        if assignment.course.instructor == request.user:
            # Instructor has full access
            pass
        else:
            # Check if student is enrolled and assignment is published
            try:
                enrollment = Enrollment.objects.get(
                    student=request.user,
                    course=assignment.course,
                    is_active=True
                )
                
                if not assignment.is_published:
                    return Response(
                        {'error': 'Assignment not published yet'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Check batch access for structured courses
                if (assignment.batch and enrollment.batch and 
                    assignment.batch != enrollment.batch):
                    return Response(
                        {'error': 'Assignment not available for your batch'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                    
            except Enrollment.DoesNotExist:
                return Response(
                    {'error': 'You are not enrolled in this course'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().retrieve(request, *args, **kwargs)


@extend_schema(
    tags=['Assignments'],
    summary='Buat Assignment Baru',
    description='''
    Membuat assignment baru untuk kursus (hanya instructor).
    
    **Jenis Assignment:**
    - **Individual**: Dikerjakan sendiri oleh setiap student
    - **Group**: Dikerjakan dalam grup dengan pembagian tugas
    - **Peer Review**: Assignment dengan sistem peer review
    
    **Field yang diperlukan:**
    - title: Judul assignment
    - description: Deskripsi singkat
    - instructions: Instruksi lengkap (HTML)
    - course: ID kursus tujuan
    - max_points: Point maksimum
    - due_date: Deadline submission
    
    **Validasi:**
    - Hanya instructor yang memiliki kursus yang dapat membuat
    - Course harus valid dan aktif
    ''',
    examples=[
        OpenApiExample(
            'Individual Assignment',
            value={
                'title': 'Quiz Python Functions',
                'description': 'Test pemahaman tentang functions dalam Python',
                'instructions': '<h2>Instruksi</h2><p>Buat 5 function Python yang mendemonstrasikan...</p>',
                'assignment_type': 'individual',
                'max_points': 100,
                'course': 1,
                'due_date': '2024-02-15T23:59:59Z',
                'allow_late_submission': True,
                'late_penalty_per_day': 10.0,
                'submission_format': 'file',
                'is_published': False
            },
            request_only=True
        ),
        OpenApiExample(
            'Group Project',
            value={
                'title': 'Final Web Application Project',
                'description': 'Build a complete web application using Django',
                'instructions': '<h2>Group Project</h2><p>Form groups of 3-4 students...</p>',
                'assignment_type': 'group',
                'max_points': 200,
                'course': 1,
                'due_date': '2024-03-01T23:59:59Z',
                'max_group_size': 4,
                'allow_late_submission': False,
                'submission_format': 'url'
            },
            request_only=True
        )
    ],
    responses={
        201: {
            'description': 'Assignment berhasil dibuat',
            'content': {
                'application/json': {
                    'example': {
                        'id': 5,
                        'title': 'Quiz Python Functions',
                        'assignment_type': 'individual',
                        'course': {
                            'id': 1,
                            'title': 'Python untuk Pemula'
                        },
                        'max_points': 100,
                        'is_published': False,
                        'created_at': '2024-01-15T10:30:00Z'
                    }
                }
            }
        },
        403: {
            'description': 'Forbidden - Hanya instructor pemilik kursus',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'You can only create assignments for your own courses'
                    }
                }
            }
        },
        400: {
            'description': 'Bad Request - Data tidak valid',
            'content': {
                'application/json': {
                    'example': {
                        'title': ['This field is required.'],
                        'due_date': ['Date cannot be in the past.']
                    }
                }
            }
        }
    }
)
class AssignmentCreateView(generics.CreateAPIView):
    """Create new assignment (instructors only)"""
    serializer_class = AssignmentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Verify instructor owns the course
        course = serializer.validated_data['course']
        if course.instructor != self.request.user:
            raise PermissionDenied("You can only create assignments for your own courses")
        
        serializer.save()


@extend_schema(
    tags=['Assignments'],
    summary='Kelola Assignment Instructor',
    description='''
    Endpoint untuk instructor mengelola semua assignment mereka.
    
    **GET Request:**
    - Daftar semua assignment milik instructor
    - Termasuk draft dan published assignments
    - Diurutkan berdasarkan tanggal terbaru
    
    **POST Request:**
    - Membuat assignment baru
    - Otomatis assign ke instructor yang login
    
    **Filter Options:**
    - course_id: Filter by specific course
    - status: Filter by published/draft status
    ''',
    responses={
        200: {
            'description': 'Daftar assignment instructor berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'count': 12,
                        'results': [
                            {
                                'id': 1,
                                'title': 'Python Quiz 1',
                                'assignment_type': 'individual',
                                'max_points': 100,
                                'due_date': '2024-01-30T23:59:59Z',
                                'is_published': True,
                                'course': {
                                    'id': 1,
                                    'title': 'Python untuk Pemula'
                                },
                                'submissions_count': 25,
                                'graded_count': 18
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
class InstructorAssignmentListView(generics.ListCreateAPIView):
    """Instructor's assignment management"""
    serializer_class = AssignmentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore[override]
        if hasattr(self.request.user, 'role') and getattr(self.request.user, 'role', None) != 'instructor':
            return Assignment.objects.none()
        return Assignment.objects.filter(
            course__instructor=self.request.user
        ).select_related('course', 'batch').order_by('-created_at')
    
    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == 'POST':
            return AssignmentCreateSerializer
        return AssignmentDetailSerializer


@extend_schema(
    tags=['Assignments'],
    summary='Detail Assignment Instructor',
    description='''
    Mengelola assignment spesifik milik instructor (view, edit, delete).
    
    **GET Request:**
    - Detail lengkap assignment
    - Statistik submissions dan grading
    
    **PUT/PATCH Request:**
    - Edit assignment details
    - Update instructions, dates, points
    
    **DELETE Request:**
    - Hapus assignment (hanya jika belum ada submissions)
    
    **Keamanan:**
    Hanya instructor pemilik assignment yang dapat mengelola.
    ''',
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID assignment yang akan dikelola'
        )
    ],
    responses={
        200: {
            'description': 'Assignment berhasil diambil/diupdate'
        },
        204: {
            'description': 'Assignment berhasil dihapus'
        },
        403: {
            'description': 'Forbidden - Hanya pemilik assignment'
        },
        400: {
            'description': 'Cannot delete assignment with submissions'
        }
    }
)
class InstructorAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Instructor assignment detail management"""
    serializer_class = AssignmentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore[override]
        return Assignment.objects.filter(course__instructor=self.request.user)


@extend_schema(
    tags=['Assignments'],
    summary='Submit Assignment',
    description='''
    Submit pekerjaan assignment oleh student.
    
    **Validasi sebelum submit:**
    1. Assignment masih dalam periode submission
    2. Student enrolled di kursus yang tepat
    3. Batch sesuai (untuk structured course)
    4. Belum submit sebelumnya (kecuali allow_resubmission=true)
    
    **Format Submission:**
    - File upload: Upload file assignment
    - Text: Submit dalam bentuk text
    - URL: Submit link ke repository/project
    
    **Status setelah submit:**
    Assignment akan berstatus 'draft' dan dapat diedit
    sampai di-finalize dengan endpoint submit.
    ''',
    parameters=[
        OpenApiParameter(
            name='assignment_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID assignment yang akan di-submit'
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'submission_text': {
                    'type': 'string',
                    'description': 'Konten submission dalam text/HTML'
                },
                'submission_url': {
                    'type': 'string',
                    'description': 'URL ke repository atau project online'
                },
                'files': {
                    'type': 'array',
                    'items': {'type': 'string', 'format': 'binary'},
                    'description': 'File-file yang di-upload'
                }
            }
        }
    },
    examples=[
        OpenApiExample(
            'Text Submission',
            value={
                'submission_text': '<h2>Jawaban</h2><p>1. Variable dalam Python...</p>'
            },
            request_only=True
        ),
        OpenApiExample(
            'URL Submission',
            value={
                'submission_url': 'https://github.com/student/python-project',
                'submission_text': 'Repository berisi project Django lengkap dengan dokumentasi.'
            },
            request_only=True
        )
    ],
    responses={
        201: {
            'description': 'Submission berhasil dibuat',
            'content': {
                'application/json': {
                    'example': {
                        'id': 1,
                        'status': 'draft',
                        'submission_text': 'Konten submission',
                        'submission_url': 'https://github.com/student/project',
                        'submitted_at': None,
                        'assignment': {
                            'id': 1,
                            'title': 'Python Project'
                        },
                        'student': {
                            'id': 1,
                            'full_name': 'John Doe'
                        },
                        'files': [],
                        'can_edit': True
                    }
                }
            }
        },
        400: {
            'description': 'Bad Request - Assignment submission is closed'
        },
        403: {
            'description': 'Forbidden - Not enrolled or wrong batch'
        }
    }
)
class AssignmentSubmissionCreateView(generics.CreateAPIView):
    """Submit assignment"""
    serializer_class = AssignmentSubmissionCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        assignment_id = kwargs.get('assignment_id')
        assignment = get_object_or_404(Assignment, id=assignment_id)
        
        # Check if user can submit
        if not assignment.can_submit():
            return Response(
                {'error': 'Assignment submission is closed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check enrollment
        try:
            enrollment = Enrollment.objects.get(
                student=request.user,
                course=assignment.course,
                is_active=True
            )
            
            # Check batch for structured courses
            if (assignment.batch and enrollment.batch and 
                assignment.batch != enrollment.batch):
                return Response(
                    {'error': 'Assignment not available for your batch'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'You are not enrolled in this course'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Add assignment to serializer context
        serializer = self.get_serializer(
            data=request.data,
            context={'assignment': assignment, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        
        return Response(
            AssignmentSubmissionDetailSerializer(submission).data,
            status=status.HTTP_201_CREATED
        )


class AssignmentSubmissionDetailView(generics.RetrieveUpdateAPIView):
    """View and update assignment submission"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == 'GET':
            return AssignmentSubmissionDetailSerializer
        return AssignmentSubmissionCreateSerializer
    
    def get_queryset(self):  # type: ignore[override]
        return AssignmentSubmission.objects.select_related(
            'assignment', 'student', 'graded_by'
        ).prefetch_related('files')
    
    def get_object(self):
        submission = super().get_object()
        
        # Check permissions - allow access if user is student, instructor, or admin
        if (submission.student == self.request.user or
            submission.assignment.course.instructor == self.request.user or
            (hasattr(self.request.user, 'role') and getattr(self.request.user, 'role', None) == 'admin')):
            pass
        else:
            raise PermissionDenied("You don't have access to this submission")
        
        return submission


@extend_schema(
    tags=['Assignments'],
    summary='Finalize Assignment Submission',
    description='''
    Finalize dan submit assignment untuk grading.
    
    **Proses finalisasi:**
    1. Ubah status dari 'draft' ke 'submitted'
    2. Set timestamp submitted_at
    3. Tidak dapat diedit lagi setelah submitted
    4. Masuk antrian untuk grading
    
    **Validasi:**
    - Assignment masih dalam deadline
    - Submission dalam status 'draft'
    - Milik student yang login
    
    **Late Submission:**
    Jika melewati deadline, akan dikenakan penalty
    sesuai konfigurasi assignment.
    ''',
    parameters=[
        OpenApiParameter(
            name='submission_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID submission yang akan di-finalize'
        )
    ],
    responses={
        200: {
            'description': 'Assignment berhasil di-submit',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Assignment submitted successfully',
                        'submission': {
                            'id': 1,
                            'status': 'submitted',
                            'submitted_at': '2024-01-15T14:30:00Z',
                            'is_late': False,
                            'late_penalty': 0.0,
                            'assignment': {
                                'id': 1,
                                'title': 'Python Project',
                                'due_date': '2024-01-20T23:59:59Z'
                            }
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Bad Request - Assignment sudah submitted atau closed',
            'content': {
                'application/json': {
                    'examples': {
                        'already_submitted': {
                            'summary': 'Sudah di-submit',
                            'value': {'error': 'Assignment already submitted'}
                        },
                        'submission_closed': {
                            'summary': 'Submission ditutup',
                            'value': {'error': 'Assignment submission is closed'}
                        }
                    }
                }
            }
        },
        403: {
            'description': 'Forbidden - Bukan milik student'
        },
        404: {
            'description': 'Submission tidak ditemukan'
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_assignment(request, submission_id):
    """Submit assignment for grading"""
    submission = get_object_or_404(
        AssignmentSubmission,
        id=submission_id,
        student=request.user
    )
    
    if submission.status == AssignmentSubmission.SubmissionStatus.SUBMITTED:
        return Response(
            {'error': 'Assignment already submitted'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if assignment allows submissions
    if not submission.assignment.can_submit():
        return Response(
            {'error': 'Assignment submission is closed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Submit the assignment
    submission.submit()
    
    return Response({
        'message': 'Assignment submitted successfully',
        'submission': AssignmentSubmissionDetailSerializer(submission).data
    })


class AssignmentSubmissionListView(generics.ListAPIView):
    """List submissions for an assignment (instructors only)"""
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore[override]
        assignment_id = self.kwargs.get('assignment_id')
        assignment = get_object_or_404(Assignment, id=assignment_id)
        
        # Check if user is the instructor
        if assignment.course.instructor != self.request.user:
            raise PermissionDenied("Only the instructor can view submissions")
        
        return getattr(assignment, 'submissions', AssignmentSubmission.objects.filter(assignment=assignment)).select_related('student').order_by('-submitted_at')


class AssignmentGradeView(generics.UpdateAPIView):
    """Grade assignment submission (instructors only)"""
    serializer_class = AssignmentGradeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore[override]
        return AssignmentSubmission.objects.select_related('assignment__course')
    
    def get_object(self):
        submission = super().get_object()
        
        # Check if user is the instructor
        if submission.assignment.course.instructor != self.request.user:
            raise PermissionDenied("Only the instructor can grade submissions")
        
        return submission


@extend_schema(
    tags=['Assignments'],
    summary='Assignment Student',
    description='''
    Mendapatkan semua assignment untuk student across all enrolled courses.
    
    **Filter Options:**
    - **pending**: Assignment yang belum di-submit
    - **submitted**: Assignment yang sudah di-submit
    - **overdue**: Assignment yang melewati deadline
    
    **Student Dashboard:**
    Endpoint ini berguna untuk student dashboard yang menampilkan
    semua assignment dari berbagai kursus yang diikuti.
    
    **Sorting:** Berdasarkan assigned_date (terbaru ke lama)
    ''',
    parameters=[
        OpenApiParameter(
            name='status',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter berdasarkan status: pending, submitted, overdue',
            enum=['pending', 'submitted', 'overdue']
        )
    ],
    responses={
        200: {
            'description': 'Daftar assignment student berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'count': 8,
                        'results': [
                            {
                                'id': 1,
                                'title': 'Python Quiz 1',
                                'assignment_type': 'individual',
                                'max_points': 100,
                                'due_date': '2024-01-25T23:59:59Z',
                                'course': {
                                    'id': 1,
                                    'title': 'Python untuk Pemula',
                                    'instructor': {
                                        'full_name': 'Dr. Jane Smith'
                                    }
                                },
                                'submission_status': 'submitted',
                                'is_overdue': False,
                                'grade': 85,
                                'time_remaining': '5 days'
                            }
                        ]
                    }
                }
            }
        }
    }
)
class StudentAssignmentListView(generics.ListAPIView):
    """Student's assignments across all courses"""
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore[override]
        # Get assignments from all enrolled courses
        enrolled_courses = Enrollment.objects.filter(
            student=self.request.user,
            is_active=True
        ).values_list('course_id', flat=True)
        
        queryset = Assignment.objects.filter(
            course_id__in=enrolled_courses,
            is_published=True
        )
        
        # Filter by status if requested
        status_filter = getattr(self.request, 'query_params', self.request.GET).get('status')
        if status_filter == 'pending':
            # Assignments without submission
            submitted_assignment_ids = AssignmentSubmission.objects.filter(
                student=self.request.user,
                status__in=['submitted', 'graded']
            ).values_list('assignment_id', flat=True)
            queryset = queryset.exclude(id__in=submitted_assignment_ids)
        elif status_filter == 'submitted':
            # Assignments with submissions
            submitted_assignment_ids = AssignmentSubmission.objects.filter(
                student=self.request.user,
                status__in=['submitted', 'graded']
            ).values_list('assignment_id', flat=True)
            queryset = queryset.filter(id__in=submitted_assignment_ids)
        elif status_filter == 'overdue':
            queryset = queryset.filter(due_date__lt=timezone.now())
        
        return queryset.order_by('-assigned_date')


class AssignmentGroupListView(generics.ListCreateAPIView):
    """List and create assignment groups"""
    serializer_class = AssignmentGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):  # type: ignore[override]
        assignment_id = self.kwargs.get('assignment_id')
        assignment = get_object_or_404(Assignment, id=assignment_id)
        
        # Check access
        if not self._check_assignment_access(assignment):
            return AssignmentGroup.objects.none()
        
        return getattr(assignment, 'groups', AssignmentGroup.objects.filter(assignment=assignment)).all()
    
    def perform_create(self, serializer):
        assignment_id = self.kwargs.get('assignment_id')
        assignment = get_object_or_404(Assignment, id=assignment_id)
        
        if not self._check_assignment_access(assignment):
            raise PermissionDenied("You don't have access to this assignment")
        
        if assignment.assignment_type != Assignment.AssignmentType.GROUP:
            raise PermissionDenied("This assignment doesn't allow groups")
        
        group = serializer.save(assignment=assignment, leader=self.request.user)
        
        # Add creator as first member
        AssignmentGroupMember.objects.create(
            group=group,
            student=self.request.user
        )
    
    def _check_assignment_access(self, assignment):
        """Check if user has access to assignment"""
        if assignment.course.instructor == self.request.user:
            return True
        
        try:
            enrollment = Enrollment.objects.get(
                student=self.request.user,
                course=assignment.course,
                is_active=True
            )
            return assignment.is_published
        except Enrollment.DoesNotExist:
            return False


@extend_schema(
    tags=['Assignments'],
    summary='Join Group Assignment',
    description='''
    Bergabung dengan grup untuk group assignment.
    
    **Validasi sebelum join:**
    1. User enrolled di kursus yang tepat
    2. Group masih memiliki slot kosong
    3. User belum bergabung di group lain untuk assignment ini
    4. Assignment berjenis 'group'
    
    **Group Management:**
    - Setiap group memiliki leader (pembuat group)
    - Maksimal member sesuai max_group_size
    - Satu student hanya bisa join satu group per assignment
    
    **Notifikasi:**
    Group leader akan mendapat notifikasi ketika ada member baru.
    ''',
    parameters=[
        OpenApiParameter(
            name='group_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID group yang akan diikuti'
        )
    ],
    responses={
        200: {
            'description': 'Berhasil bergabung dengan group',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Successfully joined group',
                        'group': {
                            'id': 1,
                            'name': 'Team Alpha',
                            'leader': {
                                'id': 2,
                                'full_name': 'Jane Smith'
                            },
                            'members': [
                                {
                                    'id': 2,
                                    'full_name': 'Jane Smith'
                                },
                                {
                                    'id': 1,
                                    'full_name': 'John Doe'
                                }
                            ],
                            'assignment': {
                                'id': 1,
                                'title': 'Group Project'
                            },
                            'current_size': 2,
                            'max_size': 4
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Bad Request - Berbagai kondisi error',
            'content': {
                'application/json': {
                    'examples': {
                        'group_full': {
                            'summary': 'Group penuh',
                            'value': {'error': 'Group is full'}
                        },
                        'already_in_group': {
                            'summary': 'Sudah dalam group',
                            'value': {'error': 'You are already in a group for this assignment'}
                        }
                    }
                }
            }
        },
        403: {
            'description': 'Forbidden - Not enrolled'
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def join_assignment_group(request, group_id):
    """Join an assignment group"""
    group = get_object_or_404(AssignmentGroup, id=group_id)
    
    # Check if user can access the assignment
    try:
        enrollment = Enrollment.objects.get(
            student=request.user,
            course=group.assignment.course,
            is_active=True
        )
    except Enrollment.DoesNotExist:
        return Response(
            {'error': 'You are not enrolled in this course'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if group has space
    if not group.can_add_member():
        return Response(
            {'error': 'Group is full'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user is already in a group for this assignment
    existing_membership = AssignmentGroupMember.objects.filter(
        student=request.user,
        group__assignment=group.assignment
    ).exists()
    
    if existing_membership:
        return Response(
            {'error': 'You are already in a group for this assignment'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Add to group
    AssignmentGroupMember.objects.create(
        group=group,
        student=request.user
    )
    
    return Response({
        'message': 'Successfully joined group',
        'group': AssignmentGroupSerializer(group).data
    })


class AssignmentRubricView(generics.RetrieveAPIView):
    """Get assignment rubric"""
    serializer_class = AssignmentRubricSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):  # type: ignore[override]
        assignment_id = self.kwargs.get('assignment_id')
        assignment = get_object_or_404(Assignment, id=assignment_id)
        
        # Check access
        try:
            enrollment = Enrollment.objects.get(
                student=self.request.user,
                course=assignment.course,
                is_active=True
            )
        except Enrollment.DoesNotExist:
            if assignment.course.instructor != self.request.user:
                raise PermissionDenied("You don't have access to this assignment")
        
        try:
            return getattr(assignment, 'rubric', None) or AssignmentRubric.objects.filter(assignment=assignment).first()
        except (AssignmentRubric.DoesNotExist, AttributeError):
            return Response(
                {'error': 'No rubric available for this assignment'},
                status=status.HTTP_404_NOT_FOUND
            )


@extend_schema(
    tags=['Assignments'],
    summary='Statistik Assignment',
    description='''
    Mendapatkan statistik lengkap assignment untuk instructor.
    
    **Statistik yang disediakan:**
    - Total submissions received
    - Jumlah yang sudah di-grade
    - Late submissions count
    - Average grade dan distribusi
    - Timeline submissions
    
    **Grade Distribution:**
    Menampilkan distribusi nilai dalam kategori:
    - A (90-100), B (80-89), C (70-79), D (60-69), F (0-59)
    
    **Analytics Value:**
    Data ini berguna untuk evaluasi assignment difficulty
    dan student performance analysis.
    ''',
    parameters=[
        OpenApiParameter(
            name='assignment_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID assignment yang akan dilihat statistiknya'
        )
    ],
    responses={
        200: {
            'description': 'Statistik assignment berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'total_submissions': 25,
                        'submitted_count': 23,
                        'graded_count': 20,
                        'late_submissions': 3,
                        'average_grade': 82.5,
                        'grade_distribution': {
                            'A (90-100)': 8,
                            'B (80-89)': 7,
                            'C (70-79)': 4,
                            'D (60-69)': 1,
                            'F (0-59)': 0
                        },
                        'submission_timeline': [
                            {
                                'date': '2024-01-15',
                                'count': 5
                            },
                            {
                                'date': '2024-01-16',
                                'count': 8
                            },
                            {
                                'date': '2024-01-17',
                                'count': 10
                            }
                        ]
                    }
                }
            }
        },
        403: {
            'description': 'Forbidden - Hanya instructor yang dapat melihat statistik',
            'content': {
                'application/json': {
                    'example': {
                        'error': 'Only the instructor can view statistics'
                    }
                }
            }
        },
        404: {
            'description': 'Assignment tidak ditemukan'
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def assignment_statistics(request, assignment_id):
    """Get assignment statistics (instructors only)"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Check if user is the instructor
    if assignment.course.instructor != request.user:
        return Response(
            {'error': 'Only the instructor can view statistics'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    submissions = getattr(assignment, 'submissions', AssignmentSubmission.objects.filter(assignment=assignment)).all()
    
    stats = {
        'total_submissions': submissions.count(),
        'submitted_count': submissions.filter(
            status__in=['submitted', 'graded']
        ).count(),
        'graded_count': submissions.exclude(grade__isnull=True).count(),
        'late_submissions': submissions.filter(is_late=True).count(),
        'average_grade': submissions.exclude(grade__isnull=True).aggregate(
            avg=Avg('grade')
        )['avg'] or 0,
        'grade_distribution': _get_grade_distribution(submissions),
        'submission_timeline': _get_submission_timeline(submissions)
    }
    
    return Response(stats)


def _get_grade_distribution(submissions):
    """Get grade distribution for assignment"""
    graded_submissions = submissions.exclude(grade__isnull=True)
    
    distribution = {
        'A (90-100)': graded_submissions.filter(grade__gte=90).count(),
        'B (80-89)': graded_submissions.filter(grade__gte=80, grade__lt=90).count(),
        'C (70-79)': graded_submissions.filter(grade__gte=70, grade__lt=80).count(),
        'D (60-69)': graded_submissions.filter(grade__gte=60, grade__lt=70).count(),
        'F (0-59)': graded_submissions.filter(grade__lt=60).count(),
    }
    
    return distribution


def _get_submission_timeline(submissions):
    """Get submission timeline data"""
    from django.db.models import Count
    from django.db.models.functions import TruncDate
    
    timeline = submissions.filter(
        submitted_at__isnull=False
    ).annotate(
        date=TruncDate('submitted_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    return list(timeline)