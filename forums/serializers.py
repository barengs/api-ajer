from rest_framework import serializers
from .models import (
    Forum, ForumPost, ForumReply, ForumVote, ForumSubscription,
    ForumReportedContent, ForumActivity
)
from accounts.models import User


class ForumSerializer(serializers.ModelSerializer):
    """Forum list serializer"""
    course_title = serializers.CharField(source='course.title', read_only=True)
    batch_name = serializers.CharField(source='batch.name', read_only=True)
    total_posts = serializers.ReadOnlyField()
    latest_post = serializers.SerializerMethodField()
    
    class Meta:
        model = Forum
        fields = (
            'id', 'name', 'description', 'forum_type', 'course_title',
            'batch_name', 'allow_student_posts', 'require_moderation',
            'is_private', 'total_posts', 'latest_post', 'is_active',
            'is_locked', 'created_at'
        )
    
    def get_latest_post(self, obj):
        latest = obj.latest_post
        if latest:
            return {
                'id': latest.id,
                'title': latest.title,
                'author': latest.author.full_name or latest.author.username,
                'created_at': latest.created_at,
                'reply_count': latest.reply_count
            }
        return None


class ForumPostSerializer(serializers.ModelSerializer):
    """Forum post list serializer"""
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    author_role = serializers.CharField(source='author.role', read_only=True)
    forum_name = serializers.CharField(source='forum.name', read_only=True)
    reply_count = serializers.ReadOnlyField()
    latest_reply = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    
    class Meta:
        model = ForumPost
        fields = (
            'id', 'title', 'content', 'post_type', 'author_name', 'author_role',
            'forum_name', 'is_question_resolved', 'is_pinned', 'is_locked',
            'upvotes', 'downvotes', 'view_count', 'reply_count', 'tags',
            'latest_reply', 'user_vote', 'is_subscribed', 'created_at',
            'updated_at', 'last_activity_at'
        )
        read_only_fields = ('author_name', 'author_role', 'forum_name')
    
    def get_latest_reply(self, obj):
        latest = obj.latest_reply
        if latest:
            return {
                'id': latest.id,
                'author': latest.author.full_name or latest.author.username,
                'author_role': latest.author.role,
                'is_instructor_reply': latest.is_instructor_reply,
                'created_at': latest.created_at
            }
        return None
    
    def get_user_vote(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            vote = obj.votes.get(user=request.user)
            return vote.vote_type
        except ForumVote.DoesNotExist:
            return None
    
    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return obj.subscribers.filter(user=request.user).exists()


class ForumPostDetailSerializer(serializers.ModelSerializer):
    """Detailed forum post serializer"""
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    author_role = serializers.CharField(source='author.role', read_only=True)
    author_profile_image = serializers.ImageField(source='author.profile_image', read_only=True)
    forum_name = serializers.CharField(source='forum.name', read_only=True)
    reply_count = serializers.ReadOnlyField()
    user_vote = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = ForumPost
        fields = (
            'id', 'title', 'content', 'post_type', 'author_name', 'author_role',
            'author_profile_image', 'forum_name', 'is_question_resolved',
            'accepted_answer', 'is_pinned', 'is_locked', 'upvotes', 'downvotes',
            'view_count', 'reply_count', 'tags', 'user_vote', 'is_subscribed',
            'can_edit', 'created_at', 'updated_at', 'last_activity_at'
        )
    
    def get_user_vote(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            vote = obj.votes.get(user=request.user)
            return vote.vote_type
        except ForumVote.DoesNotExist:
            return None
    
    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return obj.subscribers.filter(user=request.user).exists()
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return (obj.author == request.user or 
                obj.forum.course.instructor == request.user or
                request.user.role == 'admin')


class ForumPostCreateSerializer(serializers.ModelSerializer):
    """Forum post creation serializer"""
    
    class Meta:
        model = ForumPost
        fields = (
            'forum', 'title', 'content', 'post_type', 'tags'
        )
    
    def validate_forum(self, value):
        request = self.context.get('request')
        
        # Check if request and user exist
        if not request or not request.user or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication is required")
        
        # Check if user can post in this forum
        if not value.allow_student_posts and request.user.role == 'student':
            raise serializers.ValidationError("Students are not allowed to post in this forum")
        
        # Check if forum is locked
        if value.is_locked:
            raise serializers.ValidationError("This forum is locked")
        
        # Check if user has access to the course
        from courses.models import Enrollment
        if (request.user != value.course.instructor and
            not Enrollment.objects.filter(
                student=request.user,
                course=value.course,
                is_active=True
            ).exists()):
            raise serializers.ValidationError("You don't have access to this course")
        
        return value
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        
        # Set approval status based on moderation settings
        forum = validated_data['forum']
        if forum.require_moderation and self.context['request'].user.role == 'student':
            validated_data['status'] = ForumPost.PostStatus.PENDING
            validated_data['is_approved'] = False
        
        return super().create(validated_data)


class ForumReplySerializer(serializers.ModelSerializer):
    """Forum reply serializer"""
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    author_role = serializers.CharField(source='author.role', read_only=True)
    author_profile_image = serializers.ImageField(source='author.profile_image', read_only=True)
    user_vote = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = ForumReply
        fields = (
            'id', 'content', 'author_name', 'author_role', 'author_profile_image',
            'parent', 'is_instructor_reply', 'is_answer', 'upvotes', 'downvotes',
            'user_vote', 'can_edit', 'replies', 'created_at', 'updated_at'
        )
        read_only_fields = ('author_name', 'author_role', 'is_instructor_reply')
    
    def get_user_vote(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            vote = obj.votes.get(user=request.user)
            return vote.vote_type
        except ForumVote.DoesNotExist:
            return None
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return (obj.author == request.user or 
                obj.post.forum.course.instructor == request.user or
                request.user.role == 'admin')
    
    def get_replies(self, obj):
        if obj.child_replies.exists():
            return ForumReplySerializer(
                obj.child_replies.filter(is_approved=True).order_by('created_at')[:5],
                many=True,
                context=self.context
            ).data
        return []


class ForumReplyCreateSerializer(serializers.ModelSerializer):
    """Forum reply creation serializer"""
    
    class Meta:
        model = ForumReply
        fields = ('content', 'parent')
    
    def validate(self, attrs):
        # Get post from context
        post = self.context.get('post')
        if not post:
            raise serializers.ValidationError("Post context is required")
        
        # Check if post is locked
        if post.is_locked:
            raise serializers.ValidationError("This post is locked")
        
        # Validate parent reply if provided
        parent = attrs.get('parent')
        if parent and parent.post != post:
            raise serializers.ValidationError("Parent reply must belong to the same post")
        
        return attrs
    
    def create(self, validated_data):
        post = self.context['post']
        request = self.context['request']
        
        validated_data['post'] = post
        validated_data['author'] = request.user
        
        # Set approval status based on moderation settings
        if post.forum.require_moderation and request.user.role == 'student':
            validated_data['status'] = ForumReply.ReplyStatus.PENDING
            validated_data['is_approved'] = False
        
        return super().create(validated_data)


class ForumVoteSerializer(serializers.ModelSerializer):
    """Forum vote serializer"""
    
    class Meta:
        model = ForumVote
        fields = ('vote_type',)
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        
        # Set either post or reply from context
        post = self.context.get('post')
        reply = self.context.get('reply')
        
        if post:
            validated_data['post'] = post
        elif reply:
            validated_data['reply'] = reply
        else:
            raise serializers.ValidationError("Either post or reply context is required")
        
        return super().create(validated_data)


class ForumSubscriptionSerializer(serializers.ModelSerializer):
    """Forum subscription serializer"""
    post_title = serializers.CharField(source='post.title', read_only=True)
    
    class Meta:
        model = ForumSubscription
        fields = (
            'id', 'post_title', 'notify_new_replies', 'notify_accepted_answer',
            'created_at'
        )


class ForumReportSerializer(serializers.ModelSerializer):
    """Forum content report serializer"""
    reporter_name = serializers.CharField(source='reporter.username', read_only=True)
    
    class Meta:
        model = ForumReportedContent
        fields = (
            'reason', 'description'
        )
    
    def create(self, validated_data):
        validated_data['reporter'] = self.context['request'].user
        
        # Set either post or reply from context
        post = self.context.get('post')
        reply = self.context.get('reply')
        
        if post:
            validated_data['post'] = post
        elif reply:
            validated_data['reply'] = reply
        else:
            raise serializers.ValidationError("Either post or reply context is required")
        
        return super().create(validated_data)


class ForumActivitySerializer(serializers.ModelSerializer):
    """Forum activity serializer"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    forum_name = serializers.CharField(source='forum.name', read_only=True)
    
    class Meta:
        model = ForumActivity
        fields = (
            'id', 'user_name', 'forum_name', 'activity_type',
            'metadata', 'created_at'
        )
        read_only_fields = fields