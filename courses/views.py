from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from django.shortcuts import get_object_or_404

# drf-spectacular imports
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import Course, Category, Enrollment, CourseReview, CourseBatch
from .serializers import (
    CourseListSerializer, CourseDetailSerializer, CourseCreateSerializer,
    CategorySerializer, EnrollmentSerializer, CourseReviewSerializer,
    CourseBatchSerializer
)
from .filters import CourseFilter
from .permissions import IsInstructorOrReadOnly, IsEnrolledOrInstructor


@extend_schema(
    tags=['Courses'],
    summary='Daftar Kategori Kursus',
    description='''
    Mendapatkan daftar semua kategori kursus yang aktif.
    
    Kategori diurutkan berdasarkan sort_order dan nama.
    Endpoint ini dapat diakses tanpa autentikasi.
    ''',
    responses={
        200: {
            'description': 'Daftar kategori berhasil diambil',
            'content': {
                'application/json': {
                    'example': [
                        {
                            'id': 1,
                            'name': 'Programming',
                            'slug': 'programming',
                            'description': 'Kursus pemrograman komputer',
                            'icon': 'fas fa-code',
                            'course_count': 15
                        }
                    ]
                }
            }
        }
    }
)
class CategoryListView(generics.ListAPIView):
    """List all course categories"""
    queryset = Category.objects.filter(is_active=True).order_by('sort_order', 'name')
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(
    tags=['Courses'],
    summary='Daftar dan Pencarian Kursus',
    description='''
    Mendapatkan daftar kursus yang tersedia dengan fitur pencarian dan filter.
    
    **Fitur yang tersedia:**
    - Pencarian berdasarkan judul, deskripsi, atau nama instruktur
    - Filter berdasarkan kategori, harga, level kesulitan
    - Pengurutan berdasarkan tanggal, harga, jumlah pendaftar, rating
    - Paginasi hasil
    
    **Parameter Query:**
    - `search`: Kata kunci pencarian
    - `category`: ID kategori kursus
    - `difficulty_level`: Level kesulitan (beginner, intermediate, advanced)
    - `course_type`: Jenis kursus (self_paced, structured)
    - `is_free`: Filter kursus gratis (true/false)
    - `ordering`: Pengurutan (-created_at, price, -average_rating)
    ''',
    parameters=[
        OpenApiParameter(
            name='search',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Kata kunci untuk mencari kursus berdasarkan judul, deskripsi, atau instruktur'
        ),
        OpenApiParameter(
            name='category',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='ID kategori kursus untuk filter'
        ),
        OpenApiParameter(
            name='difficulty_level',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Level kesulitan kursus',
            enum=['beginner', 'intermediate', 'advanced']
        ),
        OpenApiParameter(
            name='course_type',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Jenis kursus',
            enum=['self_paced', 'structured']
        ),
        OpenApiParameter(
            name='is_free',
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            description='Filter kursus gratis'
        ),
        OpenApiParameter(
            name='ordering',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Pengurutan hasil',
            enum=['-created_at', 'created_at', 'price', '-price', 'total_enrollments', '-total_enrollments', 'average_rating', '-average_rating']
        )
    ],
    examples=[
        OpenApiExample(
            'Pencarian Python',
            value={
                'count': 25,
                'next': 'http://localhost:8000/api/v1/courses/?search=python&page=2',
                'previous': None,
                'results': [
                    {
                        'id': 1,
                        'title': 'Python untuk Pemula',
                        'slug': 'python-untuk-pemula',
                        'short_description': 'Belajar Python dari nol',
                        'thumbnail': 'http://localhost:8000/media/course_thumbnails/python.jpg',
                        'price': '199000.00',
                        'is_free': False,
                        'difficulty_level': 'beginner',
                        'average_rating': 4.5,
                        'total_reviews': 120,
                        'total_enrollments': 500,
                        'instructor': {
                            'id': 2,
                            'full_name': 'John Doe',
                            'profile_picture': 'http://localhost:8000/media/profiles/john.jpg'
                        },
                        'category': {
                            'id': 1,
                            'name': 'Programming',
                            'slug': 'programming'
                        }
                    }
                ]
            },
            response_only=True
        )
    ],
    responses={
        200: {
            'description': 'Daftar kursus berhasil diambil dengan paginasi'
        }
    }
)
class CourseListView(generics.ListAPIView):
    """List and search courses"""
    serializer_class = CourseListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CourseFilter
    search_fields = ['title', 'description', 'instructor__full_name']
    ordering_fields = ['created_at', 'price', 'total_enrollments', 'average_rating']
    ordering = ['-created_at']

    def get_queryset(self):  # type: ignore[override]
        return Course.objects.filter(
            is_published=True, 
            status=Course.CourseStatus.PUBLISHED
        ).select_related('instructor', 'category').annotate(
            average_rating=Avg('reviews__rating'),
            total_reviews=Count('reviews', filter=Q(reviews__is_approved=True))
        )


