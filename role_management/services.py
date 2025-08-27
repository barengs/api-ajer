from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .models import (
    RoleDefinition, UserRoleAssignment, RoleChangeHistory,
    RolePermissionGroup, UserRoleRequest, RolePermissionAssignment
)

User = get_user_model()


class RoleManagementService:
    """Service class for role management operations"""
    
    @staticmethod
    def assign_role(
        user_id: int,
        role_id: int,
        assigned_by: User,
        reason: str = "",
        effective_from: Optional[datetime] = None,
        effective_until: Optional[datetime] = None,
        notes: str = ""
    ) -> UserRoleAssignment:
        """Assign a role to a user"""
        
        try:
            user = User.objects.get(id=user_id)
            role = RoleDefinition.objects.get(id=role_id, is_assignable=True)
        except User.DoesNotExist:
            raise ValidationError("User not found")
        except RoleDefinition.DoesNotExist:
            raise ValidationError("Role not found or not assignable")
        
        # Check if assigner has permission
        if not RoleManagementService._can_assign_role(assigned_by, role, user):
            raise PermissionDenied("Insufficient permissions to assign this role")
        
        # Check for existing active assignment
        existing_assignment = UserRoleAssignment.objects.filter(
            user=user,
            role=role,
            status=UserRoleAssignment.AssignmentStatus.ACTIVE
        ).first()
        
        if existing_assignment:
            raise ValidationError("User already has this role assigned")
        
        with transaction.atomic():
            # Create role assignment
            assignment = UserRoleAssignment.objects.create(
                user=user,
                role=role,
                assigned_by=assigned_by,
                status=UserRoleAssignment.AssignmentStatus.ACTIVE,
                effective_from=effective_from or timezone.now(),
                effective_until=effective_until,
                assignment_reason=reason,
                notes=notes
            )
            
            # Update user's role field if this is their primary role
            if RoleManagementService._is_primary_role(role, user):
                user.role = role.name  # type: ignore
                user.save()
            
            # Create history record
            RoleChangeHistory.objects.create(
                user=user,
                role=role,
                role_assignment=assignment,
                change_type=RoleChangeHistory.ChangeType.ASSIGNED,
                changed_by=assigned_by,
                reason=reason,
                new_values={
                    'status': assignment.status,
                    'effective_from': assignment.effective_from.isoformat() if assignment.effective_from else None,
                    'effective_until': assignment.effective_until.isoformat() if assignment.effective_until else None
                }
            )
            
            return assignment
    
    @staticmethod
    def revoke_role(
        assignment_id: int,
        revoked_by: User,
        reason: str = ""
    ) -> UserRoleAssignment:
        """Revoke a role assignment"""
        
        try:
            assignment = UserRoleAssignment.objects.get(
                id=assignment_id,
                status=UserRoleAssignment.AssignmentStatus.ACTIVE
            )
        except UserRoleAssignment.DoesNotExist:
            raise ValidationError("Active role assignment not found")
        
        # Check if revoker has permission
        if not RoleManagementService._can_revoke_role(revoked_by, assignment):
            raise PermissionDenied("Insufficient permissions to revoke this role")
        
        with transaction.atomic():
            # Store previous values
            previous_values = {
                'status': assignment.status,
                'effective_until': assignment.effective_until.isoformat() if assignment.effective_until else None
            }
            
            # Revoke assignment
            assignment.revoke(revoked_by, reason)
            
            # Update user's role field if needed
            user = assignment.user
            if hasattr(user, 'role') and user.role == assignment.role.name:  # type: ignore
                # Find new primary role
                new_primary_role = RoleManagementService.get_user_primary_role(user)
                user.role = new_primary_role.name if new_primary_role else 'student'  # type: ignore
                user.save()
            
            # Create history record
            RoleChangeHistory.objects.create(
                user=user,
                role=assignment.role,
                role_assignment=assignment,
                change_type=RoleChangeHistory.ChangeType.REVOKED,
                changed_by=revoked_by,
                reason=reason,
                previous_values=previous_values,
                new_values={
                    'status': assignment.status,
                    'revoked_at': assignment.revoked_at.isoformat() if assignment.revoked_at else None
                }
            )
            
            return assignment
    
    @staticmethod
    def suspend_role(
        assignment_id: int,
        suspended_by: User,
        reason: str = ""
    ) -> UserRoleAssignment:
        """Suspend a role assignment"""
        
        try:
            assignment = UserRoleAssignment.objects.get(
                id=assignment_id,
                status=UserRoleAssignment.AssignmentStatus.ACTIVE
            )
        except UserRoleAssignment.DoesNotExist:
            raise ValidationError("Active role assignment not found")
        
        # Check permissions
        if not RoleManagementService._can_modify_role(suspended_by, assignment):
            raise PermissionDenied("Insufficient permissions to suspend this role")
        
        with transaction.atomic():
            previous_values = {'status': assignment.status}
            
            assignment.status = UserRoleAssignment.AssignmentStatus.SUSPENDED
            assignment.save()
            
            # Create history record
            RoleChangeHistory.objects.create(
                user=assignment.user,
                role=assignment.role,
                role_assignment=assignment,
                change_type=RoleChangeHistory.ChangeType.SUSPENDED,
                changed_by=suspended_by,
                reason=reason,
                previous_values=previous_values,
                new_values={'status': assignment.status}
            )
            
            return assignment
    
    @staticmethod
    def reactivate_role(
        assignment_id: int,
        reactivated_by: User,
        reason: str = ""
    ) -> UserRoleAssignment:
        """Reactivate a suspended role assignment"""
        
        try:
            assignment = UserRoleAssignment.objects.get(
                id=assignment_id,
                status=UserRoleAssignment.AssignmentStatus.SUSPENDED
            )
        except UserRoleAssignment.DoesNotExist:
            raise ValidationError("Suspended role assignment not found")
        
        # Check permissions
        if not RoleManagementService._can_modify_role(reactivated_by, assignment):
            raise PermissionDenied("Insufficient permissions to reactivate this role")
        
        with transaction.atomic():
            previous_values = {'status': assignment.status}
            
            assignment.status = UserRoleAssignment.AssignmentStatus.ACTIVE
            assignment.save()
            
            # Update user's role field if this becomes primary role
            user = assignment.user
            current_primary = RoleManagementService.get_user_primary_role(user)
            if not current_primary or assignment.role.hierarchy_level < current_primary.hierarchy_level:
                user.role = assignment.role.name  # type: ignore
                user.save()
            
            # Create history record
            RoleChangeHistory.objects.create(
                user=assignment.user,
                role=assignment.role,
                role_assignment=assignment,
                change_type=RoleChangeHistory.ChangeType.REACTIVATED,
                changed_by=reactivated_by,
                reason=reason,
                previous_values=previous_values,
                new_values={'status': assignment.status}
            )
            
            return assignment
    
    @staticmethod
    def bulk_assign_roles(
        user_ids: List[int],
        role_id: int,
        assigned_by: User,
        reason: str = "",
        effective_from: Optional[datetime] = None,
        effective_until: Optional[datetime] = None
    ) -> Tuple[List[UserRoleAssignment], List[Dict[str, Any]]]:
        """Bulk assign roles to multiple users"""
        
        successful_assignments = []
        failed_assignments = []
        
        try:
            role = RoleDefinition.objects.get(id=role_id, is_assignable=True)
        except RoleDefinition.DoesNotExist:
            raise ValidationError("Role not found or not assignable")
        
        for user_id in user_ids:
            try:
                assignment = RoleManagementService.assign_role(
                    user_id=user_id,
                    role_id=role_id,
                    assigned_by=assigned_by,
                    reason=reason,
                    effective_from=effective_from,
                    effective_until=effective_until
                )
                successful_assignments.append(assignment)
                
            except (ValidationError, PermissionDenied) as e:
                failed_assignments.append({
                    'user_id': user_id,
                    'error': str(e)
                })
        
        return successful_assignments, failed_assignments
    
    @staticmethod
    def get_user_roles(user: User) -> List[UserRoleAssignment]:
        """Get all active role assignments for a user"""
        return list(UserRoleAssignment.objects.filter(
            user=user,
            status=UserRoleAssignment.AssignmentStatus.ACTIVE
        ).select_related('role'))
    
    @staticmethod
    def get_user_primary_role(user: User) -> Optional[RoleDefinition]:
        """Get user's primary (highest hierarchy) role"""
        assignment = UserRoleAssignment.objects.filter(
            user=user,
            status=UserRoleAssignment.AssignmentStatus.ACTIVE
        ).select_related('role').order_by('role__hierarchy_level').first()
        
        return assignment.role if assignment else None
    
    @staticmethod
    def get_users_by_role(role: RoleDefinition) -> List[User]:
        """Get all users with a specific role"""
        user_ids = UserRoleAssignment.objects.filter(
            role=role,
            status=UserRoleAssignment.AssignmentStatus.ACTIVE
        ).values_list('user_id', flat=True)
        
        return list(User.objects.filter(id__in=user_ids))
    
    @staticmethod
    def process_role_request(
        request_id: int,
        processed_by: User,
        approved: bool,
        notes: str = ""
    ) -> UserRoleRequest:
        """Process a role change request"""
        
        try:
            role_request = UserRoleRequest.objects.get(
                id=request_id,
                status=UserRoleRequest.RequestStatus.PENDING
            )
        except UserRoleRequest.DoesNotExist:
            raise ValidationError("Pending role request not found")
        
        # Check if processor has permission
        if not RoleManagementService._can_process_role_request(processed_by, role_request):
            raise PermissionDenied("Insufficient permissions to process this request")
        
        with transaction.atomic():
            if approved:
                role_request.approve(processed_by, notes)
                
                # Assign the role
                try:
                    RoleManagementService.assign_role(
                        user_id=role_request.user.id,
                        role_id=role_request.requested_role.id,
                        assigned_by=processed_by,
                        reason=f"Approved role request: {role_request.justification}"
                    )
                except (ValidationError, PermissionDenied):
                    # If assignment fails, reject the request
                    role_request.reject(processed_by, "Role assignment failed")
            else:
                role_request.reject(processed_by, notes)
        
        return role_request
    
    @staticmethod
    def _can_assign_role(assigner: User, role: RoleDefinition, target_user: User) -> bool:
        """Check if user can assign a specific role"""
        # Admin can assign any role
        if hasattr(assigner, 'role') and assigner.role == 'admin':  # type: ignore
            return True
        
        # Get assigner's highest role
        assigner_role = RoleManagementService.get_user_primary_role(assigner)
        if not assigner_role:
            return False
        
        # Can't assign role higher or equal to own hierarchy
        if role.hierarchy_level <= assigner_role.hierarchy_level:
            return False
        
        # Check specific permissions
        if not assigner_role.can_manage_users:
            return False
        
        # Check manageable user limits
        if assigner_role.max_users_manageable is not None:
            current_managed = UserRoleAssignment.objects.filter(
                assigned_by=assigner,
                status=UserRoleAssignment.AssignmentStatus.ACTIVE
            ).count()
            
            if current_managed >= assigner_role.max_users_manageable:
                return False
        
        return True
    
    @staticmethod
    def _can_revoke_role(revoker: User, assignment: UserRoleAssignment) -> bool:
        """Check if user can revoke a specific role assignment"""
        # Admin can revoke any role
        if hasattr(revoker, 'role') and revoker.role == 'admin':  # type: ignore
            return True
        
        # Users can revoke their own roles (self-revocation)
        if assignment.user == revoker:
            return True
        
        # Check if revoker assigned the role originally
        if assignment.assigned_by == revoker:
            return True
        
        # Get revoker's highest role
        revoker_role = RoleManagementService.get_user_primary_role(revoker)
        if not revoker_role:
            return False
        
        # Can't revoke role higher or equal to own hierarchy
        if assignment.role.hierarchy_level <= revoker_role.hierarchy_level:
            return False
        
        # Check specific permissions
        return revoker_role.can_manage_users
    
    @staticmethod
    def _can_modify_role(modifier: User, assignment: UserRoleAssignment) -> bool:
        """Check if user can modify a specific role assignment"""
        return RoleManagementService._can_revoke_role(modifier, assignment)
    
    @staticmethod
    def _can_process_role_request(processor: User, role_request: UserRoleRequest) -> bool:
        """Check if user can process a role request"""
        # Admin can process any request
        if hasattr(processor, 'role') and processor.role == 'admin':  # type: ignore
            return True
        
        # Get processor's highest role
        processor_role = RoleManagementService.get_user_primary_role(processor)
        if not processor_role:
            return False
        
        # Can't process request for role higher or equal to own hierarchy
        if role_request.requested_role.hierarchy_level <= processor_role.hierarchy_level:
            return False
        
        # Check specific permissions
        return processor_role.can_manage_users
    
    @staticmethod
    def _is_primary_role(role: RoleDefinition, user: User) -> bool:
        """Check if this role should be the user's primary role"""
        current_primary = RoleManagementService.get_user_primary_role(user)
        
        # If no current primary role, this becomes primary
        if not current_primary:
            return True
        
        # If this role has higher hierarchy (lower number), it becomes primary
        return role.hierarchy_level < current_primary.hierarchy_level


