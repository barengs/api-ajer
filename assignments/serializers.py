from rest_framework import serializers
from django.utils import timezone
from .models import (
    Assignment, AssignmentSubmission, AssignmentFile, AssignmentGroup,
    AssignmentGroupMember, AssignmentRubric, RubricCriterion, RubricLevel,
    RubricGrade, PeerReview, PeerReviewAssignment, PeerReviewSubmission
)


class AssignmentSerializer(serializers.ModelSerializer):
    """Assignment list serializer"""
    instructor_name = serializers.CharField(source='course.instructor.full_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    submission_count = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()
    time_remaining = serializers.SerializerMethodField()
    user_submission = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = (
            'id', 'title', 'description', 'assignment_type', 'grading_type',
            'max_points', 'assigned_date', 'due_date', 'late_submission_allowed',
            'instructor_name', 'course_title', 'submission_count', 'is_overdue',
            'time_remaining', 'is_published', 'user_submission', 'created_at'
        )
    
    def get_submission_count(self, obj):
        return obj.submissions.count()
    
    def get_time_remaining(self, obj):
        if obj.time_remaining:
            total_seconds = int(obj.time_remaining.total_seconds())
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60
            return {
                'days': days,
                'hours': hours,
                'minutes': minutes,
                'total_seconds': total_seconds
            }
        return None
    
    def get_user_submission(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            submission = obj.submissions.get(student=request.user)
            return {
                'id': submission.id,
                'status': submission.status,
                'submitted_at': submission.submitted_at,
                'grade': float(submission.grade) if submission.grade else None,
                'is_late': submission.is_late
            }
        except AssignmentSubmission.DoesNotExist:
            return None


class AssignmentDetailSerializer(serializers.ModelSerializer):
    """Detailed assignment serializer"""
    instructor_name = serializers.CharField(source='course.instructor.full_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    batch_name = serializers.CharField(source='batch.name', read_only=True)
    submission_count = serializers.SerializerMethodField()
    graded_count = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()
    time_remaining = serializers.SerializerMethodField()
    can_submit = serializers.ReadOnlyField()
    user_submission = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = (
            'id', 'title', 'description', 'instructions', 'assignment_type',
            'grading_type', 'max_points', 'assigned_date', 'due_date',
            'late_submission_allowed', 'late_penalty_percentage',
            'allow_file_uploads', 'allowed_file_types', 'max_file_size_mb',
            'max_files_count', 'allow_text_submission', 'allow_url_submission',
            'max_group_size', 'allow_self_selection', 'instructor_name',
            'course_title', 'batch_name', 'submission_count', 'graded_count',
            'is_overdue', 'time_remaining', 'can_submit', 'is_published',
            'user_submission', 'created_at', 'updated_at'
        )
    
    def get_submission_count(self, obj):
        return obj.get_submission_count()
    
    def get_graded_count(self, obj):
        return obj.get_graded_count()
    
    def get_time_remaining(self, obj):
        if obj.time_remaining:
            total_seconds = int(obj.time_remaining.total_seconds())
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60
            return {
                'days': days,
                'hours': hours,
                'minutes': minutes,
                'total_seconds': total_seconds
            }
        return None
    
    def get_user_submission(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            submission = obj.submissions.get(student=request.user)
            return AssignmentSubmissionDetailSerializer(submission).data
        except AssignmentSubmission.DoesNotExist:
            return None


class AssignmentCreateSerializer(serializers.ModelSerializer):
    """Assignment creation serializer"""
    
    class Meta:
        model = Assignment
        fields = (
            'course', 'batch', 'title', 'description', 'instructions',
            'assignment_type', 'grading_type', 'max_points', 'due_date',
            'late_submission_allowed', 'late_penalty_percentage',
            'allow_file_uploads', 'allowed_file_types', 'max_file_size_mb',
            'max_files_count', 'allow_text_submission', 'allow_url_submission',
            'max_group_size', 'allow_self_selection'
        )
    
    def validate_course(self, value):
        # Ensure instructor owns the course
        request = self.context.get('request')
        if request and request.user != value.instructor:
            raise serializers.ValidationError("You can only create assignments for your own courses")
        return value
    
    def validate_due_date(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Due date must be in the future")
        return value


class AssignmentFileSerializer(serializers.ModelSerializer):
    """Assignment file serializer"""
    
    class Meta:
        model = AssignmentFile
        fields = (
            'id', 'file', 'original_filename', 'file_size_bytes',
            'content_type', 'uploaded_at'
        )
        read_only_fields = ('file_size_bytes', 'content_type', 'uploaded_at')


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    """Assignment submission list serializer"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    final_grade = serializers.ReadOnlyField()
    
    class Meta:
        model = AssignmentSubmission
        fields = (
            'id', 'student_name', 'assignment_title', 'status', 'is_late',
            'grade', 'final_grade', 'letter_grade', 'submitted_at',
            'graded_at', 'created_at'
        )


class AssignmentSubmissionDetailSerializer(serializers.ModelSerializer):
    """Detailed assignment submission serializer"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    graded_by_name = serializers.CharField(source='graded_by.full_name', read_only=True)
    files = AssignmentFileSerializer(many=True, read_only=True)
    final_grade = serializers.ReadOnlyField()
    
    class Meta:
        model = AssignmentSubmission
        fields = (
            'id', 'student_name', 'assignment_title', 'text_submission',
            'url_submission', 'status', 'is_late', 'grade', 'final_grade',
            'letter_grade', 'graded_by_name', 'instructor_feedback',
            'files', 'submitted_at', 'graded_at', 'created_at', 'last_modified_at'
        )


class AssignmentSubmissionCreateSerializer(serializers.ModelSerializer):
    """Assignment submission creation serializer"""
    uploaded_files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = AssignmentSubmission
        fields = (
            'text_submission', 'url_submission', 'uploaded_files'
        )
    
    def create(self, validated_data):
        uploaded_files = validated_data.pop('uploaded_files', [])
        assignment = self.context['assignment']
        student = self.context['request'].user
        
        # Check if submission already exists
        existing_submission = AssignmentSubmission.objects.filter(
            assignment=assignment,
            student=student
        ).first()
        
        if existing_submission:
            if existing_submission.status == AssignmentSubmission.SubmissionStatus.SUBMITTED:
                raise serializers.ValidationError("Assignment already submitted")
            submission = existing_submission
            # Update existing submission
            for attr, value in validated_data.items():
                setattr(submission, attr, value)
            submission.save()
        else:
            submission = AssignmentSubmission.objects.create(
                assignment=assignment,
                student=student,
                **validated_data
            )
        
        # Handle file uploads
        for uploaded_file in uploaded_files:
            AssignmentFile.objects.create(
                submission=submission,
                file=uploaded_file,
                original_filename=uploaded_file.name,
                file_size_bytes=uploaded_file.size,
                content_type=uploaded_file.content_type or 'application/octet-stream'
            )
        
        return submission


class AssignmentGradeSerializer(serializers.ModelSerializer):
    """Assignment grading serializer"""
    
    class Meta:
        model = AssignmentSubmission
        fields = (
            'grade', 'letter_grade', 'instructor_feedback', 'private_notes'
        )
    
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        
        # Update status and graded timestamp
        if instance.grade is not None:
            instance.status = AssignmentSubmission.SubmissionStatus.GRADED
            instance.graded_at = timezone.now()
            instance.graded_by = self.context['request'].user
            instance.save(update_fields=['status', 'graded_at', 'graded_by'])
        
        return instance


class AssignmentGroupSerializer(serializers.ModelSerializer):
    """Assignment group serializer"""
    leader_name = serializers.CharField(source='leader.full_name', read_only=True)
    member_count = serializers.ReadOnlyField()
    members = serializers.SerializerMethodField()
    
    class Meta:
        model = AssignmentGroup
        fields = (
            'id', 'name', 'description', 'leader_name', 'member_count',
            'members', 'created_at'
        )
    
    def get_members(self, obj):
        return [{
            'id': member.student.id,
            'name': member.student.full_name,
            'joined_at': member.joined_at
        } for member in obj.members.all()]


class RubricLevelSerializer(serializers.ModelSerializer):
    """Rubric level serializer"""
    
    class Meta:
        model = RubricLevel
        fields = (
            'id', 'name', 'description', 'points', 'sort_order'
        )


class RubricCriterionSerializer(serializers.ModelSerializer):
    """Rubric criterion serializer"""
    levels = RubricLevelSerializer(many=True, read_only=True)
    
    class Meta:
        model = RubricCriterion
        fields = (
            'id', 'name', 'description', 'points', 'sort_order', 'levels'
        )


class AssignmentRubricSerializer(serializers.ModelSerializer):
    """Assignment rubric serializer"""
    criteria = RubricCriterionSerializer(many=True, read_only=True)
    total_points = serializers.ReadOnlyField()
    
    class Meta:
        model = AssignmentRubric
        fields = (
            'id', 'title', 'description', 'criteria', 'total_points',
            'created_at', 'updated_at'
        )


class RubricGradeSerializer(serializers.ModelSerializer):
    """Rubric grading serializer"""
    criterion_name = serializers.CharField(source='criterion.name', read_only=True)
    level_name = serializers.CharField(source='level.name', read_only=True)
    
    class Meta:
        model = RubricGrade
        fields = (
            'id', 'criterion', 'level', 'criterion_name', 'level_name',
            'points_earned', 'comments', 'graded_at'
        )


class PeerReviewSerializer(serializers.ModelSerializer):
    """Peer review configuration serializer"""
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    
    class Meta:
        model = PeerReview
        fields = (
            'id', 'assignment_title', 'reviews_per_submission',
            'reviewer_anonymity', 'review_start_date', 'review_end_date',
            'review_instructions', 'review_criteria', 'created_at'
        )


class PeerReviewSubmissionSerializer(serializers.ModelSerializer):
    """Peer review submission serializer"""
    reviewer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PeerReviewSubmission
        fields = (
            'id', 'overall_rating', 'criteria_scores', 'written_feedback',
            'suggestions', 'reviewer_name', 'is_approved', 'submitted_at'
        )
    
    def get_reviewer_name(self, obj):
        if obj.review_assignment.peer_review.reviewer_anonymity:
            return "Anonymous Reviewer"
        return obj.review_assignment.reviewer.full_name