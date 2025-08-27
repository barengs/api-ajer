from rest_framework import serializers
from .models import Notification, NotificationPreference, EmailTemplate
from accounts.models import User


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'user',
            'title',
            'message',
            'notification_type',
            'priority',
            'is_read',
            'is_archived',
            'created_at',
            'read_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for NotificationPreference model"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'email_notifications',
            'email_course_updates',
            'email_assignments',
            'email_forum_activity',
            'email_payments',
            'in_app_notifications',
            'in_app_course_updates',
            'in_app_assignments',
            'in_app_forum_activity',
            'in_app_payments',
            'push_notifications',
            'push_course_updates',
            'push_assignments',
            'push_forum_activity',
            'push_payments',
            'updated_at'
        ]
        read_only_fields = ['updated_at']


class EmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplate model"""
    
    class Meta:
        model = EmailTemplate
        fields = [
            'id',
            'name',
            'template_type',
            'subject',
            'body',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications"""
    
    class Meta:
        model = Notification
        fields = [
            'title',
            'message',
            'notification_type',
            'priority',
            'related_object_id',
            'related_content_type'
        ]


class NotificationBulkReadSerializer(serializers.Serializer):
    """Serializer for marking multiple notifications as read"""
    
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text="List of notification IDs to mark as read"
    )