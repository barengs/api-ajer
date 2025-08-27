from rest_framework import permissions
from typing import Any, Union


class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Permission that allows only instructors to create/edit courses,
    but allows everyone to read.
    """
    
    def has_permission(self, request: Any, view: Any) -> bool:  # type: ignore[override]
        if request.method in permissions.SAFE_METHODS:
            return True
        return (request.user.is_authenticated and 
                request.user.role == 'instructor' and
                request.user.verification_status == 'verified')

    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:  # type: ignore[override]
        if request.method in permissions.SAFE_METHODS:
            return True
        return (request.user.is_authenticated and 
                obj.instructor == request.user)


class IsEnrolledOrInstructor(permissions.BasePermission):
    """
    Permission that allows access only to enrolled students or the course instructor.
    """
    
    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:  # type: ignore[override]
        if not request.user.is_authenticated:
            return False
        
        # Instructor has full access to their courses
        if obj.instructor == request.user:
            return True
        
        # Check if user is enrolled in the course
        from courses.models import Enrollment
        return Enrollment.objects.filter(
            student=request.user,
            course=obj,
            is_active=True
        ).exists()


class IsStudentOrInstructor(permissions.BasePermission):
    """
    Permission for students and instructors only (excludes guests).
    """
    
    def has_permission(self, request: Any, view: Any) -> bool:  # type: ignore[override]
        return (request.user.is_authenticated and 
                request.user.role in ['student', 'instructor'])


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission that allows only owners of an object to edit it.
    """
    
    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:  # type: ignore[override]
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if object has 'user' or 'student' or 'author' attribute
        owner_fields = ['user', 'student', 'author', 'created_by']
        for field in owner_fields:
            if hasattr(obj, field):
                return getattr(obj, field) == request.user
        
        return False


class IsInstructor(permissions.BasePermission):
    """
    Permission for instructor users only.
    """
    
    def has_permission(self, request: Any, view: Any) -> bool:  # type: ignore[override]
        return (request.user.is_authenticated and 
                request.user.role == 'instructor')


class IsStudent(permissions.BasePermission):
    """
    Permission for student users only.
    """
    
    def has_permission(self, request: Any, view: Any) -> bool:  # type: ignore[override]
        return (request.user.is_authenticated and 
                request.user.role == 'student')


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission for admin users only for write operations.
    """
    
    def has_permission(self, request: Any, view: Any) -> bool:  # type: ignore[override]
        if request.method in permissions.SAFE_METHODS:
            return True
        return (request.user.is_authenticated and 
                request.user.role == 'admin')


class IsInstructorOfCourse(permissions.BasePermission):
    """
    Permission that checks if user is the instructor of a specific course.
    """
    
    def has_permission(self, request: Any, view: Any) -> bool:  # type: ignore[override]
        if not request.user.is_authenticated:
            return False
        
        # Get course from URL parameters
        course_id = view.kwargs.get('course_id')
        if not course_id:
            return False
        
        from courses.models import Course
        try:
            course = Course.objects.get(id=course_id)
            return course.instructor == request.user
        except Course.DoesNotExist:
            return False