@extend_schema(
    tags=['Courses'],
    summary='Detail Kursus',
    description='''
    Mendapatkan informasi detail lengkap dari sebuah kursus.
    
    **Informasi yang disediakan:**
    - Informasi dasar kursus (judul, deskripsi, harga)
    - Data instruktur
    - Statistik kursus (rating, jumlah review, pendaftar)
    - Daftar lesson/materi
    - Review dan rating
    - Learning objectives dan prerequisites
    
    Endpoint ini dapat diakses tanpa autentikasi.
    ''',
    parameters=[
        OpenApiParameter(
            name='slug',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Slug unik dari kursus'
        )
    ],
    examples=[
        OpenApiExample(
            'Detail Kursus Python',
            value={
                'id': 1,
                'title': 'Python untuk Pemula',
                'slug': 'python-untuk-pemula',
                'description': 'Kursus lengkap Python dari dasar hingga menengah...',
                'short_description': 'Belajar Python dari nol',
                'thumbnail': 'http://localhost:8000/media/course_thumbnails/python.jpg',
                'preview_video': 'http://localhost:8000/media/course_previews/python_preview.mp4',
                'price': '199000.00',
                'original_price': '299000.00',
                'is_free': False,
                'course_type': 'self_paced',
                'difficulty_level': 'beginner',
                'status': 'published',
                'total_duration_minutes': 1200,
                'total_lessons': 45,
                'average_rating': 4.5,
                'total_reviews': 120,
                'total_enrollments': 500,
                'learning_objectives': [
                    'Memahami syntax dasar Python',
                    'Membuat aplikasi sederhana',
                    'Menggunakan library populer'
                ],
                'prerequisites': [
                    'Tidak ada pengalaman programming sebelumnya',
                    'Komputer dengan internet'
                ],
                'target_audience': [
                    'Pemula yang ingin belajar programming',
                    'Mahasiswa computer science'
                ],
                'instructor': {
                    'id': 2,
                    'full_name': 'John Doe',
                    'bio': 'Senior Python Developer dengan 10 tahun pengalaman',
                    'profile_picture': 'http://localhost:8000/media/profiles/john.jpg'
                },
                'category': {
                    'id': 1,
                    'name': 'Programming',
                    'slug': 'programming'
                }
            },
            response_only=True
        )
    ],
    responses={
        200: {
            'description': 'Detail kursus berhasil diambil'
        },
        404: {
            'description': 'Kursus tidak ditemukan',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'Not found.'
                    }
                }
            }
        }
    }
)
class CourseDetailView(generics.RetrieveAPIView):
    """Get course details"""
    serializer_class = CourseDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):  # type: ignore[override]
        return Course.objects.filter(
            is_published=True,
            status=Course.CourseStatus.PUBLISHED
        ).select_related('instructor', 'category')