class RolePermissionService:
    """Service for managing role permissions"""
    
    @staticmethod
    def create_permission_group(
        name: str,
        description: str,
        permissions: List[str],
        created_by: User
    ) -> RolePermissionGroup:
        """Create a new permission group"""
        
        if not RolePermissionService._can_manage_permissions(created_by):
            raise PermissionDenied("Insufficient permissions to create permission groups")
        
        return RolePermissionGroup.objects.create(
            name=name,
            description=description,
            permissions=permissions
        )
    
    @staticmethod
    def assign_permission_group_to_role(
        role_id: int,
        permission_group_id: int,
        assigned_by: User
    ) -> bool:
        """Assign a permission group to a role"""
        
        if not RolePermissionService._can_manage_permissions(assigned_by):
            raise PermissionDenied("Insufficient permissions to assign permission groups")
        
        try:
            role = RoleDefinition.objects.get(id=role_id)
            permission_group = RolePermissionGroup.objects.get(id=permission_group_id)
            
            # Create the assignment through the through model
            assignment, created = RolePermissionAssignment.objects.get_or_create(
                role=role,
                permission_group=permission_group,
                defaults={'assigned_by': assigned_by}
            )
            return True
            
        except (RoleDefinition.DoesNotExist, RolePermissionGroup.DoesNotExist):
            raise ValidationError("Role or permission group not found")
    
    @staticmethod
    def _can_manage_permissions(user: User) -> bool:
        """Check if user can manage permissions"""
        if hasattr(user, 'role') and user.role == 'admin':  # type: ignore
            return True
        
        user_role = RoleManagementService.get_user_primary_role(user)
        return bool(user_role and user_role.can_manage_system)