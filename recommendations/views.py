from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import (
    Recommendation, RecommendationFeedback, 
    RecommendationSettings, UserRecommendationProfile
)
from .serializers import (
    RecommendationSerializer, RecommendationFeedbackSerializer,
    RecommendationSettingsSerializer, UserRecommendationProfileSerializer,
    UserCourseInteractionSerializer
)
from .services import recommendation_service
from courses.models import Course


class RecommendationListView(generics.ListAPIView):
    """
    View untuk menampilkan daftar rekomendasi pengguna yang terautentikasi
    
    Mengembalikan daftar rekomendasi aktif untuk pengguna saat ini, diurutkan berdasarkan skor.
    Hanya rekomendasi yang belum kedaluwarsa yang akan ditampilkan.
    """
    
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['AI Recommendations'],
        summary="Daftar rekomendasi pengguna",
        description="Mengembalikan daftar rekomendasi aktif untuk pengguna yang terautentikasi, diurutkan berdasarkan skor.",
        responses={200: RecommendationSerializer(many=True)},
        examples=[
            OpenApiExample(
                'Respons Daftar Rekomendasi',
                summary='Respons berhasil',
                description='Daftar objek rekomendasi',
                value={
                    "count": 2,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "user": {
                                "id": 1,
                                "email": "user@example.com",
                                "full_name": "John Doe"
                            },
                            "recommendation_type": "course",
                            "course": {
                                "id": 5,
                                "title": "Pengantar Machine Learning",
                                "description": "Pelajari dasar-dasar machine learning",
                                "instructor": "Dr. Smith",
                                "category": "Data Science",
                                "difficulty_level": "intermediate",
                                "duration": 120,
                                "rating": 4.5,
                                "enrollment_count": 1200
                            },
                            "algorithm_used": "collaborative",
                            "score": 0.85,
                            "reason": "Pengguna dengan minat serupa sangat merekomendasikan kursus ini",
                            "generated_at": "2023-06-15T10:30:00Z",
                            "expires_at": "2023-06-22T10:30:00Z"
                        }
                    ]
                }
            )
        ]
    )
    def get_queryset(self) -> QuerySet[Recommendation]:  # type: ignore[override]
        return Recommendation.objects.filter(
            user=self.request.user,
            expires_at__gt=timezone.now()
        ).select_related('course').order_by('-score')


class RecommendationDetailView(generics.RetrieveAPIView):
    """
    View untuk mengambil detail rekomendasi tertentu
    
    Mengembalikan informasi detail tentang rekomendasi tertentu berdasarkan ID-nya.
    Hanya rekomendasi milik pengguna yang terautentikasi yang dapat diakses.
    """
    
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['AI Recommendations'],
        summary="Ambil detail rekomendasi",
        description="Mengembalikan informasi detail tentang rekomendasi tertentu berdasarkan ID-nya.",
        responses={200: RecommendationSerializer},
        examples=[
            OpenApiExample(
                'Respons Detail Rekomendasi',
                summary='Respons berhasil',
                description='Objek rekomendasi tunggal',
                value={
                    "id": 1,
                    "user": {
                        "id": 1,
                        "email": "user@example.com",
                        "full_name": "John Doe"
                    },
                    "recommendation_type": "course",
                    "course": {
                        "id": 5,
                        "title": "Pengantar Machine Learning",
                        "description": "Pelajari dasar-dasar machine learning",
                        "instructor": "Dr. Smith",
                        "category": "Data Science",
                        "difficulty_level": "intermediate",
                        "duration": 120,
                        "rating": 4.5,
                        "enrollment_count": 1200
                    },
                    "algorithm_used": "collaborative",
                    "score": 0.85,
                    "reason": "Pengguna dengan minat serupa sangat merekomendasikan kursus ini",
                    "generated_at": "2023-06-15T10:30:00Z",
                    "expires_at": "2023-06-22T10:30:00Z"
                }
            )
        ]
    )
    def get_queryset(self) -> QuerySet[Recommendation]:  # type: ignore[override]
        return Recommendation.objects.filter(user=self.request.user)


