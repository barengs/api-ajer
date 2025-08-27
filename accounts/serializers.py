from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.templatetags.static import static
from .models import User, UserProfile


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer"""
    username_field = User.USERNAME_FIELD
    
    email = serializers.EmailField()

    def get_fields(self):
        fields = super().get_fields()
        # Remove username field since we're using email
        if 'username' in fields:
            del fields['username']
        return fields

    def validate(self, attrs):
        # Use email instead of username
        attrs['username'] = attrs['email']
        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['role'] = user.role
        token['full_name'] = user.full_name or user.username
        
        # Add profile image URL if available
        if user.profile_image:
            # For development, we need to handle the media URL properly
            token['profile_image'] = user.profile_image.url
        else:
            # Provide a default profile image
            token['profile_image'] = static('images/default-profile.png')
        
        return token


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'username', 'password', 'password_confirm',
            'full_name', 'role'
        )
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken")
        return value

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'full_name', 'role', 
            'bio', 'profile_image', 'birth_date', 'phone', 
            'country', 'city', 'is_email_verified', 
            'verification_status', 'date_joined', 'last_login'
        )
        read_only_fields = ('id', 'email', 'role', 'verification_status', 'date_joined', 'last_login')

    def update(self, instance, validated_data):
        # Handle profile image upload
        if 'profile_image' in validated_data:
            # Delete old image if exists
            if instance.profile_image:
                instance.profile_image.delete(save=False)
        
        return super().update(instance, validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """Extended user profile serializer"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            'user_email', 'user_full_name', 'website', 'linkedin', 
            'twitter', 'github', 'education', 'experience', 
            'skills', 'interests', 'profile_visibility'
        )


class ChangePasswordSerializer(serializers.Serializer):
    """Change password serializer"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs


class InstructorApplicationSerializer(serializers.Serializer):
    """Instructor application serializer"""
    instructor_bio = serializers.CharField(max_length=1000)
    expertise_areas = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=1
    )


class UserListSerializer(serializers.ModelSerializer):
    """Simplified user serializer for listings"""
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'full_name', 'profile_image', 
            'role', 'verification_status', 'date_joined'
        )
        read_only_fields = fields