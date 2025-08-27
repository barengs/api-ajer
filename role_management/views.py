from typing import Dict, Any, Optional, cast
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, ListCreateAPIView
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import (
    RoleDefinition, UserRoleAssignment, RoleChangeHistory,
    RolePermissionGroup, UserRoleRequest
)
from .serializers import (
    RoleDefinitionSerializer, UserRoleAssignmentSerializer,
    RoleChangeHistorySerializer, RolePermissionGroupSerializer,
    UserRoleRequestSerializer, UserRoleManagementSerializer,
    UserWithRolesSerializer, BulkRoleAssignmentSerializer
)
from .services import RoleManagementService, RolePermissionService

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class RoleDefinitionListView(ListCreateAPIView):
    """List and create role definitions"""
    
    serializer_class = RoleDefinitionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        tags=['Role Management'],
        summary='List Role Definitions',
        description='Get list of all role definitions with their permissions and settings',
        parameters=[
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by active status'
            ),
            OpenApiParameter(
                name='is_assignable',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by assignable status'
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Role Management'],
        summary='Create Role Definition',
        description='Create a new role definition (Admin only)',
        request=RoleDefinitionSerializer,
        responses={
            201: RoleDefinitionSerializer,
            403: {'description': 'Forbidden - Admin access required'}
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def get_queryset(self):  # type: ignore[override]
        """Filter role definitions based on query parameters"""
        queryset = RoleDefinition.objects.all()
        
        # Apply filters
        is_active = getattr(self.request, 'query_params', self.request.GET).get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        is_assignable = getattr(self.request, 'query_params', self.request.GET).get('is_assignable')
        if is_assignable is not None:
            queryset = queryset.filter(is_assignable=is_assignable.lower() == 'true')
        
        return queryset.order_by('hierarchy_level', 'name')
    
    def perform_create(self, serializer):
        """Check admin permission before creating role"""
        if not hasattr(self.request.user, 'role') or self.request.user.role != 'admin':  # type: ignore
            raise PermissionDenied("Admin access required")
        
        serializer.save()


class RoleDefinitionDetailView(RetrieveAPIView):
    """Retrieve specific role definition"""
    
    queryset = RoleDefinition.objects.all()
    serializer_class = RoleDefinitionSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Role Management'],
        summary='Get Role Definition',
        description='Get detailed information about a specific role definition'
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserRoleAssignmentListView(ListAPIView):
    """List user role assignments with filtering"""
    
    serializer_class = UserRoleAssignmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        tags=['Role Management'],
        summary='List User Role Assignments',
        description='Get list of user role assignments with filtering options',
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by user ID'
            ),
            OpenApiParameter(
                name='role_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by role ID'
            ),
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by assignment status'
            ),
            OpenApiParameter(
                name='assigned_by',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by who assigned the role'
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):  # type: ignore[override]
        """Filter role assignments based on permissions and query parameters"""
        user = self.request.user
        
        # Base queryset
        queryset = UserRoleAssignment.objects.select_related(
            'user', 'role_definition', 'assigned_by'
        )
        
        # Apply permission-based filtering
        if hasattr(user, 'role') and user.role == 'admin':  # type: ignore
            # Admin can see all assignments
            pass
        elif hasattr(user, 'role') and user.role in ['instructor', 'moderator']:  # type: ignore
            # Instructors/moderators can see assignments they made or lower hierarchy roles
            if hasattr(user, 'is_authenticated') and user.is_authenticated:  # type: ignore
                user_role = RoleManagementService.get_user_primary_role(user)  # type: ignore
            else:
                user_role = None
            if user_role:
                queryset = queryset.filter(
                    Q(assigned_by=user) |
                    Q(role_definition__hierarchy_level__lt=user_role.hierarchy_level)
                )
        else:
            # Regular users can only see their own assignments
            queryset = queryset.filter(user=user)
        
        # Apply query parameter filters
        user_id = getattr(self.request, 'query_params', self.request.GET).get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        role_id = getattr(self.request, 'query_params', self.request.GET).get('role_id')
        if role_id:
            queryset = queryset.filter(role_definition_id=role_id)
        
        status_filter = getattr(self.request, 'query_params', self.request.GET).get('status')
        if status_filter:
            queryset = queryset.filter(is_active=status_filter.lower() == 'true')
        
        assigned_by = getattr(self.request, 'query_params', self.request.GET).get('assigned_by')
        if assigned_by:
            queryset = queryset.filter(assigned_by_id=assigned_by)
        
        return queryset.order_by('-assigned_at')


