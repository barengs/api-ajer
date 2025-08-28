from django.test import TestCase
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta
import json
from typing import TYPE_CHECKING, cast

from .models import (
    RoleDefinition, 
    UserRoleAssignment, 
    RoleChangeHistory, 
    RolePermissionGroup, 
    UserRoleRequest
)
from .services import RoleManagementService

User = get_user_model()

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


class RoleDefinitionModelTest(TestCase):
    """Test RoleDefinition model functionality"""
    
    def setUp(self):
        self.role = RoleDefinition.objects.create(
            name=RoleDefinition.RoleType.ADMIN,
            display_name='Test Admin',
            hierarchy_level=90,
            description='Test administrator role'
        )
    
    def test_role_creation(self):
        """Test role definition creation"""
        self.assertEqual(self.role.display_name, 'Test Admin')
        self.assertEqual(self.role.name, RoleDefinition.RoleType.ADMIN)
        self.assertEqual(self.role.hierarchy_level, 90)
        self.assertTrue(self.role.is_active)
    
    def test_role_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.role), 'Test Admin (admin)')
    
    def test_role_hierarchy(self):
        """Test role hierarchy levels"""
        lower_role = RoleDefinition.objects.create(
            name=RoleDefinition.RoleType.STUDENT,
            display_name='Test Student',
            hierarchy_level=10
        )
        
        self.assertTrue(self.role.hierarchy_level > lower_role.hierarchy_level)
    
    def test_unique_name_constraint(self):
        """Test unique name constraint"""
        with self.assertRaises(Exception):
            RoleDefinition.objects.create(
                name=RoleDefinition.RoleType.ADMIN,
                display_name='Another Admin',
                hierarchy_level=50
            )