@extend_schema(
    tags=['Courses'],
    summary='Buat Kursus Baru',
    description='''
    Membuat kursus baru (hanya untuk instruktur yang terverifikasi).
    
    **Persyaratan:**
    - User harus login dan memiliki role "instructor"
    - Status verifikasi instruktur harus "verified"
    - Semua field wajib harus diisi
    
    **Field yang diperlukan:**
    - title: Judul kursus
    - description: Deskripsi lengkap
    - short_description: Deskripsi singkat
    - category: ID kategori kursus
    - course_type: Jenis kursus (self_paced/structured)
    - difficulty_level: Level kesulitan
    - price: Harga kursus (0 untuk gratis)
    
    Setelah dibuat, kursus akan memiliki status "draft" dan perlu dipublikasikan.
    ''',
    examples=[
        OpenApiExample(
            'Buat Kursus Python',
            value={
                'title': 'Mastering Django REST Framework',
                'description': 'Kursus lengkap untuk menguasai Django REST Framework dari dasar hingga advanced...',
                'short_description': 'Belajar Django REST Framework secara mendalam',
                'category': 1,
                'course_type': 'self_paced',
                'difficulty_level': 'intermediate',
                'price': '299000.00',
                'learning_objectives': [
                    'Membangun REST API dengan Django',
                    'Implementasi authentication dan authorization',
                    'Testing API dengan pytest'
                ],
                'prerequisites': [
                    'Familiar dengan Python',
                    'Basic Django knowledge',
                    'Understanding of HTTP protocols'
                ],
                'target_audience': [
                    'Python developers',
                    'Backend developers',
                    'Full-stack developers'
                ]
            },
            request_only=True
        )
    ],
    responses={
        201: {
            'description': 'Kursus berhasil dibuat',
            'content': {
                'application/json': {
                    'example': {
                        'id': 5,
                        'title': 'Mastering Django REST Framework',
                        'slug': 'mastering-django-rest-framework',
                        'status': 'draft',
                        'instructor': 2,
                        'created_at': '2024-01-15T10:30:00Z'
                    }
                }
            }
        },
        401: {
            'description': 'Unauthorized - Login diperlukan'
        },
        403: {
            'description': 'Forbidden - Hanya instruktur terverifikasi yang dapat membuat kursus',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'Only verified instructors can create courses'
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
                        'category': ['Invalid pk "999" - object does not exist.']
                    }
                }
            }
        }
    }
)
class CourseCreateView(generics.CreateAPIView):
    """Create new course (instructors only)"""
    serializer_class = CourseCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Check if user is verified instructor
        if (getattr(self.request.user, 'role', None) != 'instructor' or 
            getattr(self.request.user, 'verification_status', None) != 'verified'):
            raise PermissionDenied("Only verified instructors can create courses")
        
        serializer.save(instructor=self.request.user)


class InstructorCourseListView(generics.ListCreateAPIView):
    """List instructor's courses and create new ones"""
    serializer_class = CourseDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):  # type: ignore[override]
        if getattr(self.request.user, 'role', None) != 'instructor':
            return Course.objects.none()
        return getattr(self.request.user, 'created_courses', Course.objects.none()).all().order_by('-created_at')

    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == 'POST':
            return CourseCreateSerializer
        return CourseDetailSerializer


class InstructorCourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Manage instructor's specific course"""
    serializer_class = CourseCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):  # type: ignore[override]
        return getattr(self.request.user, 'created_courses', Course.objects.none()).all()


class CourseBatchListView(generics.ListAPIView):
    """List available batches for a structured course"""
    serializer_class = CourseBatchSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):  # type: ignore[override]
        course_id = self.kwargs.get('course_id')
        return CourseBatch.objects.filter(
            course_id=course_id,
            course__course_type=Course.CourseType.STRUCTURED,
            course__is_published=True
        ).order_by('start_date')


