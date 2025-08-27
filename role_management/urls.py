from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()

app_name = 'role_management'

urlpatterns = [
    # Role Definition endpoints
    path('roles/', views.RoleDefinitionListView.as_view(), name='role-list'),
    path('roles/<int:pk>/', views.RoleDefinitionDetailView.as_view(), name='role-detail'),
    
    # User Role Management endpoints
    path('users/<int:user_id>/roles/', views.UserRoleManagementView.as_view(), name='user-roles'),
    path('users/<int:user_id>/roles/<int:role_id>/', views.UserRoleDetailView.as_view(), name='user-role-detail'),
    
    # Bulk operations
    path('users/bulk-assign-roles/', views.BulkRoleAssignmentView.as_view(), name='bulk-assign-roles'),
    path('users/bulk-revoke-roles/', views.BulkRoleRevocationView.as_view(), name='bulk-revoke-roles'),
    
    # User listing with roles
    path('users/', views.UserWithRolesListView.as_view(), name='users-with-roles'),
    
    # Role statistics and analytics
    path('statistics/', views.RoleStatisticsView.as_view(), name='role-statistics'),
    path('statistics/users-by-role/', views.UsersByRoleView.as_view(), name='users-by-role'),
    
    # Role requests management
    path('requests/', views.UserRoleRequestListView.as_view(), name='role-requests'),
    path('requests/<int:pk>/', views.RoleRequestDetailView.as_view(), name='role-request-detail'),
    path('requests/<int:pk>/approve/', views.ApproveRoleRequestView.as_view(), name='approve-role-request'),
    path('requests/<int:pk>/reject/', views.RejectRoleRequestView.as_view(), name='reject-role-request'),
    
    # Role change history
    path('history/', views.RoleChangeHistoryListView.as_view(), name='role-history'),
    path('users/<int:user_id>/history/', views.UserRoleHistoryView.as_view(), name='user-role-history'),
    
    # Permission groups
    path('permission-groups/', views.RolePermissionGroupListView.as_view(), name='permission-groups'),
    path('permission-groups/<int:pk>/', views.RolePermissionGroupDetailView.as_view(), name='permission-group-detail'),
    
    # Include router URLs
    path('', include(router.urls)),
]