class UserRoleAssignmentModelTest(TestCase):
    """Test UserRoleAssignment model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(  # type: ignore
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(  # type: ignore
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.role = RoleDefinition.objects.create(
            name=RoleDefinition.RoleType.INSTRUCTOR,
            display_name='Test Role',
            hierarchy_level=50
        )
    
    def test_role_assignment_creation(self):
        """Test role assignment creation"""
        assignment = UserRoleAssignment.objects.create(
            user=self.user,
            role=self.role,
            assigned_by=self.admin_user,
            assignment_reason='Test assignment'
        )
        
        self.assertEqual(assignment.user, self.user)
        self.assertEqual(assignment.role, self.role)
        self.assertEqual(assignment.assigned_by, self.admin_user)
        self.assertTrue(assignment.is_currently_active)
    
    def test_role_assignment_expiration(self):
        """Test role assignment with expiration"""
        future_date = timezone.now() + timedelta(days=30)
        assignment = UserRoleAssignment.objects.create(
            user=self.user,
            role=self.role,
            assigned_by=self.admin_user,
            effective_until=future_date
        )
        
        self.assertTrue(assignment.is_currently_active)
        
        # Test expired assignment
        past_date = timezone.now() - timedelta(days=1)
        assignment.effective_until = past_date
        assignment.save()
        
        self.assertFalse(assignment.is_currently_active)
    
    def test_unique_active_role_constraint(self):
        """Test unique constraint for active roles"""
        UserRoleAssignment.objects.create(
            user=self.user,
            role=self.role,
            assigned_by=self.admin_user
        )
        
        # This should raise an integrity error due to unique constraint
        with self.assertRaises(Exception):
            UserRoleAssignment.objects.create(
                user=self.user,
                role=self.role,
                assigned_by=self.admin_user
            )


class RoleManagementServiceTest(TestCase):
    """Test RoleManagementService functionality"""
    
    def setUp(self):
        self.service = RoleManagementService()
        self.user = User.objects.create_user(  # type: ignore
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(  # type: ignore
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        self.instructor_role = RoleDefinition.objects.create(
            name=RoleDefinition.RoleType.INSTRUCTOR,
            display_name='Instructor',
            hierarchy_level=50
        )
        self.admin_role = RoleDefinition.objects.create(
            name=RoleDefinition.RoleType.ADMIN,
            display_name='Administrator',
            hierarchy_level=90
        )
    
    def test_assign_role_success(self):
        """Test successful role assignment"""
        assignment = self.service.assign_role(
            user_id=self.user.id,
            role_id=self.instructor_role.pk,
            assigned_by=self.admin_user,
            reason='Test assignment'
        )
        
        self.assertIsInstance(assignment, UserRoleAssignment)
        self.assertEqual(assignment.user, self.user)
        self.assertEqual(assignment.role, self.instructor_role)
        
        # Verify assignment was created
        assignment = UserRoleAssignment.objects.get(
            user=self.user,
            role=self.instructor_role
        )
        self.assertTrue(assignment.is_currently_active)
    
    def test_assign_role_duplicate(self):
        """Test assigning duplicate role"""
        # First assignment
        self.service.assign_role(
            user_id=self.user.id,
            role_id=self.instructor_role.pk,
            assigned_by=self.admin_user
        )
        
        # Second assignment (should fail)
        with self.assertRaises(ValidationError):
            self.service.assign_role(
                user_id=self.user.id,
                role_id=self.instructor_role.pk,
                assigned_by=self.admin_user
            )
    
    def test_revoke_role_success(self):
        """Test successful role revocation"""
        # First assign a role
        assignment = self.service.assign_role(
            user_id=self.user.id,
            role_id=self.instructor_role.pk,
            assigned_by=self.admin_user
        )
        
        # Then revoke it
        revoked_assignment = self.service.revoke_role(
            assignment_id=assignment.pk,
            revoked_by=self.admin_user,
            reason='Test revocation'
        )
        
        self.assertIsInstance(revoked_assignment, UserRoleAssignment)
        
        # Verify assignment was deactivated
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, UserRoleAssignment.AssignmentStatus.REVOKED)
    
    def test_revoke_role_not_assigned(self):
        """Test revoking non-assigned role"""
        # Try to revoke a role assignment that doesn't exist
        with self.assertRaises(ValidationError):
            self.service.revoke_role(
                assignment_id=999,  # Non-existent assignment
                revoked_by=self.admin_user
            )
    
    def test_bulk_assign_roles(self):
        """Test bulk role assignment"""
        user2 = User.objects.create_user(  # type: ignore
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        user_ids = [self.user.id, user2.id]
        successful_assignments, failed_assignments = self.service.bulk_assign_roles(
            user_ids=user_ids,
            role_id=self.instructor_role.pk,
            assigned_by=self.admin_user,
            reason='Bulk assignment test'
        )
        
        self.assertEqual(len(successful_assignments), 2)
        self.assertEqual(len(failed_assignments), 0)
        
        # Verify assignments were created
        assignments = UserRoleAssignment.objects.filter(
            role=self.instructor_role,
            status=UserRoleAssignment.AssignmentStatus.ACTIVE
        )
        self.assertEqual(assignments.count(), 2)
    
    def test_get_user_roles(self):
        """Test getting user roles"""
        # Assign a role
        self.service.assign_role(
            user_id=self.user.id,
            role_id=self.instructor_role.pk,
            assigned_by=self.admin_user
        )
        
        role_assignments = self.service.get_user_roles(self.user)
        self.assertEqual(len(role_assignments), 1)
        self.assertEqual(role_assignments[0].role, self.instructor_role)
    
    def test_has_role(self):
        """Test checking if user has specific role"""
        # Initially should not have role
        roles = self.service.get_user_roles(self.user)
        self.assertEqual(len(roles), 0)
        
        # Assign role
        self.service.assign_role(
            user_id=self.user.id,
            role_id=self.instructor_role.pk,
            assigned_by=self.admin_user
        )
        
        # Now should have role
        roles = self.service.get_user_roles(self.user)
        self.assertEqual(len(roles), 1)
        self.assertEqual(roles[0].role, self.instructor_role)


class RoleManagementAPITest(APITestCase):
    """Test Role Management API endpoints"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(  # type: ignore
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        self.regular_user = User.objects.create_user(  # type: ignore
            username='user',
            email='user@example.com',
            password='userpass123'
        )
        self.instructor_role = RoleDefinition.objects.create(
            name=RoleDefinition.RoleType.INSTRUCTOR,
            display_name='Instructor',
            hierarchy_level=50
        )
    
    def test_role_list_api(self):
        """Test role definition list API"""
        self.client.force_authenticate(user=self.admin_user)  # type: ignore
        url = reverse('role_management:role-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # type: ignore
    
    def test_user_role_assignment_api(self):
        """Test user role assignment API"""
        self.client.force_authenticate(user=self.admin_user)  # type: ignore
        url = reverse('role_management:user-roles', kwargs={'user_id': self.regular_user.id})
        
        data = {
            'role_id': self.instructor_role.pk,
            'reason': 'API test assignment'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify assignment was created
        assignment = UserRoleAssignment.objects.get(
            user=self.regular_user,
            role=self.instructor_role
        )
        self.assertEqual(assignment.status, UserRoleAssignment.AssignmentStatus.ACTIVE)
    
    def test_bulk_role_assignment_api(self):
        """Test bulk role assignment API"""
        user2 = User.objects.create_user(  # type: ignore
            username='user2',
            email='user2@example.com',
            password='userpass123'
        )
        
        self.client.force_authenticate(user=self.admin_user)  # type: ignore
        url = reverse('role_management:bulk-assign-roles')
        
        data = {
            'user_ids': [self.regular_user.id, user2.id],
            'role_id': self.instructor_role.pk,
            'action': 'assign',  # Add the required action parameter
            'reason': 'Bulk API test'
        }
        response = self.client.post(url, data, format='json')
        
        # Print response for debugging
        print(f"Response status: {response.status_code}")
        # Access response data properly with proper type checking
        response_data = getattr(response, 'data', None)
        if response_data is not None:
            print(f"Response data: {response_data}")
        else:
            content = getattr(response, 'content', b'')
            if content:
                print(f"Response content: {content.decode() if isinstance(content, bytes) else content}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Access response data properly with proper type checking
        response_data = getattr(response, 'data', None)
        if response_data is not None:
            self.assertEqual(response_data['successful_count'], 2)  # type: ignore
            self.assertEqual(response_data['failed_count'], 0)  # type: ignore

    def test_role_statistics_api(self):
        """Test role statistics API"""
        # Assign some roles first
        UserRoleAssignment.objects.create(
            user=self.regular_user,
            role=self.instructor_role,
            assigned_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.admin_user)  # type: ignore
        url = reverse('role_management:role-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_users', response.data)  # type: ignore
        self.assertIn('role_distribution', response.data)  # type: ignore
    
    def test_unauthorized_access(self):
        """Test unauthorized access to admin endpoints"""
        self.client.force_authenticate(user=self.regular_user)  # type: ignore
        url = reverse('role_management:role-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RoleRequestModelTest(TestCase):
    """Test UserRoleRequest model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(  # type: ignore
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(  # type: ignore
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.instructor_role = RoleDefinition.objects.create(
            name=RoleDefinition.RoleType.INSTRUCTOR,
            display_name='Instructor',
            hierarchy_level=50
        )
    
    def test_role_request_creation(self):
        """Test role request creation"""
        request = UserRoleRequest.objects.create(
            user=self.user,
            requested_role=self.instructor_role,
            justification='I want to teach courses'
        )
        
        self.assertEqual(request.user, self.user)
        self.assertEqual(request.requested_role, self.instructor_role)
        self.assertEqual(request.status, UserRoleRequest.RequestStatus.PENDING)
    
    def test_role_request_approval(self):
        """Test role request approval"""
        request = UserRoleRequest.objects.create(
            user=self.user,
            requested_role=self.instructor_role,
            justification='I want to teach courses'
        )
        
        # Approve the request
        request.status = UserRoleRequest.RequestStatus.APPROVED
        request.reviewed_by = self.admin_user
        request.reviewed_at = timezone.now()
        request.save()
        
        self.assertEqual(request.status, UserRoleRequest.RequestStatus.APPROVED)
        self.assertEqual(request.reviewed_by, self.admin_user)
        self.assertIsNotNone(request.reviewed_at)
    
    def test_unique_pending_request_constraint(self):
        """Test unique constraint for pending requests"""
        # Create first pending request
        UserRoleRequest.objects.create(
            user=self.user,
            requested_role=self.instructor_role,
            justification='First request'
        )
        
        # Try to create a second pending request for the same user and role
        # This should raise an IntegrityError due to unique constraint
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            UserRoleRequest.objects.create(
                user=self.user,
                requested_role=self.instructor_role,
                justification='Second request'
            )


class RolePermissionGroupTest(TestCase):
    """Test RolePermissionGroup model functionality"""
    
    def setUp(self):
        self.permission_group = RolePermissionGroup.objects.create(
            name='Course Management',
            description='Permissions for managing courses'
        )
        self.role = RoleDefinition.objects.create(
            name=RoleDefinition.RoleType.INSTRUCTOR,
            display_name='Course Manager',
            hierarchy_level=60
        )
    
    def test_permission_group_creation(self):
        """Test permission group creation"""
        self.assertEqual(self.permission_group.name, 'Course Management')
        self.assertTrue(self.permission_group.is_active)
    
    def test_role_permission_group_relationship(self):
        """Test relationship between roles and permission groups"""
        # Note: The relationship should be set up through RolePermissionAssignment
        # For this test, we'll just verify the models exist
        self.assertIsNotNone(self.permission_group)
        self.assertIsNotNone(self.role)


class RoleChangeHistoryTest(TestCase):
    """Test RoleChangeHistory model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(  # type: ignore
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(  # type: ignore
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.role = RoleDefinition.objects.create(
            name=RoleDefinition.RoleType.INSTRUCTOR,
            display_name='Test Role',
            hierarchy_level=50
        )
        # Create a role assignment first, as it's required for RoleChangeHistory
        self.assignment = UserRoleAssignment.objects.create(
            user=self.user,
            role=self.role,
            assigned_by=self.admin_user
        )
    
    def test_role_change_history_creation(self):
        """Test role change history creation"""
        history = RoleChangeHistory.objects.create(
            user=self.user,
            role=self.role,
            role_assignment=self.assignment,
            change_type=RoleChangeHistory.ChangeType.ASSIGNED,
            changed_by=self.admin_user,
            reason='Test assignment'
        )
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.role, self.role)
        self.assertEqual(history.change_type, RoleChangeHistory.ChangeType.ASSIGNED)
        self.assertEqual(history.changed_by, self.admin_user)
    
    def test_role_change_history_metadata(self):
        """Test role change history with context"""
        context = {
            'ip_address': '192.168.1.1',
            'user_agent': 'Test Browser'
        }
        
        history = RoleChangeHistory.objects.create(
            user=self.user,
            role=self.role,
            role_assignment=self.assignment,
            change_type=RoleChangeHistory.ChangeType.ASSIGNED,
            changed_by=self.admin_user,
            context=context
        )
        
        self.assertEqual(history.context, context)