@extend_schema(
    tags=['AI Recommendations'],
    summary="Hasilkan rekomendasi",
    description="Menghasilkan rekomendasi berbasis AI baru untuk pengguna yang terautentikasi. Ini akan menggantikan rekomendasi yang ada sebelumnya untuk pengguna tersebut.",
    request=None,
    responses={
        200: OpenApiTypes.OBJECT,
        500: OpenApiTypes.OBJECT
    },
    examples=[
        OpenApiExample(
            'Respons Berhasil',
            summary='Berhasil menghasilkan',
            description='Rekomendasi berhasil dihasilkan',
            value={
                "message": "Rekomendasi berhasil dihasilkan",
                "recommendations": [
                    # Array objek rekomendasi
                ]
            }
        ),
        OpenApiExample(
            'Respons Error',
            summary='Error saat menghasilkan',
            description='Gagal menghasilkan rekomendasi',
            value={
                "error": "Gagal menghasilkan rekomendasi: Kesalahan koneksi database"
            }
        )
    ]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_recommendations_view(request):
    """
    Menghasilkan rekomendasi baru untuk pengguna yang terautentikasi
    """
    try:
        recommendations = recommendation_service.generate_recommendations(
            request.user, force_refresh=True
        )
        serializer = RecommendationSerializer(recommendations, many=True)
        return Response({
            'message': 'Rekomendasi berhasil dihasilkan',
            'recommendations': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': f'Gagal menghasilkan rekomendasi: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['AI Recommendations'],
    summary="Tandai rekomendasi sebagai diklik",
    description="Menandai rekomendasi sebagai diklik oleh pengguna. Ini membantu meningkatkan algoritma rekomendasi.",
    parameters=[
        OpenApiParameter(
            name='recommendation_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID rekomendasi yang akan ditandai sebagai diklik',
            required=True
        )
    ],
    request=None,
    responses={
        200: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT,
        500: OpenApiTypes.OBJECT
    },
    examples=[
        OpenApiExample(
            'Respons Berhasil',
            summary='Berhasil ditandai',
            description='Rekomendasi berhasil ditandai sebagai diklik',
            value={
                "message": "Rekomendasi berhasil ditandai sebagai diklik"
            }
        ),
        OpenApiExample(
            'Respons Tidak Ditemukan',
            summary='Rekomendasi tidak ditemukan',
            description='Rekomendasi dengan ID yang diberikan tidak ditemukan',
            value={
                "error": "Rekomendasi tidak ditemukan"
            }
        ),
        OpenApiExample(
            'Respons Error',
            summary='Error pemrosesan',
            description='Gagal menandai rekomendasi sebagai diklik',
            value={
                "error": "Gagal menandai rekomendasi sebagai diklik: Kesalahan database"
            }
        )
    ]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_recommendation_clicked_view(request, recommendation_id):
    """
    Menandai rekomendasi sebagai diklik oleh pengguna
    """
    try:
        recommendation = recommendation_service.mark_recommendation_clicked(
            recommendation_id, request.user
        )
        if recommendation:
            return Response({
                'message': 'Rekomendasi berhasil ditandai sebagai diklik'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Rekomendasi tidak ditemukan'
            }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Gagal menandai rekomendasi sebagai diklik: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['AI Recommendations'],
    summary="Kirim umpan balik rekomendasi",
    description="Mengirim umpan balik pada rekomendasi untuk membantu meningkatkan sistem rekomendasi.",
    parameters=[
        OpenApiParameter(
            name='recommendation_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID rekomendasi yang akan diberi umpan balik',
            required=True
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'feedback_type': {
                    'type': 'string',
                    'enum': ['helpful', 'not_helpful', 'irrelevant', 'misleading'],
                    'description': 'Jenis umpan balik'
                },
                'comment': {
                    'type': 'string',
                    'description': 'Komentar opsional tentang rekomendasi'
                }
            },
            'required': ['feedback_type']
        }
    },
    responses={
        200: RecommendationFeedbackSerializer,
        400: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT,
        500: OpenApiTypes.OBJECT
    },
    examples=[
        OpenApiExample(
            'Contoh Request',
            summary='Request umpan balik',
            description='Contoh body request untuk mengirim umpan balik',
            value={
                "feedback_type": "helpful",
                "comment": "Rekomendasi ini sangat membantu untuk jalur pembelajaran saya"
            }
        ),
        OpenApiExample(
            'Respons Berhasil',
            summary='Umpan balik dikirim',
            description='Umpan balik berhasil dikirim',
            value={
                "message": "Umpan balik berhasil dikirim",
                "feedback": {
                    "id": 1,
                    "user": {
                        "id": 1,
                        "email": "user@example.com",
                        "full_name": "John Doe"
                    },
                    "recommendation": 1,
                    "feedback_type": "helpful",
                    "comment": "Rekomendasi ini sangat membantu untuk jalur pembelajaran saya",
                    "created_at": "2023-06-15T10:30:00Z"
                }
            }
        ),
        OpenApiExample(
            'Respons Bad Request',
            summary='Jenis umpan balik tidak ada',
            description='Jenis umpan balik diperlukan',
            value={
                "error": "feedback_type diperlukan"
            }
        ),
        OpenApiExample(
            'Respons Tidak Ditemukan',
            summary='Rekomendasi tidak ditemukan',
            description='Rekomendasi dengan ID yang diberikan tidak ditemukan',
            value={
                "error": "Rekomendasi tidak ditemukan"
            }
        )
    ]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_feedback_view(request, recommendation_id):
    """
    Mengirim umpan balik pada rekomendasi
    """
    try:
        feedback_type = request.data.get('feedback_type')
        comment = request.data.get('comment', '')
        
        if not feedback_type:
            return Response({
                'error': 'feedback_type diperlukan'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        feedback = recommendation_service.submit_feedback(
            recommendation_id, request.user, feedback_type, comment
        )
        
        if feedback:
            serializer = RecommendationFeedbackSerializer(feedback)
            return Response({
                'message': 'Umpan balik berhasil dikirim',
                'feedback': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Rekomendasi tidak ditemukan'
            }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Gagal mengirim umpan balik: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecommendationFeedbackListView(generics.ListAPIView):
    """
    View untuk menampilkan daftar umpan balik rekomendasi
    
    Mengembalikan daftar umpan balik yang dikirim oleh pengguna yang terautentikasi untuk rekomendasi.
    """
    
    serializer_class = RecommendationFeedbackSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['AI Recommendations'],
        summary="Daftar umpan balik rekomendasi",
        description="Mengembalikan daftar umpan balik yang dikirim oleh pengguna yang terautentikasi untuk rekomendasi.",
        responses={200: RecommendationFeedbackSerializer(many=True)},
        examples=[
            OpenApiExample(
                'Respons Daftar Umpan Balik',
                summary='Respons berhasil',
                description='Daftar objek umpan balik',
                value={
                    "count": 1,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "user": {
                                "id": 1,
                                "email": "user@example.com",
                                "full_name": "John Doe"
                            },
                            "recommendation": 1,
                            "feedback_type": "helpful",
                            "comment": "Rekomendasi ini sangat membantu untuk jalur pembelajaran saya",
                            "created_at": "2023-06-15T10:30:00Z"
                        }
                    ]
                }
            )
        ]
    )
    def get_queryset(self) -> QuerySet[RecommendationFeedback]:  # type: ignore[override]
        return RecommendationFeedback.objects.filter(
            user=self.request.user
        ).select_related('recommendation')


class UserRecommendationProfileView(generics.RetrieveUpdateAPIView):
    """
    View untuk mengambil dan memperbarui profil rekomendasi pengguna
    
    Memungkinkan pengguna untuk melihat profil rekomendasi mereka dan memperbarui preferensi mereka.
    """
    
    serializer_class = UserRecommendationProfileSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['AI Recommendations'],
        summary="Dapatkan profil rekomendasi pengguna",
        description="Mengembalikan profil rekomendasi untuk pengguna yang terautentikasi.",
        responses={200: UserRecommendationProfileSerializer},
        examples=[
            OpenApiExample(
                'Respons Profil',
                summary='Respons berhasil',
                description='Profil rekomendasi pengguna',
                value={
                    "id": 1,
                    "user": {
                        "id": 1,
                        "email": "user@example.com",
                        "full_name": "John Doe"
                    },
                    "preferred_categories": [1, 3, 5],
                    "preferred_difficulty_levels": ["beginner", "intermediate"],
                    "preferred_learning_styles": ["video", "interactive"],
                    "completed_courses": [],
                    "viewed_courses": [],
                    "last_active": "2023-06-15T10:30:00Z",
                    "total_learning_time": 120,
                    "feature_vector": {},
                    "created_at": "2023-06-01T09:00:00Z",
                    "updated_at": "2023-06-15T10:30:00Z"
                }
            )
        ]
    )
    def get_object(self) -> UserRecommendationProfile:  # type: ignore[override]
        profile, created = UserRecommendationProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile
    
    @extend_schema(
        tags=['AI Recommendations'],
        summary="Perbarui profil rekomendasi pengguna",
        description="Memperbarui profil rekomendasi untuk pengguna yang terautentikasi.",
        request=UserRecommendationProfileSerializer,
        responses={200: UserRecommendationProfileSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        summary="Perbarui sebagian profil rekomendasi pengguna",
        description="Memperbarui sebagian profil rekomendasi untuk pengguna yang terautentikasi.",
        request=UserRecommendationProfileSerializer,
        responses={200: UserRecommendationProfileSerializer}
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


@extend_schema(
    summary="Lacak interaksi kursus",
    description="Melacak interaksi pengguna dengan kursus untuk tujuan rekomendasi.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'course_id': {
                    'type': 'integer',
                    'description': 'ID kursus yang berinteraksi'
                },
                'interaction_type': {
                    'type': 'string',
                    'enum': ['viewed', 'enrolled', 'completed', 'rated', 'wishlisted', 'searched'],
                    'description': 'Jenis interaksi'
                },
                'rating': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 5,
                    'description': 'Peringkat yang diberikan pada kursus (1-5)'
                },
                'time_spent': {
                    'type': 'integer',
                    'description': 'Waktu yang dihabiskan pada kursus dalam menit'
                }
            },
            'required': ['course_id', 'interaction_type']
        }
    },
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT,
        500: OpenApiTypes.OBJECT
    },
    examples=[
        OpenApiExample(
            'Contoh Request',
            summary='Request pelacakan interaksi',
            description='Contoh body request untuk melacak interaksi kursus',
            value={
                "course_id": 5,
                "interaction_type": "viewed",
                "time_spent": 30
            }
        ),
        OpenApiExample(
            'Respons Berhasil',
            summary='Interaksi dilacak',
            description='Interaksi berhasil dilacak',
            value={
                "message": "Interaksi berhasil dilacak",
                "interaction": {
                    "id": 1,
                    "user": {
                        "id": 1,
                        "email": "user@example.com",
                        "full_name": "John Doe"
                    },
                    "course": {
                        "id": 5,
                        "title": "Pengantar Machine Learning",
                        "description": "Pelajari dasar-dasar machine learning",
                        "instructor": "Dr. Smith",
                        "category": "Data Science",
                        "difficulty_level": "intermediate",
                        "duration": 120,
                        "rating": 4.5,
                        "enrollment_count": 1200
                    },
                    "interaction_type": "viewed",
                    "time_spent": 30,
                    "interaction_date": "2023-06-15T10:30:00Z"
                }
            }
        ),
        OpenApiExample(
            'Respons Bad Request',
            summary='Field yang diperlukan tidak ada',
            description='ID kursus dan jenis interaksi diperlukan',
            value={
                "error": "course_id dan interaction_type diperlukan"
            }
        ),
        OpenApiExample(
            'Respons Tidak Ditemukan',
            summary='Kursus tidak ditemukan',
            description='Kursus dengan ID yang diberikan tidak ditemukan',
            value={
                "error": "Kursus tidak ditemukan"
            }
        )
    ]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_course_interaction_view(request):
    """
    Melacak interaksi pengguna dengan kursus
    """
    try:
        course_id = request.data.get('course_id')
        interaction_type = request.data.get('interaction_type')
        
        if not course_id or not interaction_type:
            return Response({
                'error': 'course_id dan interaction_type diperlukan'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        course = get_object_or_404(Course, id=course_id)
        
        # Data tambahan untuk interaksi
        rating = request.data.get('rating')
        time_spent = request.data.get('time_spent', 0)
        
        interaction_data = {}
        if rating:
            interaction_data['rating'] = rating
        if time_spent:
            interaction_data['time_spent'] = time_spent
        
        interaction = recommendation_service.track_user_interaction(
            request.user, course, interaction_type, **interaction_data
        )
        
        if interaction:
            serializer = UserCourseInteractionSerializer(interaction)
            return Response({
                'message': 'Interaksi berhasil dilacak',
                'interaction': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Gagal melacak interaksi'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({
            'error': f'Gagal melacak interaksi: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecommendationSettingsView(generics.RetrieveUpdateAPIView):
    """
    View untuk mengambil dan memperbarui pengaturan rekomendasi
    
    Memungkinkan administrator untuk melihat dan memperbarui pengaturan rekomendasi di seluruh sistem.
    """
    
    serializer_class = RecommendationSettingsSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Dapatkan pengaturan rekomendasi",
        description="Mengembalikan pengaturan rekomendasi di seluruh sistem saat ini.",
        responses={200: RecommendationSettingsSerializer},
        examples=[
            OpenApiExample(
                'Respons Pengaturan',
                summary='Respons berhasil',
                description='Pengaturan rekomendasi saat ini',
                value={
                    "id": 1,
                    "default_algorithm": "hybrid",
                    "max_recommendations_per_user": 10,
                    "recommendation_expiry_days": 7,
                    "auto_refresh_enabled": True,
                    "refresh_interval_hours": 24,
                    "exclude_completed_courses": True,
                    "exclude_enrolled_courses": True,
                    "created_at": "2023-06-01T09:00:00Z",
                    "updated_at": "2023-06-15T10:30:00Z"
                }
            )
        ]
    )
    def get_object(self) -> RecommendationSettings:  # type: ignore[override]
        # Dapatkan atau buat objek pengaturan singleton
        settings_obj, created = RecommendationSettings.objects.get_or_create(
            id=1,
            defaults={
                'default_algorithm': 'hybrid',
                'max_recommendations_per_user': 10,
                'recommendation_expiry_days': 7,
                'auto_refresh_enabled': True,
                'refresh_interval_hours': 24,
                'exclude_completed_courses': True,
                'exclude_enrolled_courses': True
            }
        )
        return settings_obj
    
    @extend_schema(
        summary="Perbarui pengaturan rekomendasi",
        description="Memperbarui pengaturan rekomendasi di seluruh sistem.",
        request=RecommendationSettingsSerializer,
        responses={200: RecommendationSettingsSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        summary="Perbarui sebagian pengaturan rekomendasi",
        description="Memperbarui sebagian pengaturan rekomendasi di seluruh sistem.",
        request=RecommendationSettingsSerializer,
        responses={200: RecommendationSettingsSerializer}
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)