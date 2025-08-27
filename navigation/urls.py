from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'groups', views.MenuGroupViewSet, basename='menugroup')
router.register(r'items', views.MenuItemViewSet, basename='menuitem')
router.register(r'permissions', views.MenuItemPermissionViewSet, basename='menuitempermlssion')
router.register(r'configurations', views.MenuConfigurationViewSet, basename='menuconfiguration')

app_name = 'navigation'

urlpatterns = [
    # Navigation tree and main endpoints
    path('tree/', views.NavigationTreeView.as_view(), name='navigation_tree'),
    path('analytics/', views.MenuAnalyticsView.as_view(), name='menu_analytics'),
    
    # Utility endpoints
    path('search/', views.search_menu_items, name='search_menu_items'),
    
    # Include router URLs
    path('', include(router.urls)),
]