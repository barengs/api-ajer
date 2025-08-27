from rest_framework import serializers
from .models import Course, Category, Enrollment, CourseReview, CourseBatch


class CategorySerializer(serializers.ModelSerializer):
    """Course category serializer"""
    course_count = serializers.ReadOnlyField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'icon', 'course_count')


class CourseListSerializer(serializers.ModelSerializer):
    """Course list serializer (for browse/search)"""
    instructor_name = serializers.CharField(source='instructor.full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.ReadOnlyField()
    total_reviews = serializers.ReadOnlyField()

    class Meta:
        model = Course
        fields = (
            'id', 'title', 'slug', 'short_description', 'instructor_name',
            'category_name', 'course_type', 'difficulty_level', 'thumbnail',
            'price', 'is_free', 'average_rating', 'total_reviews',
            'total_enrollments', 'total_duration_minutes', 'created_at'
        )


class CourseDetailSerializer(serializers.ModelSerializer):
    """Detailed course serializer"""
    instructor = serializers.StringRelatedField(read_only=True)
    category = CategorySerializer(read_only=True)
    average_rating = serializers.ReadOnlyField()
    total_reviews = serializers.ReadOnlyField()
    
    class Meta:
        model = Course
        fields = (
            'id', 'title', 'slug', 'description', 'short_description',
            'instructor', 'category', 'course_type', 'difficulty_level',
            'thumbnail', 'preview_video', 'price', 'original_price', 'is_free',
            'learning_objectives', 'prerequisites', 'target_audience',
            'average_rating', 'total_reviews', 'total_enrollments',
            'total_duration_minutes', 'total_lessons', 'created_at',
            'updated_at'
        )


class CourseCreateSerializer(serializers.ModelSerializer):
    """Course creation serializer"""
    
    class Meta:
        model = Course
        fields = (
            'title', 'description', 'short_description', 'category',
            'course_type', 'difficulty_level', 'thumbnail', 'preview_video',
            'price', 'is_free', 'learning_objectives', 'prerequisites',
            'target_audience', 'meta_title', 'meta_description'
        )

    def create(self, validated_data):
        # Set instructor to current user
        validated_data['instructor'] = self.context['request'].user
        return super().create(validated_data)


class CourseBatchSerializer(serializers.ModelSerializer):
    """Course batch serializer for structured courses"""
    
    class Meta:
        model = CourseBatch
        fields = (
            'id', 'name', 'description', 'start_date', 'end_date',
            'enrollment_start', 'enrollment_end', 'max_students',
            'current_enrollments', 'price', 'status', 'available_spots',
            'is_enrollment_open'
        )


class EnrollmentSerializer(serializers.ModelSerializer):
    """Course enrollment serializer"""
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_thumbnail = serializers.ImageField(source='course.thumbnail', read_only=True)
    instructor_name = serializers.CharField(source='course.instructor.full_name', read_only=True)

    class Meta:
        model = Enrollment
        fields = (
            'id', 'course_title', 'course_thumbnail', 'instructor_name',
            'status', 'progress_percentage', 'enrolled_at', 'last_accessed_at',
            'completed_at'
        )


class CourseReviewSerializer(serializers.ModelSerializer):
    """Course review serializer"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = CourseReview
        fields = (
            'id', 'student_name', 'rating', 'title', 'comment',
            'is_approved', 'created_at', 'updated_at'
        )
        read_only_fields = ('student_name', 'is_approved', 'created_at', 'updated_at')

    def create(self, validated_data):
        # Set student to current user
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)