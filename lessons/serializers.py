from rest_framework import serializers
from .models import (
    Section, Lesson, LessonProgress, Quiz, QuizQuestion, QuizAttempt, 
    QuizAnswer, LessonComment, LessonNote
)


class LessonSerializer(serializers.ModelSerializer):
    """Basic lesson serializer"""
    can_access = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = (
            'id', 'title', 'slug', 'description', 'lesson_type', 
            'duration_minutes', 'sort_order', 'is_preview', 
            'is_mandatory', 'status', 'can_access', 'created_at'
        )
    
    def get_can_access(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return obj.is_preview
        return obj.can_be_accessed_by_user(request.user)


class LessonDetailSerializer(serializers.ModelSerializer):
    """Detailed lesson serializer with content"""
    can_access = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = (
            'id', 'title', 'slug', 'description', 'lesson_type', 
            'content', 'video_file', 'video_url', 'audio_file',
            'downloadable_resources', 'duration_minutes', 'sort_order',
            'is_preview', 'is_mandatory', 'status', 'can_access',
            'user_progress', 'created_at', 'updated_at'
        )
    
    def get_can_access(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return obj.is_preview
        return obj.can_be_accessed_by_user(request.user)
    
    def get_user_progress(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            progress = LessonProgress.objects.get(student=request.user, lesson=obj)
            return {
                'is_completed': progress.is_completed,
                'completion_percentage': float(progress.completion_percentage),
                'time_spent_minutes': progress.time_spent_minutes,
                'last_accessed_at': progress.last_accessed_at
            }
        except LessonProgress.DoesNotExist:
            return None


class SectionSerializer(serializers.ModelSerializer):
    """Course section serializer"""
    lessons = LessonSerializer(many=True, read_only=True)
    total_lessons = serializers.ReadOnlyField()
    total_duration = serializers.ReadOnlyField()
    
    class Meta:
        model = Section
        fields = (
            'id', 'title', 'description', 'sort_order', 
            'lessons', 'total_lessons', 'total_duration',
            'created_at'
        )


class LessonProgressSerializer(serializers.ModelSerializer):
    """Lesson progress tracking serializer"""
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = (
            'id', 'lesson_title', 'is_completed', 'completion_percentage',
            'time_spent_minutes', 'video_progress_seconds', 'video_duration_seconds',
            'first_accessed_at', 'last_accessed_at', 'completed_at'
        )


class QuizQuestionSerializer(serializers.ModelSerializer):
    """Quiz question serializer"""
    
    class Meta:
        model = QuizQuestion
        fields = (
            'id', 'question_text', 'question_type', 'points', 
            'sort_order', 'options', 'explanation'
        )
        # Don't expose correct_answer in serialization
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Only show correct answers after quiz completion or for instructors
        if request and hasattr(request, 'user'):
            if (request.user.is_authenticated and 
                (request.user == instance.quiz.lesson.section.course.instructor or
                 request.user.role == 'admin')):
                data['correct_answer'] = instance.correct_answer
        
        return data


class QuizSerializer(serializers.ModelSerializer):
    """Quiz serializer"""
    questions = QuizQuestionSerializer(many=True, read_only=True)
    total_questions = serializers.ReadOnlyField()
    user_attempts = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = (
            'id', 'title', 'description', 'time_limit_minutes',
            'max_attempts', 'passing_score', 'show_correct_answers',
            'randomize_questions', 'questions', 'total_questions',
            'user_attempts', 'created_at'
        )
    
    def get_user_attempts(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return []
        
        attempts = obj.attempts.filter(student=request.user)
        return [{
            'attempt_number': attempt.attempt_number,
            'status': attempt.status,
            'percentage_score': float(attempt.percentage_score),
            'is_passed': attempt.is_passed,
            'started_at': attempt.started_at,
            'completed_at': attempt.completed_at
        } for attempt in attempts]


class QuizAttemptSerializer(serializers.ModelSerializer):
    """Quiz attempt serializer"""
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = (
            'id', 'quiz_title', 'attempt_number', 'status',
            'total_questions', 'correct_answers', 'total_points',
            'earned_points', 'percentage_score', 'is_passed',
            'started_at', 'completed_at', 'time_spent_seconds'
        )


class QuizAnswerSerializer(serializers.ModelSerializer):
    """Quiz answer submission serializer"""
    
    class Meta:
        model = QuizAnswer
        fields = (
            'question', 'answer_text', 'selected_options'
        )
        
    def create(self, validated_data):
        # Add attempt from context
        validated_data['attempt'] = self.context['attempt']
        return super().create(validated_data)


class LessonCommentSerializer(serializers.ModelSerializer):
    """Lesson comment serializer"""
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LessonComment
        fields = (
            'id', 'content', 'user_name', 'user_role', 'parent',
            'is_instructor_reply', 'replies_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('user_name', 'user_role', 'is_instructor_reply')
    
    def get_replies_count(self, obj):
        return obj.replies.filter(is_approved=True).count()


class LessonNoteSerializer(serializers.ModelSerializer):
    """Student lesson notes serializer"""
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = LessonNote
        fields = (
            'id', 'lesson_title', 'title', 'content', 
            'timestamp_seconds', 'created_at', 'updated_at'
        )
        read_only_fields = ('lesson_title',)


class LessonCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating lessons (instructors only)"""
    
    class Meta:
        model = Lesson
        fields = (
            'section', 'title', 'description', 'lesson_type', 'content',
            'video_file', 'video_url', 'audio_file', 'downloadable_resources',
            'duration_minutes', 'sort_order', 'is_preview', 'is_mandatory'
        )
    
    def validate_section(self, value):
        # Ensure instructor owns the course
        request = self.context.get('request')
        if request and request.user != value.course.instructor:
            raise serializers.ValidationError("You can only add lessons to your own courses")
        return value