class UserRoleManagementView(APIView):
    """Manage user role assignments"""
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Role Management'],
        summary='Manage User Role',
        description='''
        Perform role management actions on users.
        
        **Available Actions:**
        - assign: Assign a role to user
        - revoke: Revoke a role from user
        - suspend: Suspend a role assignment
        - reactivate: Reactivate a suspended role
        
        **Permissions:**
        - Admin: Can manage all roles
        - Users with can_manage_users: Can manage lower hierarchy roles
        ''',
        request=UserRoleManagementSerializer,
        responses={
            200: UserRoleAssignmentSerializer,
            400: {'description': 'Invalid request data'},
            403: {'description': 'Insufficient permissions'},
            404: {'description': 'User or role not found'}
        }
    )
    def post(self, request):
        """Perform role management action"""
        serializer = UserRoleManagementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Type casting for proper type checking
        data: Dict[str, Any] = cast(Dict[str, Any], serializer.validated_data)
        if not data:
            return Response(
                {'error': 'Invalid request data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action = data.get('action')
        if not action:
            return Response(
                {'error': 'Action is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            assignment = None
            
            if action == 'assign':
                user_id = data.get('user_id')
                role_id = data.get('role_id')
                
                if not user_id or not role_id:
                    return Response(
                        {'error': 'user_id and role_id are required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                assignment = RoleManagementService.assign_role(
                    user_id=int(user_id),
                    role_id=int(role_id),
                    assigned_by=request.user,
                    reason=data.get('reason', ''),
                    effective_from=data.get('effective_from'),
                    effective_until=data.get('effective_until'),
                    notes=data.get('notes', '')
                )
                
            elif action == 'revoke':
                user_id = data.get('user_id')
                role_id = data.get('role_id')
                
                if not user_id or not role_id:
                    return Response(
                        {'error': 'user_id and role_id are required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Find the assignment to revoke
                assignment = UserRoleAssignment.objects.filter(
                    user_id=int(user_id),
                    role_id=int(role_id),
                    status=UserRoleAssignment.AssignmentStatus.ACTIVE
                ).first()
                
                if not assignment:
                    return Response(
                        {'error': 'Active role assignment not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                assignment = RoleManagementService.revoke_role(
                    assignment_id=assignment.pk,
                    revoked_by=request.user,
                    reason=data.get('reason', '')
                )
                
            elif action == 'suspend':
                user_id = data.get('user_id')
                role_id = data.get('role_id')
                
                if not user_id or not role_id:
                    return Response(
                        {'error': 'user_id and role_id are required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                assignment = UserRoleAssignment.objects.filter(
                    user_id=int(user_id),
                    role_id=int(role_id),
                    status=UserRoleAssignment.AssignmentStatus.ACTIVE
                ).first()
                
                if not assignment:
                    return Response(
                        {'error': 'Active role assignment not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                assignment = RoleManagementService.suspend_role(
                    assignment_id=assignment.pk,
                    suspended_by=request.user,
                    reason=data.get('reason', '')
                )
                
            elif action == 'reactivate':
                user_id = data.get('user_id')
                role_id = data.get('role_id')
                
                if not user_id or not role_id:
                    return Response(
                        {'error': 'user_id and role_id are required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                assignment = UserRoleAssignment.objects.filter(
                    user_id=int(user_id),
                    role_id=int(role_id),
                    status=UserRoleAssignment.AssignmentStatus.SUSPENDED
                ).first()
                
                if not assignment:
                    return Response(
                        {'error': 'Suspended role assignment not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                assignment = RoleManagementService.reactivate_role(
                    assignment_id=assignment.pk,
                    reactivated_by=request.user,
                    reason=data.get('reason', '')
                )
            else:
                return Response(
                    {'error': f'Invalid action: {action}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if assignment is None:
                return Response(
                    {'error': 'Failed to process role assignment'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = UserRoleAssignmentSerializer(assignment)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )


class BulkRoleAssignmentView(APIView):
    """Bulk role assignment operations"""
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Role Management'],
        summary='Bulk Role Assignment',
        description='Assign or revoke roles for multiple users at once (Admin/Manager only)',
        request=BulkRoleAssignmentSerializer,
        responses={
            200: {
                'description': 'Bulk operation completed',
                'content': {
                    'application/json': {
                        'example': {
                            'successful_count': 5,
                            'failed_count': 2,
                            'successful_assignments': [],
                            'failed_assignments': []
                        }
                    }
                }
            }
        }
    )
    def post(self, request):
        """Perform bulk role assignments"""
        serializer = BulkRoleAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Type casting for proper type checking
        data: Dict[str, Any] = cast(Dict[str, Any], serializer.validated_data)
        if not data:
            return Response(
                {'error': 'Invalid request data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action = data.get('action')
        if not action:
            return Response(
                {'error': 'Action is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if action == 'assign':
                user_ids = data.get('user_ids', [])
                role_id = data.get('role_id')
                
                if not user_ids or not role_id:
                    return Response(
                        {'error': 'user_ids and role_id are required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                successful, failed = RoleManagementService.bulk_assign_roles(
                    user_ids=user_ids,
                    role_id=role_id,
                    assigned_by=request.user,
                    reason=data.get('reason', ''),
                    effective_from=data.get('effective_from'),
                    effective_until=data.get('effective_until')
                )
                
                successful_serializer = UserRoleAssignmentSerializer(successful, many=True)
                
                return Response({
                    'successful_count': len(successful),
                    'failed_count': len(failed),
                    'successful_assignments': successful_serializer.data,
                    'failed_assignments': failed
                }, status=status.HTTP_200_OK)
                
            elif action == 'revoke':
                user_ids = data.get('user_ids', [])
                role_id = data.get('role_id')
                
                if not user_ids or not role_id:
                    return Response(
                        {'error': 'user_ids and role_id are required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Implement bulk revoke logic
                successful = []
                failed = []
                
                for user_id in user_ids:
                    try:
                        assignment = UserRoleAssignment.objects.filter(
                            user_id=user_id,
                            role_id=role_id,
                            status=UserRoleAssignment.AssignmentStatus.ACTIVE
                        ).first()
                        
                        if assignment:
                            revoked_assignment = RoleManagementService.revoke_role(
                                assignment_id=assignment.pk,
                                revoked_by=request.user,
                                reason=data.get('reason', '')
                            )
                            successful.append(revoked_assignment)
                        else:
                            failed.append({
                                'user_id': user_id,
                                'error': 'Active role assignment not found'
                            })
                            
                    except (ValidationError, PermissionDenied) as e:
                        failed.append({
                            'user_id': user_id,
                            'error': str(e)
                        })
                
                successful_serializer = UserRoleAssignmentSerializer(successful, many=True)
                
                return Response({
                    'successful_count': len(successful),
                    'failed_count': len(failed),
                    'successful_assignments': successful_serializer.data,
                    'failed_assignments': failed
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': f'Invalid action: {action}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )


class UserWithRolesListView(ListAPIView):
    """List users with their role information"""
    
    serializer_class = UserWithRolesSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        tags=['Role Management'],
        summary='List Users with Roles',
        description='Get list of users with their current role assignments',
        parameters=[
            OpenApiParameter(
                name='role',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by specific role name'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search by username or email'
            ),
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by user active status'
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):  # type: ignore[override]
        """Filter users based on permissions and query parameters"""
        user = self.request.user
        
        # Base queryset
        queryset = User.objects.prefetch_related('role_assignments__role')
        
        # Apply permission-based filtering
        if not (hasattr(user, 'role') and user.role in ['admin', 'moderator']):  # type: ignore
            # Non-admin/moderator users see limited user list
            return User.objects.none()
        
        # Apply query parameter filters
        role_filter = getattr(self.request, 'query_params', self.request.GET).get('role')
        if role_filter:
            queryset = queryset.filter(
                role_assignments__role__name=role_filter,
                role_assignments__status=UserRoleAssignment.AssignmentStatus.ACTIVE
            )
        
        search = getattr(self.request, 'query_params', self.request.GET).get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        is_active = getattr(self.request, 'query_params', self.request.GET).get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.distinct().order_by('username')


class RoleChangeHistoryListView(ListAPIView):
    """List role change history"""
    
    serializer_class = RoleChangeHistorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        tags=['Role Management'],
        summary='List Role Change History',
        description='Get audit trail of role changes',
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by user ID'
            ),
            OpenApiParameter(
                name='role_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by role ID'
            ),
            OpenApiParameter(
                name='change_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by change type'
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):  # type: ignore[override]
        """Filter role change history based on permissions"""
        user = self.request.user
        
        # Only admin and moderators can view change history
        if not (hasattr(user, 'role') and user.role in ['admin', 'moderator']):  # type: ignore
            return RoleChangeHistory.objects.none()
        
        queryset = RoleChangeHistory.objects.select_related(
            'user', 'role', 'changed_by'
        )
        
        # Apply filters
        user_id = getattr(self.request, 'query_params', self.request.GET).get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        role_id = getattr(self.request, 'query_params', self.request.GET).get('role_id')
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        
        change_type = getattr(self.request, 'query_params', self.request.GET).get('change_type')
        if change_type:
            queryset = queryset.filter(change_type=change_type)
        
        return queryset.order_by('-changed_at')


class UserRoleRequestListView(ListCreateAPIView):
    """List and create user role requests"""
    
    serializer_class = UserRoleRequestSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        tags=['Role Management'],
        summary='List Role Requests',
        description='Get list of role change requests',
        parameters=[
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by request status'
            ),
            OpenApiParameter(
                name='requested_role',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by requested role ID'
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Role Management'],
        summary='Create Role Request',
        description='Submit a request for role change',
        request=UserRoleRequestSerializer
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def get_queryset(self):  # type: ignore[override]
        """Filter role requests based on permissions"""
        user = self.request.user
        
        if hasattr(user, 'role') and user.role in ['admin', 'moderator']:  # type: ignore
            # Admin and moderators can see all requests
            queryset = UserRoleRequest.objects.all()
        else:
            # Regular users can only see their own requests
            queryset = UserRoleRequest.objects.filter(user=user)
        
        # Apply filters
        status_filter = getattr(self.request, 'query_params', self.request.GET).get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        requested_role = getattr(self.request, 'query_params', self.request.GET).get('requested_role')
        if requested_role:
            queryset = queryset.filter(requested_role_id=requested_role)
        
        return queryset.select_related(
            'user', 'requested_role', 'reviewed_by'
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set the requesting user"""
        serializer.save(user=self.request.user)


@extend_schema(
    tags=['Role Management'],
    summary='Process Role Request',
    description='Approve or reject a role change request (Admin/Manager only)',
    request={
        'application/json': {
            'example': {
                'approved': True,
                'notes': 'Request approved based on qualifications'
            }
        }
    },
    responses={
        200: UserRoleRequestSerializer,
        403: {'description': 'Insufficient permissions'},
        404: {'description': 'Request not found'}
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_role_request(request, request_id):
    """Process a role change request"""
    try:
        approved = request.data.get('approved', False)
        notes = request.data.get('notes', '')
        
        role_request = RoleManagementService.process_role_request(
            request_id=request_id,
            processed_by=request.user,
            approved=approved,
            notes=notes
        )
        
        serializer = UserRoleRequestSerializer(role_request)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except ValidationError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except PermissionDenied as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_403_FORBIDDEN
        )


@extend_schema(
    tags=['Role Management'],
    summary='Get User Role Statistics',
    description='Get statistics about role assignments and changes',
    responses={
        200: {
            'description': 'Role statistics',
            'content': {
                'application/json': {
                    'example': {
                        'total_users': 100,
                        'users_by_role': {
                            'admin': 5,
                            'instructor': 20,
                            'student': 75
                        },
                        'recent_changes': 10,
                        'pending_requests': 3
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def role_statistics(request):
    """Get role management statistics"""
    # Check admin permission
    if not (hasattr(request.user, 'role') and request.user.role == 'admin'):  # type: ignore
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Calculate statistics
    total_users = User.objects.count()
    
    # Users by role
    users_by_role = {}
    for role in RoleDefinition.objects.filter(is_active=True):
        count = UserRoleAssignment.objects.filter(
            role=role,
            status=UserRoleAssignment.AssignmentStatus.ACTIVE
        ).count()
        users_by_role[role.name] = count
    
    # Recent changes (last 30 days)
    from datetime import timedelta
    from django.utils import timezone
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_changes = RoleChangeHistory.objects.filter(
        changed_at__gte=thirty_days_ago
    ).count()
    
    # Pending requests
    pending_requests = UserRoleRequest.objects.filter(
        status=UserRoleRequest.RequestStatus.PENDING
    ).count()
    
    return Response({
        'total_users': total_users,
        'users_by_role': users_by_role,
        'recent_changes': recent_changes,
        'pending_requests': pending_requests
    }, status=status.HTTP_200_OK)


class UserRoleDetailView(APIView):
    """Manage specific user role assignment"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Role Management'],
        summary='Get User Role Assignment',
        description='Get details of a specific user role assignment'
    )
    def get(self, request, user_id, role_id):
        try:
            assignment = UserRoleAssignment.objects.get(
                user_id=user_id,
                role_definition_id=role_id
            )
            serializer = UserRoleAssignmentSerializer(assignment)
            return Response(serializer.data)
        except UserRoleAssignment.DoesNotExist:
            return Response(
                {'error': 'Role assignment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        tags=['Role Management'],
        summary='Update User Role Assignment',
        description='Update a specific user role assignment (Admin only)'
    )
    def put(self, request, user_id, role_id):
        # Admin permission check
        if not (hasattr(request.user, 'role') and request.user.role == 'admin'):  # type: ignore
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            assignment = UserRoleAssignment.objects.get(
                user_id=user_id,
                role_definition_id=role_id
            )
            serializer = UserRoleAssignmentSerializer(assignment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserRoleAssignment.DoesNotExist:
            return Response(
                {'error': 'Role assignment not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class BulkRoleRevocationView(APIView):
    """Bulk revoke roles from multiple users"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Role Management'],
        summary='Bulk Revoke Roles',
        description='Revoke roles from multiple users (Admin only)',
        request={
            'application/json': {
                'example': {
                    'user_ids': [1, 2, 3],
                    'role_id': 5,
                    'reason': 'Bulk revocation for security purposes'
                }
            }
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'successful_count': {'type': 'integer', 'example': 2},
                    'failed_count': {'type': 'integer', 'example': 1},
                    'successful_revocations': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer', 'example': 1},
                                'user': {'type': 'integer', 'example': 1},
                                'role_definition': {'type': 'integer', 'example': 5},
                                'assigned_at': {'type': 'string', 'format': 'date-time'},
                                'assigned_by': {'type': 'integer', 'example': 1},
                                'is_active': {'type': 'boolean', 'example': False},
                                'revoked_at': {'type': 'string', 'format': 'date-time'},
                                'revoked_by': {'type': 'integer', 'example': 1},
                                'revocation_reason': {'type': 'string', 'example': 'Bulk revocation for security purposes'}
                            }
                        }
                    },
                    'failed_revocations': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'user_id': {'type': 'integer', 'example': 3},
                                'error': {'type': 'string', 'example': 'Active role assignment not found'}
                            }
                        }
                    }
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'example': 'user_ids and role_id are required'}
                }
            },
            403: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'example': 'Admin access required'}
                }
            },
            404: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'example': 'Role not found'}
                }
            }
        }
    )
    def post(self, request):
        if not (hasattr(request.user, 'role') and request.user.role == 'admin'):  # type: ignore
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = request.data
        user_ids = data.get('user_ids', [])
        role_id = data.get('role_id')
        reason = data.get('reason', '')
        
        if not user_ids or not role_id:
            return Response(
                {'error': 'user_ids and role_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            role = RoleDefinition.objects.get(id=role_id)
            
            # Implement bulk revoke logic similar to BulkRoleAssignmentView
            successful = []
            failed = []
            
            for user_id in user_ids:
                try:
                    assignment = UserRoleAssignment.objects.filter(
                        user_id=user_id,
                        role_definition_id=role_id,
                        status=UserRoleAssignment.AssignmentStatus.ACTIVE
                    ).first()
                    
                    if assignment:
                        revoked_assignment = RoleManagementService.revoke_role(
                            assignment_id=assignment.pk,
                            revoked_by=request.user,
                            reason=reason
                        )
                        successful.append(revoked_assignment)
                    else:
                        failed.append({
                            'user_id': user_id,
                            'error': 'Active role assignment not found'
                        })
                        
                except (ValidationError, PermissionDenied) as e:
                    failed.append({
                        'user_id': user_id,
                        'error': str(e)
                    })
            
            successful_serializer = UserRoleAssignmentSerializer(successful, many=True)
            
            results = {
                'successful_count': len(successful),
                'failed_count': len(failed),
                'successful_revocations': successful_serializer.data,
                'failed_revocations': failed
            }
            
            return Response(results, status=status.HTTP_200_OK)
            
        except RoleDefinition.DoesNotExist:
            return Response(
                {'error': 'Role not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RoleStatisticsView(APIView):
    """Get role management statistics"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Role Management'],
        summary='Get Role Statistics',
        description='Get comprehensive role management statistics (Admin only)'
    )
    def get(self, request):
        if not (hasattr(request.user, 'role') and request.user.role == 'admin'):  # type: ignore
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get statistics
        total_users = User.objects.count()
        total_roles = RoleDefinition.objects.filter(is_active=True).count()
        active_assignments = UserRoleAssignment.objects.filter(is_active=True).count()
        
        # Role distribution
        role_distribution = []
        for role in RoleDefinition.objects.filter(is_active=True):
            count = UserRoleAssignment.objects.filter(
                role_definition=role,
                is_active=True
            ).count()
            role_distribution.append({
                'role_name': role.name,
                'role_type': role.name,
                'user_count': count
            })
        
        # Recent activity
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_changes = RoleChangeHistory.objects.filter(
            changed_at__gte=thirty_days_ago
        ).count()
        
        pending_requests = UserRoleRequest.objects.filter(
            status=UserRoleRequest.RequestStatus.PENDING
        ).count()
        
        return Response({
            'total_users': total_users,
            'total_roles': total_roles,
            'active_assignments': active_assignments,
            'role_distribution': role_distribution,
            'recent_changes': recent_changes,
            'pending_requests': pending_requests
        })


class UsersByRoleView(ListAPIView):
    """Get users grouped by their roles"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserWithRolesSerializer
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        tags=['Role Management'],
        summary='Get Users by Role',
        description='Get users grouped by their assigned roles (Admin only)'
    )
    def get(self, request, *args, **kwargs):
        if not (hasattr(request.user, 'role') and request.user.role == 'admin'):  # type: ignore
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):  # type: ignore[override]
        role_type = getattr(self.request, 'query_params', self.request.GET).get('role_type')
        queryset = User.objects.prefetch_related('role_assignments__role_definition')
        
        if role_type:
            queryset = queryset.filter(
                role_assignments__role_definition__role_type=role_type,
                role_assignments__is_active=True
            ).distinct()
        
        return queryset


class RoleRequestDetailView(RetrieveAPIView):
    """Get details of a specific role request"""
    queryset = UserRoleRequest.objects.all()
    serializer_class = UserRoleRequestSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Role Management'],
        summary='Get Role Request Details',
        description='Get detailed information about a role change request'
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ApproveRoleRequestView(APIView):
    """Approve a role change request"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Role Management'],
        summary='Approve Role Request',
        description='Approve a pending role change request (Admin only)'
    )
    def post(self, request, pk):
        if not (hasattr(request.user, 'role') and request.user.role == 'admin'):  # type: ignore
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            role_request = UserRoleRequest.objects.get(pk=pk)
            
            if role_request.status != UserRoleRequest.RequestStatus.PENDING:
                return Response(
                    {'error': 'Request has already been processed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Approve the request
            role_request.status = UserRoleRequest.RequestStatus.APPROVED
            role_request.reviewed_by = request.user
            role_request.reviewed_at = timezone.now()
            role_request.review_notes = request.data.get('admin_notes', '')
            role_request.save()
            
            # Assign the role
            RoleManagementService.assign_role(
                user_id=role_request.user.id,
                role_id=role_request.requested_role.id,
                assigned_by=request.user,
                reason=f'Approved role request #{role_request.pk}'
            )
            
            serializer = UserRoleRequestSerializer(role_request)
            return Response(serializer.data)
            
        except UserRoleRequest.DoesNotExist:
            return Response(
                {'error': 'Role request not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RejectRoleRequestView(APIView):
    """Reject a role change request"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Role Management'],
        summary='Reject Role Request',
        description='Reject a pending role change request (Admin only)'
    )
    def post(self, request, pk):
        if not (hasattr(request.user, 'role') and request.user.role == 'admin'):  # type: ignore
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            role_request = UserRoleRequest.objects.get(pk=pk)
            
            if role_request.status != UserRoleRequest.RequestStatus.PENDING:
                return Response(
                    {'error': 'Request has already been processed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Reject the request
            role_request.status = UserRoleRequest.RequestStatus.REJECTED
            role_request.reviewed_by = request.user
            role_request.reviewed_at = timezone.now()
            role_request.review_notes = request.data.get('admin_notes', '')
            role_request.save()
            
            serializer = UserRoleRequestSerializer(role_request)
            return Response(serializer.data)
            
        except UserRoleRequest.DoesNotExist:
            return Response(
                {'error': 'Role request not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class UserRoleHistoryView(ListAPIView):
    """Get role change history for a specific user"""
    serializer_class = RoleChangeHistorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        tags=['Role Management'],
        summary='Get User Role History',
        description='Get role change history for a specific user'
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):  # type: ignore[override]
        user_id = self.kwargs['user_id']
        return RoleChangeHistory.objects.filter(
            user_id=user_id
        ).select_related(
            'user', 'role_definition', 'changed_by'
        ).order_by('-changed_at')


class RolePermissionGroupListView(ListAPIView):
    """List role permission groups"""
    queryset = RolePermissionGroup.objects.filter(is_active=True)
    serializer_class = RolePermissionGroupSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        tags=['Role Management'],
        summary='List Permission Groups',
        description='Get list of role permission groups'
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class RolePermissionGroupDetailView(RetrieveAPIView):
    """Get details of a specific permission group"""
    queryset = RolePermissionGroup.objects.all()
    serializer_class = RolePermissionGroupSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Role Management'],
        summary='Get Permission Group Details',
        description='Get detailed information about a permission group'
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)