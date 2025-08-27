from rest_framework import status, permissions, generics, viewsets, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FileUploadParser
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, QuerySet
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from typing import Any
import json
import csv

from .models import (
    MenuGroup, MenuItem, MenuItemPermission, 
    MenuClickTracking, MenuConfiguration
)
from .serializers import (
    MenuGroupSerializer, MenuItemSerializer, MenuItemCreateSerializer,
    MenuItemUpdateSerializer, MenuItemPermissionSerializer,
    MenuClickTrackingSerializer, NavigationTreeSerializer, 
    MenuAnalyticsSerializer, MenuConfigurationSerializer
)
from .utils import get_user_role_level, track_menu_click


class NavigationTreeView(APIView):
    """
    Get complete navigation tree for the current user based on their role
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        tags=['Navigation'],
        summary='Get Navigation Tree',
        description='''
        Mendapatkan struktur navigasi lengkap berdasarkan role pengguna.
        
        **Fitur:**
        - Hierarki menu yang lengkap dengan sub-menu
        - Filter otomatis berdasarkan level role pengguna
        - Informasi URL yang sudah di-resolve
        - Status visibility untuk setiap menu item
        
        **Role Levels:**
        - 10: Student
        - 30: Instructor  
        - 70: Admin
        - 100: Super Admin
        ''',
        parameters=[
            OpenApiParameter(
                name='group_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by menu group type (main, admin, student, instructor)',
                enum=['main', 'admin', 'student', 'instructor', 'mobile']
            )
        ],
        responses={
            200: NavigationTreeSerializer,
            404: {'description': 'No navigation found'}
        }
    )
    def get(self, request):
        """Get navigation tree for current user"""
        group_type = request.query_params.get('group_type')
        
        # Get user's role level
        user_role_level = get_user_role_level(request.user) if request.user.is_authenticated else 10
        
        # Filter menu groups based on role level and group type
        menu_groups_qs = MenuGroup.objects.filter(
            is_active=True,
            min_role_level__lte=user_role_level
        ).order_by('sort_order', 'name')
        
        if group_type:
            menu_groups_qs = menu_groups_qs.filter(group_type=group_type)
        
        # Get user permissions
        user_permissions = []
        if request.user.is_authenticated:
            user_permissions = list(request.user.get_all_permissions())
        
        # Serialize response
        serializer = NavigationTreeSerializer({
            'menu_groups': menu_groups_qs,
            'user_role_level': user_role_level,
            'user_permissions': user_permissions
        }, context={'request': request})
        
        return Response(serializer.data, status=status.HTTP_200_OK)


class MenuGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing menu groups
    """
    queryset = MenuGroup.objects.all()
    serializer_class = MenuGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['sort_order', 'name', 'created_at']
    ordering = ['sort_order', 'name']
    
    @extend_schema(
        tags=['Navigation'],
        summary='List Menu Groups',
        description='Get list of menu groups with filtering options'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Navigation'],
        summary='Create Menu Group',
        description='Create a new menu group (Admin only)'
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Navigation'],
        summary='Validate Menu Structure',
        description='Validate menu structure for circular references and other issues'
    )
    @action(detail=True, methods=['get'])
    def validate_structure(self, request, pk=None):
        """Validate menu group structure"""
        menu_group = self.get_object()
        
        # Check admin permission
        user_role_level = get_user_role_level(request.user)
        if user_role_level < 70:
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        from .utils import validate_menu_structure
        validation_result = validate_menu_structure(menu_group)
        
        return Response(validation_result, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Navigation'],
        summary='Export Menu Group',
        description='Export complete menu group structure as JSON'
    )
    @action(detail=True, methods=['get'])
    def export_structure(self, request, pk=None):
        """Export menu group structure"""
        menu_group = self.get_object()
        
        # Check admin permission
        user_role_level = get_user_role_level(request.user)
        if user_role_level < 70:
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        from .utils import export_menu_structure
        export_data = export_menu_structure(menu_group)
        
        response = HttpResponse(
            json.dumps(export_data, indent=2, default=str),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="menu_{menu_group.slug}.json"'
        return response
    
    def get_queryset(self):  # type: ignore[override]
        """Filter queryset based on user permissions"""
        user_role_level = get_user_role_level(self.request.user)
        
        if user_role_level >= 70:  # Admin and above can see all
            return MenuGroup.objects.all()
        else:
            return MenuGroup.objects.filter(
                min_role_level__lte=user_role_level
            )
    
    def perform_create(self, serializer):
        """Set created_by when creating menu group"""
        serializer.save(created_by=self.request.user)
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Only admin and above can modify
            user_role_level = get_user_role_level(self.request.user)
            if user_role_level < 70:
                self.permission_classes = [permissions.IsAdminUser]
        
        return super().get_permissions()


class MenuItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing menu items
    """
    queryset = MenuItem.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'url_name', 'url_path']
    ordering_fields = ['sort_order', 'title', 'created_at', 'min_role_level']
    ordering = ['menu_group', 'sort_order', 'title']
    
    def get_serializer_class(self):  # type: ignore[override]
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return MenuItemCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MenuItemUpdateSerializer
        return MenuItemSerializer
    
    @extend_schema(
        tags=['Navigation'],
        summary='List Menu Items',
        description='Get list of menu items with filtering options',
        parameters=[
            OpenApiParameter('menu_group', OpenApiTypes.INT, description='Filter by menu group ID'),
            OpenApiParameter('parent', OpenApiTypes.INT, description='Filter by parent ID (use 0 for root items)'),
            OpenApiParameter('is_active', OpenApiTypes.BOOL, description='Filter by active status'),
            OpenApiParameter('target_type', OpenApiTypes.STR, description='Filter by target type'),
            OpenApiParameter('min_role_level', OpenApiTypes.INT, description='Filter by minimum role level'),
            OpenApiParameter('search', OpenApiTypes.STR, description='Search in title, description, URLs'),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Navigation'],
        summary='Create Menu Item',
        description='Create a new menu item (Admin only)'
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Navigation'],
        summary='Track Menu Click',
        description='Track a click on this menu item for analytics'
    )
    @action(detail=True, methods=['post'])
    def track_click(self, request, pk=None):
        """Track menu item click"""
        menu_item = self.get_object()
        
        # Track the click
        tracking = track_menu_click(
            menu_item=menu_item,
            user=request.user if request.user.is_authenticated else None,
            request=request
        )
        
        serializer = MenuClickTrackingSerializer(tracking)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        tags=['Navigation'],
        summary='Get Menu Item Analytics',
        description='Get analytics data for this menu item'
    )
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get analytics for menu item"""
        menu_item = self.get_object()
        
        # Get analytics data
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        clicks = MenuClickTracking.objects.filter(
            menu_item=menu_item,
            clicked_at__gte=start_date
        )
        
        analytics_data = {
            'menu_item_id': menu_item.id,
            'menu_item_title': menu_item.title,
            'click_count': clicks.count(),
            'unique_users': clicks.values('user').distinct().count(),
            'last_clicked': clicks.first().clicked_at if clicks.exists() else None,
            'daily_clicks': self._get_daily_clicks(clicks, days)
        }
        
        return Response(analytics_data, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Navigation'],
        summary='Bulk Update Menu Items',
        description='Update multiple menu items at once'
    )
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update menu items"""
        # Check admin permission
        user_role_level = get_user_role_level(request.user)
        if user_role_level < 70:
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        items_data = request.data.get('items', [])
        if not items_data:
            return Response(
                {'error': 'No items provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_items = []
        errors = []
        
        for item_data in items_data:
            item_id = item_data.get('id')
            if not item_id:
                errors.append({'error': 'Missing item ID', 'data': item_data})
                continue
            
            try:
                item = MenuItem.objects.get(id=item_id)
                serializer = MenuItemUpdateSerializer(item, data=item_data, partial=True)
                
                if serializer.is_valid():
                    serializer.save()
                    updated_items.append(serializer.data)
                else:
                    errors.append({
                        'id': item_id,
                        'errors': serializer.errors
                    })
                    
            except MenuItem.DoesNotExist:
                errors.append({
                    'id': item_id,
                    'error': 'Item not found'
                })
        
        return Response({
            'updated_count': len(updated_items),
            'error_count': len(errors),
            'updated_items': updated_items,
            'errors': errors
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Navigation'],
        summary='Bulk Delete Menu Items',
        description='Delete multiple menu items at once'
    )
    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        """Bulk delete menu items"""
        # Check admin permission
        user_role_level = get_user_role_level(request.user)
        if user_role_level < 70:
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        item_ids = request.data.get('item_ids', [])
        if not item_ids:
            return Response(
                {'error': 'No item IDs provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count = 0
        errors = []
        
        for item_id in item_ids:
            try:
                item = MenuItem.objects.get(id=item_id)
                item_title = item.title
                item.delete()
                deleted_count += 1
            except MenuItem.DoesNotExist:
                errors.append({
                    'id': item_id,
                    'error': 'Item not found'
                })
        
        return Response({
            'deleted_count': deleted_count,
            'error_count': len(errors),
            'errors': errors
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Navigation'],
        summary='Export Menu Items',
        description='Export menu items to JSON or CSV format'
    )
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export menu items"""
        export_format = request.query_params.get('format', 'json')
        group_id = request.query_params.get('group_id')
        
        # Get items to export
        queryset = self.get_queryset()
        if group_id:
            queryset = queryset.filter(menu_group_id=group_id)
        
        if export_format == 'csv':
            return self._export_csv(queryset)
        else:
            return self._export_json(queryset)
    
    def _export_json(self, queryset):
        """Export items as JSON"""
        serializer = MenuItemSerializer(queryset, many=True, context={'request': self.request})
        
        response = HttpResponse(
            json.dumps(serializer.data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="menu_items.json"'
        return response
    
    def _export_csv(self, queryset):
        """Export items as CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="menu_items.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Title', 'Description', 'Group', 'Parent', 'URL Name', 'URL Path',
            'Target Type', 'Icon', 'Sort Order', 'Min Role Level', 'Is Active'
        ])
        
        for item in queryset:
            writer.writerow([
                item.id,
                item.title,
                item.description,
                item.menu_group.name,
                item.parent.title if item.parent else '',
                item.url_name,
                item.url_path,
                item.target_type,
                item.icon,
                item.sort_order,
                item.min_role_level,
                item.is_active
            ])
        
        return response
    
    @extend_schema(
        tags=['Navigation'],
        summary='Import Menu Items',
        description='Import menu items from JSON file'
    )
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def import_items(self, request):
        """Import menu items from file"""
        # Check admin permission
        user_role_level = get_user_role_level(request.user)
        if user_role_level < 70:
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if file_obj.name.endswith('.json'):
                import_data = json.loads(file_obj.read().decode('utf-8'))
            else:
                return Response(
                    {'error': 'Only JSON files are supported'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            created_items = []
            errors = []
            
            for item_data in import_data:
                serializer = MenuItemCreateSerializer(data=item_data)
                
                if serializer.is_valid():
                    item = serializer.save(created_by=request.user)
                    created_items.append(MenuItemSerializer(item).data)
                else:
                    errors.append({
                        'data': item_data,
                        'errors': serializer.errors
                    })
            
            return Response({
                'created_count': len(created_items),
                'error_count': len(errors),
                'created_items': created_items,
                'errors': errors
            }, status=status.HTTP_201_CREATED)
            
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return Response(
                {'error': f'Invalid file format: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _get_daily_clicks(self, clicks, days):
        """Get daily click statistics"""
        daily_data = []
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            day_clicks = clicks.filter(
                clicked_at__date=date
            ).count()
            daily_data.append({
                'date': date,
                'clicks': day_clicks
            })
        return list(reversed(daily_data))
    
    def get_queryset(self):  # type: ignore[override]
        """Filter queryset based on parameters and user permissions"""
        queryset = MenuItem.objects.select_related('menu_group', 'parent')
        
        # Apply filters
        menu_group = self.request.query_params.get('menu_group')  # type: ignore[attr-defined]  # type: ignore[attr-defined]
        if menu_group:
            queryset = queryset.filter(menu_group_id=menu_group)
        
        parent = self.request.query_params.get('parent')  # type: ignore[attr-defined]  # type: ignore[attr-defined]
        if parent is not None:
            if parent == '0':
                queryset = queryset.filter(parent=None)
            else:
                queryset = queryset.filter(parent_id=parent)
        
        is_active = self.request.query_params.get('is_active')  # type: ignore[attr-defined]
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        target_type = self.request.query_params.get('target_type')  # type: ignore[attr-defined]  # type: ignore[attr-defined]
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        
        min_role_level = self.request.query_params.get('min_role_level')  # type: ignore[attr-defined]  # type: ignore[attr-defined]
        if min_role_level:
            queryset = queryset.filter(min_role_level__gte=int(min_role_level))
        
        # Filter by user role level
        user_role_level = get_user_role_level(self.request.user)
        if user_role_level < 70:  # Non-admin users
            queryset = queryset.filter(min_role_level__lte=user_role_level)
        
        return queryset

    def perform_create(self, serializer):
        """Set created_by when creating menu item"""
        serializer.save(created_by=self.request.user)
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Only admin and above can modify
            user_role_level = get_user_role_level(self.request.user)
            if user_role_level < 70:
                self.permission_classes = [permissions.IsAdminUser]
        
        return super().get_permissions()


class MenuItemPermissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing menu item permissions
    """
    queryset = MenuItemPermission.objects.all()
    serializer_class = MenuItemPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        tags=['Navigation'],
        summary='List Menu Item Permissions',
        description='Get list of menu item permissions (Admin only)'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):  # type: ignore[override]
        """Filter by menu item if specified"""
        queryset = MenuItemPermission.objects.select_related('menu_item', 'role')
        
        menu_item = self.request.query_params.get('menu_item')  # type: ignore[attr-defined]
        if menu_item:
            queryset = queryset.filter(menu_item_id=menu_item)
        
        return queryset.order_by('menu_item', 'role')
    
    def get_permissions(self):
        """Only admin can manage permissions"""
        user_role_level = get_user_role_level(self.request.user)
        if user_role_level < 70:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()


class MenuConfigurationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing menu configuration
    """
    queryset = MenuConfiguration.objects.all()
    serializer_class = MenuConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        tags=['Navigation'],
        summary='List Menu Configurations',
        description='Get list of menu configurations with filtering options'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Navigation'],
        summary='Create Menu Configuration',
        description='Create a new menu configuration (Admin only)'
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def get_queryset(self):  # type: ignore[override]
        """Filter queryset based on parameters"""
        queryset = MenuConfiguration.objects.all()
        
        config_type = self.request.query_params.get('config_type')  # type: ignore[attr-defined]
        if config_type:
            queryset = queryset.filter(config_type=config_type)
        
        is_active = self.request.query_params.get('is_active')  # type: ignore[attr-defined]
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('config_type', 'key')
    
    def get_permissions(self):
        """Only admin can manage configurations"""
        user_role_level = get_user_role_level(self.request.user)
        if user_role_level < 70:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()


class MenuAnalyticsView(APIView):
    """
    Get analytics data for navigation menus
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        tags=['Navigation'],
        summary='Get Menu Analytics',
        description='''
        Mendapatkan data analytics untuk menu navigasi.
        
        **Metrics:**
        - Total clicks per menu item
        - Unique users per menu item
        - Click trends over time
        - Most popular menu items
        ''',
        parameters=[
            OpenApiParameter('days', OpenApiTypes.INT, description='Number of days for analysis (default: 30)'),
            OpenApiParameter('menu_group', OpenApiTypes.INT, description='Filter by menu group ID'),
        ]
    )
    def get(self, request):
        """Get navigation analytics"""
        # Check admin permission
        user_role_level = get_user_role_level(request.user)
        if user_role_level < 70:
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = int(request.query_params.get('days', 30))
        menu_group = request.query_params.get('menu_group')
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Base queryset for clicks
        clicks_qs = MenuClickTracking.objects.filter(clicked_at__gte=start_date)
        
        if menu_group:
            clicks_qs = clicks_qs.filter(menu_item__menu_group_id=menu_group)
        
        # Get analytics data
        menu_analytics = clicks_qs.values(
            'menu_item__id',
            'menu_item__title'
        ).annotate(
            click_count=Count('id'),
            unique_users=Count('user', distinct=True)
        ).order_by('-click_count')[:20]  # Top 20
        
        # Get daily trends
        daily_clicks = []
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            day_clicks = clicks_qs.filter(clicked_at__date=date).count()
            daily_clicks.append({
                'date': date,
                'clicks': day_clicks
            })
        
        analytics_data = {
            'popular_items': list(menu_analytics),
            'daily_trends': list(reversed(daily_clicks)),
            'total_clicks': clicks_qs.count(),
            'unique_users': clicks_qs.values('user').distinct().count(),
            'period_days': days
        }
        
        return Response(analytics_data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Navigation'],
    summary='Search Menu Items',
    description='Search menu items by title or description',
    parameters=[
        OpenApiParameter('q', OpenApiTypes.STR, required=True, description='Search query'),
        OpenApiParameter('limit', OpenApiTypes.INT, description='Limit results (default: 10)'),
    ]
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_menu_items(request):
    """Search menu items"""
    query = request.query_params.get('q', '').strip()
    limit = int(request.query_params.get('limit', 10))
    
    if not query:
        return Response([], status=status.HTTP_200_OK)
    
    # Get user's role level for filtering
    user_role_level = get_user_role_level(request.user)
    
    # Search menu items
    menu_items = MenuItem.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query),
        is_active=True,
        min_role_level__lte=user_role_level
    ).select_related('menu_group')[:limit]
    
    # Filter by visibility
    visible_items = [
        item for item in menu_items 
        if item.is_visible_to_user(request.user)
    ]
    
    serializer = MenuItemSerializer(
        visible_items, 
        many=True, 
        context={'request': request}
    )
    
    return Response(serializer.data, status=status.HTTP_200_OK)