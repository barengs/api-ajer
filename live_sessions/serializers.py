from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    LiveSession, SessionAttendance, SessionResource, 
    SessionRecording, SessionChat, SessionPoll, PollResponse
)
from courses.models import Course, CourseBatch

User = get_user_model()


class LiveSessionSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(source='instructor.full_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    batch_name = serializers.CharField(source='batch.name', read_only=True)
    attendee_count = serializers.SerializerMethodField()
    is_upcoming = serializers.ReadOnlyField()
    is_live_now = serializers.ReadOnlyField()
    duration_minutes = serializers.ReadOnlyField()
    
    class Meta:
        model = LiveSession
        fields = [
            'id', 'course', 'batch', 'instructor', 'instructor_name',
            'course_title', 'batch_name', 'title', 'description',
            'scheduled_start', 'scheduled_end', 'actual_start', 'actual_end',
            'platform', 'meeting_url', 'meeting_id', 'meeting_password',
            'max_participants', 'is_recorded', 'recording_url',
            'status', 'attendee_count', 'is_upcoming', 'is_live_now',
            'duration_minutes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'actual_start', 'actual_end', 'created_at', 'updated_at']
    
    def get_attendee_count(self, obj):
        return obj.attendances.count()
    
    def validate(self, attrs):
        if attrs['scheduled_start'] >= attrs['scheduled_end']:
            raise serializers.ValidationError("Start time must be before end time")
        return attrs


class SessionAttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    session_title = serializers.CharField(source='session.title', read_only=True)
    attendance_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = SessionAttendance
        fields = [
            'id', 'session', 'student', 'student_name', 'student_email',
            'session_title', 'status', 'joined_at', 'left_at',
            'total_duration_minutes', 'questions_asked', 'chat_messages',
            'attendance_percentage', 'registered_at'
        ]
        read_only_fields = ['id', 'registered_at']


class SessionResourceSerializer(serializers.ModelSerializer):
    shared_by_name = serializers.CharField(source='shared_by.full_name', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SessionResource
        fields = [
            'id', 'session', 'title', 'description', 'resource_type',
            'file', 'file_url', 'url', 'shared_by', 'shared_by_name',
            'shared_at', 'is_public'
        ]
        read_only_fields = ['id', 'shared_by', 'shared_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class SessionRecordingSerializer(serializers.ModelSerializer):
    session_title = serializers.CharField(source='session.title', read_only=True)
    video_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    is_available = serializers.ReadOnlyField()
    
    class Meta:
        model = SessionRecording
        fields = [
            'id', 'session', 'session_title', 'title', 'duration_minutes',
            'file_size_mb', 'video_file', 'video_url', 'external_url',
            'thumbnail', 'thumbnail_url', 'processing_status',
            'is_public', 'available_until', 'is_available',
            'created_at', 'processed_at'
        ]
        read_only_fields = ['id', 'created_at', 'processed_at']
    
    def get_video_url(self, obj):
        if obj.video_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.video_file.url)
        return obj.external_url
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
        return None


class SessionChatSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    sender_role = serializers.CharField(source='sender.role', read_only=True)
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SessionChat
        fields = [
            'id', 'session', 'sender', 'sender_name', 'sender_role',
            'message', 'message_type', 'parent_message', 'replies_count',
            'is_visible', 'is_highlighted', 'sent_at'
        ]
        read_only_fields = ['id', 'sender', 'sent_at']
    
    def get_replies_count(self, obj):
        return obj.replies.filter(is_visible=True).count()


class SessionPollSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    response_count = serializers.ReadOnlyField()
    results = serializers.SerializerMethodField()
    
    class Meta:
        model = SessionPoll
        fields = [
            'id', 'session', 'created_by', 'created_by_name',
            'question', 'options', 'is_multiple_choice',
            'is_anonymous', 'is_active', 'response_count',
            'results', 'created_at', 'closed_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'closed_at']
    
    def get_results(self, obj):
        if not obj.is_active and obj.closed_at:
            # Calculate poll results
            responses = obj.responses.all()
            results = {}
            for i, option in enumerate(obj.options):
                count = sum(1 for response in responses if i in response.selected_options)
                results[option] = {
                    'count': count,
                    'percentage': (count / len(responses) * 100) if responses else 0
                }
            return results
        return {}


class PollResponseSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    poll_question = serializers.CharField(source='poll.question', read_only=True)
    
    class Meta:
        model = PollResponse
        fields = [
            'id', 'poll', 'student', 'student_name',
            'poll_question', 'selected_options', 'submitted_at'
        ]
        read_only_fields = ['id', 'student', 'submitted_at']
    
    def validate_selected_options(self, value):
        # Get poll from instance or from parent validation context
        poll = None
        if self.instance:
            poll = self.instance.poll
        elif hasattr(self, 'initial_data') and self.initial_data and isinstance(self.initial_data, dict):
            poll_id = self.initial_data.get('poll')
            if poll_id:
                from .models import SessionPoll
                try:
                    poll = SessionPoll.objects.get(id=poll_id)
                except SessionPoll.DoesNotExist:
                    raise serializers.ValidationError("Invalid poll specified")
        
        if poll:
            max_options = len(poll.options)
            for option_index in value:
                if option_index >= max_options or option_index < 0:
                    raise serializers.ValidationError(f"Invalid option index: {option_index}")
        return value


# Create/Update Serializers
class LiveSessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveSession
        fields = [
            'course', 'batch', 'title', 'description',
            'scheduled_start', 'scheduled_end', 'platform',
            'meeting_url', 'meeting_id', 'meeting_password',
            'max_participants', 'is_recorded'
        ]
    
    def validate(self, attrs):
        if attrs['scheduled_start'] >= attrs['scheduled_end']:
            raise serializers.ValidationError("Start time must be before end time")
        
        # Validate course and batch relationship
        if attrs.get('batch') and attrs.get('course'):
            if attrs['batch'].course != attrs['course']:
                raise serializers.ValidationError("Batch does not belong to the specified course")
        
        return attrs
    
    def create(self, validated_data):
        validated_data['instructor'] = self.context['request'].user
        return super().create(validated_data)


class SessionAttendanceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionAttendance
        fields = ['session']
    
    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)


class SessionChatCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionChat
        fields = ['session', 'message', 'message_type', 'parent_message']
    
    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


class SessionPollCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionPoll
        fields = [
            'session', 'question', 'options',
            'is_multiple_choice', 'is_anonymous'
        ]
    
    def validate_options(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Poll must have at least 2 options")
        if len(value) > 10:
            raise serializers.ValidationError("Poll cannot have more than 10 options")
        return value
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)