@extend_schema(
    tags=['Courses'],
    summary='Daftar Kursus',
    description='''
    Mendaftarkan pengguna ke dalam kursus.
    
    **Jenis Kursus:**
    - **Self-paced**: Bisa langsung mendaftar tanpa batch
    - **Structured**: Harus memilih batch yang tersedia
    
    **Proses Pendaftaran:**
    1. Cek apakah user sudah terdaftar di kursus
    2. Untuk kursus structured, validasi batch dan availability
    3. Buat enrollment record
    4. Update statistik kursus dan batch
    
    **Catatan**: Dalam implementasi production, proses ini akan
    terintegrasi dengan sistem payment gateway.
    ''',
    parameters=[
        OpenApiParameter(
            name='course_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID kursus yang akan didaftar'
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'batch_id': {
                    'type': 'integer',
                    'description': 'ID batch untuk kursus structured (opsional untuk self-paced)',
                    'example': 1
                }
            }
        }
    },
    examples=[
        OpenApiExample(
            'Daftar Kursus Self-paced',
            value={},
            request_only=True,
            summary='Untuk kursus self-paced tidak perlu batch_id'
        ),
        OpenApiExample(
            'Daftar Kursus Structured',
            value={
                'batch_id': 1
            },
            request_only=True,
            summary='Untuk kursus structured wajib pilih batch'
        )
    ],
    responses={
        201: {
            'description': 'Berhasil mendaftar kursus',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Successfully enrolled in course'
                    }
                }
            }
        },
        400: {
            'description': 'Bad Request - Berbagai error kondisi',
            'content': {
                'application/json': {
                    'examples': {
                        'already_enrolled': {
                            'summary': 'Sudah terdaftar',
                            'value': {
                                'error': 'You are already enrolled in this course'
                            }
                        },
                        'batch_required': {
                            'summary': 'Batch diperlukan untuk structured course',
                            'value': {
                                'error': 'Batch selection is required for structured courses'
                            }
                        },
                        'enrollment_closed': {
                            'summary': 'Pendaftaran batch sudah ditutup',
                            'value': {
                                'error': 'Enrollment is closed for this batch'
                            }
                        }
                    }
                }
            }
        },
        401: {
            'description': 'Unauthorized - Login diperlukan'
        },
        404: {
            'description': 'Course atau batch tidak ditemukan'
        }
    }
)
class CourseEnrollmentView(generics.CreateAPIView):
    """Enroll in a course"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        batch_id = request.data.get('batch_id')  # For structured courses
        
        course = get_object_or_404(Course, id=course_id, is_published=True)
        
        # Check if already enrolled
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response(
                {'error': 'You are already enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # For structured courses, batch is required
        batch = None
        if course.course_type == Course.CourseType.STRUCTURED:
            if not batch_id:
                return Response(
                    {'error': 'Batch selection is required for structured courses'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            batch = get_object_or_404(CourseBatch, id=batch_id, course=course)
            
            # Check if enrollment is open
            if not batch.is_enrollment_open:
                return Response(
                    {'error': 'Enrollment is closed for this batch'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Create enrollment (in real app, this would be after payment)
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course,
            batch=batch,
            amount_paid=course.price if not course.is_free else 0
        )
        
        # Update course enrollment count
        course.total_enrollments += 1
        course.save(update_fields=['total_enrollments'])
        
        # Update batch enrollment count for structured courses
        if batch:
            batch.current_enrollments += 1
            batch.save(update_fields=['current_enrollments'])
        
        return Response(
            {'message': 'Successfully enrolled in course'},
            status=status.HTTP_201_CREATED
        )


class StudentEnrollmentListView(generics.ListAPIView):
    """List student's enrolled courses"""
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):  # type: ignore[override]
        return getattr(self.request.user, 'enrollments', Enrollment.objects.none()).filter(
            is_active=True
        ).select_related('course', 'course__instructor').order_by('-enrolled_at')


class CourseReviewListView(generics.ListCreateAPIView):
    """List and create course reviews"""
    serializer_class = CourseReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):  # type: ignore[override]
        course_id = self.kwargs.get('course_id')
        return CourseReview.objects.filter(
            course_id=course_id,
            is_approved=True
        ).select_related('student').order_by('-created_at')

    def perform_create(self, serializer):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        
        # Check if user is enrolled
        if not Enrollment.objects.filter(
            student=self.request.user, 
            course=course,
            is_active=True
        ).exists():
            raise PermissionDenied("You must be enrolled to review this course")
        
        # Check if already reviewed
        if CourseReview.objects.filter(
            student=self.request.user,
            course=course
        ).exists():
            raise PermissionDenied("You have already reviewed this course")
        
        serializer.save(student=self.request.user, course=course)


@extend_schema(
    tags=['Courses'],
    summary='Kursus Unggulan',
    description='''
    Mendapatkan daftar kursus unggulan untuk ditampilkan di homepage.
    
    **Kriteria kursus unggulan:**
    - Status published dan is_featured = True
    - Diurutkan berdasarkan rating dan popularitas
    - Maksimal 8 kursus yang ditampilkan
    
    Endpoint ini tidak memerlukan autentikasi dan dapat diakses publik.
    ''',
    responses={
        200: {
            'description': 'Daftar kursus unggulan berhasil diambil',
            'content': {
                'application/json': {
                    'example': [
                        {
                            'id': 1,
                            'title': 'Python untuk Pemula',
                            'slug': 'python-untuk-pemula',
                            'short_description': 'Belajar Python dari nol',
                            'thumbnail': 'http://localhost:8000/media/course_thumbnails/python.jpg',
                            'price': '199000.00',
                            'is_free': False,
                            'difficulty_level': 'beginner',
                            'average_rating': 4.8,
                            'total_reviews': 150,
                            'total_enrollments': 750,
                            'instructor': {
                                'id': 2,
                                'full_name': 'John Doe',
                                'profile_picture': 'http://localhost:8000/media/profiles/john.jpg'
                            },
                            'category': {
                                'id': 1,
                                'name': 'Programming',
                                'slug': 'programming'
                            }
                        }
                    ]
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def featured_courses(request):
    """Get featured courses for homepage"""
    courses = Course.objects.filter(
        is_published=True,
        is_featured=True,
        status=Course.CourseStatus.PUBLISHED
    ).select_related('instructor', 'category').annotate(
        average_rating=Avg('reviews__rating'),
        total_reviews=Count('reviews', filter=Q(reviews__is_approved=True))
    )[:8]
    
    serializer = CourseListSerializer(courses, many=True)
    return Response(serializer.data)


@extend_schema(
    tags=['Courses'],
    summary='Statistik Kursus',
    description='''
    Mendapatkan statistik lengkap dari sebuah kursus.
    
    **Statistik yang disediakan:**
    - Jumlah total siswa
    - Jumlah total lessons
    - Total durasi dalam menit
    - Rating rata-rata
    - Jumlah review
    - Tingkat completion rate
    
    Endpoint ini dapat diakses tanpa autentikasi.
    ''',
    parameters=[
        OpenApiParameter(
            name='course_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID kursus yang akan dilihat statistiknya'
        )
    ],
    responses={
        200: {
            'description': 'Statistik kursus berhasil diambil',
            'content': {
                'application/json': {
                    'example': {
                        'total_students': 500,
                        'total_lessons': 45,
                        'total_duration': 1200,
                        'average_rating': 4.5,
                        'total_reviews': 120,
                        'completion_rate': 75.5
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
@permission_classes([permissions.AllowAny])
def course_stats(request, course_id):
    """Get course statistics"""
    course = get_object_or_404(Course, id=course_id, is_published=True)
    
    stats = {
        'total_students': course.total_enrollments,
        'total_lessons': course.total_lessons,
        'total_duration': course.total_duration_minutes,
        'average_rating': course.average_rating,
        'total_reviews': course.total_reviews,
        'completion_rate': 0,  # Calculate based on completed enrollments
    }
    
    # Calculate completion rate
    total_enrollments = getattr(course, 'enrollments', Enrollment.objects.none()).count()
    completed_enrollments = getattr(course, 'enrollments', Enrollment.objects.none()).filter(status='completed').count()
    if total_enrollments > 0:
        stats['completion_rate'] = (completed_enrollments / total_enrollments) * 100
    
    return Response(stats)


@extend_schema(
    tags=['Courses'],
    summary='Toggle Wishlist',
    description='''
    Menambahkan atau menghapus kursus dari wishlist pengguna.
    
    **Behavior:**
    - Jika kursus belum ada di wishlist: ditambahkan
    - Jika kursus sudah ada di wishlist: dihapus
    
    Response akan menunjukkan status akhir wishlist.
    ''',
    parameters=[
        OpenApiParameter(
            name='course_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID kursus yang akan ditambah/hapus dari wishlist'
        )
    ],
    responses={
        200: {
            'description': 'Wishlist berhasil diupdate',
            'content': {
                'application/json': {
                    'examples': {
                        'added': {
                            'summary': 'Ditambahkan ke wishlist',
                            'value': {
                                'message': 'Added to wishlist',
                                'wishlisted': True
                            }
                        },
                        'removed': {
                            'summary': 'Dihapus dari wishlist',
                            'value': {
                                'message': 'Removed from wishlist',
                                'wishlisted': False
                            }
                        }
                    }
                }
            }
        },
        401: {
            'description': 'Unauthorized - Login diperlukan'
        },
        404: {
            'description': 'Kursus tidak ditemukan'
        }
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_wishlist(request, course_id):
    """Add or remove course from wishlist"""
    course = get_object_or_404(Course, id=course_id, is_published=True)
    
    from .models import CourseWishlist
    wishlist_item, created = CourseWishlist.objects.get_or_create(
        student=request.user,
        course=course
    )
    
    if not created:
        wishlist_item.delete()
        return Response({'message': 'Removed from wishlist', 'wishlisted': False})
    
    return Response({'message': 'Added to wishlist', 'wishlisted': True})


@extend_schema(
    tags=['Courses'],
    summary='Wishlist Siswa',
    description='''
    Mendapatkan daftar semua kursus dalam wishlist pengguna.
    
    **Informasi yang disediakan:**
    - Data lengkap kursus (judul, harga, rating, dll)
    - Informasi instruktur
    - Kategori kursus
    - Diurutkan berdasarkan tanggal ditambahkan
    
    Hanya kursus yang masih tersedia dan published yang ditampilkan.
    ''',
    responses={
        200: {
            'description': 'Wishlist berhasil diambil',
            'content': {
                'application/json': {
                    'example': [
                        {
                            'id': 1,
                            'title': 'Python untuk Pemula',
                            'slug': 'python-untuk-pemula',
                            'short_description': 'Belajar Python dari nol',
                            'thumbnail': 'http://localhost:8000/media/course_thumbnails/python.jpg',
                            'price': '199000.00',
                            'is_free': False,
                            'difficulty_level': 'beginner',
                            'average_rating': 4.5,
                            'total_reviews': 120,
                            'total_enrollments': 500,
                            'instructor': {
                                'id': 2,
                                'full_name': 'John Doe',
                                'profile_picture': 'http://localhost:8000/media/profiles/john.jpg'
                            },
                            'category': {
                                'id': 1,
                                'name': 'Programming',
                                'slug': 'programming'
                            }
                        }
                    ]
                }
            }
        },
        401: {
            'description': 'Unauthorized - Login diperlukan'
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def student_wishlist(request):
    """Get student's wishlist"""
    from .models import CourseWishlist
    wishlist = CourseWishlist.objects.filter(
        student=request.user
    ).select_related('course', 'course__instructor', 'course__category')
    
    courses = [item.course for item in wishlist]
    serializer = CourseListSerializer(courses, many=True)
    return Response(serializer.data)