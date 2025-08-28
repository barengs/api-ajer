from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import json
from typing import Any, Dict, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from rest_framework.response import Response
    from django.http import HttpResponse

from .models import MenuGroup, MenuItem, MenuItemPermission, MenuClickTracking, MenuConfiguration
from accounts.models import User


class NavigationModelTests(TestCase):
    """Test cases for navigation models"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.superuser = User.objects.create_superuser(  # type: ignore
            email='admin@example.com',
            username='admin',
            password='testpass123'
        )
        self.instructor = User.objects.create_user(  # type: ignore
            email='instructor@example.com',
            username='instructor',
            password='testpass123',
            role='instructor'
        )
        self.student = User.objects.create_user(  # type: ignore
            email='student@example.com',
            username='student',
            password='testpass123',
            role='student'
        )
        
        # Create menu group
        self.menu_group = MenuGroup.objects.create(
            name='Main Navigation',
            slug='main-nav',
            description='Main navigation menu',
            group_type=MenuGroup.GroupType.MAIN,
            min_role_level=10,
            created_by=self.superuser
        )
        
        # Create menu items
        self.dashboard_item = MenuItem.objects.create(
            menu_group=self.menu_group,
            title='Dashboard',
            description='User dashboard',
            icon='fas fa-tachometer-alt',
            target_type=MenuItem.TargetType.INTERNAL,
            url_name='accounts:user_dashboard',
            min_role_level=10,
            sort_order=0,
            created_by=self.superuser
        )
        
        self.admin_item = MenuItem.objects.create(
            menu_group=self.menu_group,
            title='Admin Panel',
            description='Administrative functions',
            icon='fas fa-cogs',
            target_type=MenuItem.TargetType.INTERNAL,
            url_name='admin:index',
            min_role_level=70,
            sort_order=1,
            created_by=self.superuser
        )
        
        self.external_item = MenuItem.objects.create(
            menu_group=self.menu_group,
            title='External Link',
            description='External website',
            icon='fas fa-external-link-alt',
            target_type=MenuItem.TargetType.EXTERNAL,
            url_path='https://example.com',
            min_role_level=10,
            sort_order=2,
            opens_in_new_window=True,
            created_by=self.superuser
        )
    
    def test_get_navigation_tree_authenticated(self):
        """Test getting navigation tree for authenticated user"""
        # Use Django's login method for TestCase
        self.client.login(email='student@example.com', password='testpass123')
        
        response = self.client.get(reverse('navigation:navigation_tree'))
        self.assertEqual(response.status_code, 200)
        
        # Handle the response content - check if it has content attribute
        if hasattr(response, 'content'):
            content = response.content.decode('utf-8')
            try:
                data = json.loads(content)
                self.assertIn('menu_groups', data)
                
                # Student should see menu groups with accessible items only
                menu_groups = data['menu_groups']
                self.assertGreater(len(menu_groups), 0)
                
                # Find our test group
                test_group = None
                for group in menu_groups:
                    if group['name'] == 'Main Navigation':
                        test_group = group
                        break
                
                self.assertIsNotNone(test_group)
                if test_group is not None:  # Add type check
                    # Should have dashboard item but not admin item
                    items = test_group['items']
                    dashboard_items = [item for item in items if item['title'] == 'Dashboard']
                    admin_items = [item for item in items if item['title'] == 'Admin Panel']
                    
                    self.assertEqual(len(dashboard_items), 1)
                    self.assertEqual(len(admin_items), 0)
            except json.JSONDecodeError:
                self.fail("Response is not valid JSON")
        else:
            self.fail("Response does not have content attribute")

    def test_menu_group_creation(self):
        """Test menu group creation"""
        self.assertEqual(self.menu_group.name, 'Main Navigation')
        self.assertEqual(self.menu_group.slug, 'main-nav')
        self.assertEqual(self.menu_group.group_type, MenuGroup.GroupType.MAIN)
        self.assertEqual(self.menu_group.min_role_level, 10)
        self.assertEqual(str(self.menu_group), 'Main Navigation')
    
    def test_menu_item_creation(self):
        """Test menu item creation"""
        self.assertEqual(self.dashboard_item.title, 'Dashboard')
        self.assertEqual(self.dashboard_item.menu_group, self.menu_group)
        self.assertEqual(self.dashboard_item.target_type, MenuItem.TargetType.INTERNAL)
        self.assertEqual(self.dashboard_item.min_role_level, 10)
        self.assertEqual(str(self.dashboard_item), 'Main Navigation > Dashboard')
    
    def test_menu_item_get_url(self):
        """Test menu item URL resolution"""
        # Internal link with URL name
        self.assertEqual(self.dashboard_item.get_url(), '/dashboard/')
        
        # External link
        self.assertEqual(self.external_item.get_url(), 'https://example.com')
        
        # Item without URL
        no_url_item = MenuItem.objects.create(
            menu_group=self.menu_group,
            title='No URL Item',
            min_role_level=10,
            created_by=self.superuser
        )
        self.assertEqual(no_url_item.get_url(), '#')
    
    def test_menu_item_visibility(self):
        """Test menu item visibility based on user roles"""
        # Student should see dashboard but not admin panel
        self.assertTrue(self.dashboard_item.is_visible_to_user(self.student))
        self.assertFalse(self.admin_item.is_visible_to_user(self.student))
        
        # Instructor should see dashboard but not admin panel
        self.assertTrue(self.dashboard_item.is_visible_to_user(self.instructor))
        self.assertFalse(self.admin_item.is_visible_to_user(self.instructor))
        
        # Admin should see both
        self.assertTrue(self.dashboard_item.is_visible_to_user(self.superuser))
        self.assertTrue(self.admin_item.is_visible_to_user(self.superuser))
    
    def test_menu_group_get_items_for_user(self):
        """Test getting menu items for specific user"""
        # Student should only get dashboard item
        student_items = self.menu_group.get_items_for_user(self.student)
        self.assertEqual(student_items.count(), 2)  # dashboard + external
        
        # Admin should get all items
        admin_items = self.menu_group.get_items_for_user(self.superuser)
        self.assertEqual(admin_items.count(), 3)
    
    def test_menu_item_level(self):
        """Test menu item hierarchy level calculation"""
        # Root item
        self.assertEqual(self.dashboard_item.level, 0)
        
        # Child item
        child_item = MenuItem.objects.create(
            menu_group=self.menu_group,
            parent=self.dashboard_item,
            title='Child Item',
            min_role_level=10,
            created_by=self.superuser
        )
        self.assertEqual(child_item.level, 1)
        
        # Grandchild item
        grandchild_item = MenuItem.objects.create(
            menu_group=self.menu_group,
            parent=child_item,
            title='Grandchild Item',
            min_role_level=10,
            created_by=self.superuser
        )
        self.assertEqual(grandchild_item.level, 2)
    
    def test_menu_click_tracking(self):
        """Test menu click tracking"""
        # Create click tracking
        click = MenuClickTracking.objects.create(
            menu_item=self.dashboard_item,
            user=self.student,
            ip_address='127.0.0.1',
            user_agent='Test Browser',
            referrer='https://example.com'
        )
        
        self.assertEqual(click.menu_item, self.dashboard_item)
        self.assertEqual(click.user, self.student)
        self.assertEqual(click.ip_address, '127.0.0.1')
        self.assertIn('Test Browser', click.user_agent)
        self.assertIn('example.com', click.referrer)
        self.assertIn('Dashboard clicked by', str(click))
    
    def test_menu_configuration(self):
        """Test menu configuration model"""
        config = MenuConfiguration.objects.create(
            key='theme_color',
            config_type=MenuConfiguration.ConfigType.THEME,
            description='Primary theme color',
            value='{"primary": "#007bff", "secondary": "#6c757d"}',
            is_active=True
        )
        
        self.assertEqual(config.key, 'theme_color')
        self.assertEqual(config.config_type, MenuConfiguration.ConfigType.THEME)
        self.assertTrue(config.is_active)
        self.assertEqual(str(config), 'theme_color (theme)')
        
        # Test value parsing
        parsed_value = config.get_value()
        # Handle type checking issue by checking type before accessing
        if isinstance(parsed_value, dict):
            self.assertEqual(parsed_value['primary'], '#007bff')  # type: ignore
        else:
            self.fail("Expected parsed_value to be a dict")
        
        # Test string value
        string_config = MenuConfiguration.objects.create(
            key='site_name',
            config_type=MenuConfiguration.ConfigType.BEHAVIOR,
            value='My Learning Platform'
        )
        self.assertEqual(string_config.get_value(), 'My Learning Platform')

class NavigationAPITests(APITestCase):
    """Test cases for navigation API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Use APIClient for API tests
        self.client = APIClient()
        
        # Create users
        self.superuser = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='testpass123'
        )
        self.instructor = User.objects.create_user(
            email='instructor@example.com',
            username='instructor',
            password='testpass123',
            role='instructor'
        )
        self.student = User.objects.create_user(
            email='student@example.com',
            username='student',
            password='testpass123',
            role='student'
        )
        
        # Create menu group
        self.menu_group = MenuGroup.objects.create(
            name='Main Navigation',
            slug='main-nav',
            description='Main navigation menu',
            group_type=MenuGroup.GroupType.MAIN,
            min_role_level=10,
            created_by=self.superuser
        )
        
        # Create menu items
        self.dashboard_item = MenuItem.objects.create(
            menu_group=self.menu_group,
            title='Dashboard',
            description='User dashboard',
            icon='fas fa-tachometer-alt',
            target_type=MenuItem.TargetType.INTERNAL,
            url_name='dashboard',
            min_role_level=10,
            sort_order=0,
            created_by=self.superuser
        )
        
        self.admin_item = MenuItem.objects.create(
            menu_group=self.menu_group,
            title='Admin Panel',
            description='Administrative functions',
            icon='fas fa-cogs',
            target_type=MenuItem.TargetType.INTERNAL,
            url_name='admin:index',
            min_role_level=70,
            sort_order=1,
            created_by=self.superuser
        )
        
        # Create menu configuration
        self.config = MenuConfiguration.objects.create(
            key='theme_settings',
            config_type=MenuConfiguration.ConfigType.THEME,
            description='Theme configuration',
            value='{"primary_color": "#007bff"}',
            is_active=True
        )
    
    def test_get_navigation_tree_authenticated(self):
        """Test getting navigation tree for authenticated user"""
        self.client.force_authenticate(user=self.student)  # type: ignore
        
        response = self.client.get(reverse('navigation:navigation_tree'))  # type: ignore
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertIn('menu_groups', response.data)  # type: ignore
        
        # Student should see menu groups with accessible items only
        menu_groups = response.data['menu_groups']  # type: ignore
        self.assertGreater(len(menu_groups), 0)
        
        # Find our test group
        test_group = None
        for group in menu_groups:
            if group['name'] == 'Main Navigation':
                test_group = group
                break
        
        self.assertIsNotNone(test_group)
        # Should have dashboard item but not admin item
        items = test_group['items']  # type: ignore
        dashboard_items = [item for item in items if item['title'] == 'Dashboard']
        admin_items = [item for item in items if item['title'] == 'Admin Panel']
        
        self.assertEqual(len(dashboard_items), 1)
        self.assertEqual(len(admin_items), 0)
    
    def test_get_navigation_tree_unauthenticated(self):
        """Test getting navigation tree for unauthenticated user"""
        response = self.client.get(reverse('navigation:navigation_tree'))  # type: ignore
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        
        # Unauthenticated user should see only public items
        menu_groups = response.data['menu_groups']  # type: ignore
        # Implementation depends on your authentication requirements
    
    def test_list_menu_groups(self):
        """Test listing menu groups"""
        self.client.force_authenticate(user=self.superuser)  # type: ignore
        
        response = self.client.get(reverse('navigation:menugroup-list'))  # type: ignore
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertGreater(len(response.data), 0)  # type: ignore
    
    def test_create_menu_group(self):
        """Test creating menu group"""
        self.client.force_authenticate(user=self.superuser)  # type: ignore
        
        data = {
            'name': 'Footer Navigation',
            'slug': 'footer-nav',
            'description': 'Footer navigation menu',
            'group_type': 'main',
            'min_role_level': 10
        }
        
        response = self.client.post(reverse('navigation:menugroup-list'), data)  # type: ignore
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        self.assertEqual(response.data['name'], 'Footer Navigation')  # type: ignore
    
    def test_list_menu_items(self):
        """Test listing menu items"""
        self.client.force_authenticate(user=self.superuser)  # type: ignore
        
        response = self.client.get(reverse('navigation:menuitem-list'))  # type: ignore
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertGreater(len(response.data), 0)  # type: ignore
    
    def test_create_menu_item(self):
        """Test creating menu item"""
        self.client.force_authenticate(user=self.superuser)  # type: ignore
        
        data = {
            'menu_group': self.menu_group.id,  # type: ignore
            'title': 'New Item',
            'description': 'A new menu item',
            'target_type': 'internal',
            'url_name': 'courses:list',
            'min_role_level': 10,
            'sort_order': 3
        }
        
        response = self.client.post(reverse('navigation:menuitem-list'), data)  # type: ignore
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        self.assertEqual(response.data['title'], 'New Item')  # type: ignore
    
    def test_bulk_update_menu_items(self):
        """Test bulk updating menu items"""
        self.client.force_authenticate(user=self.superuser)  # type: ignore
        
        data = {
            'items': [
                {
                    'id': self.dashboard_item.id,  # type: ignore
                    'title': 'Updated Dashboard',
                    'sort_order': 5
                },
                {
                    'id': self.admin_item.id,  # type: ignore
                    'description': 'Updated admin panel description'
                }
            ]
        }
        
        response = self.client.post(  # type: ignore
            reverse('navigation:menuitem-bulk-update'), 
            data, 
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(response.data['updated_count'], 2)  # type: ignore
        
        # Verify updates
        updated_dashboard = MenuItem.objects.get(id=self.dashboard_item.id)  # type: ignore
        self.assertEqual(updated_dashboard.title, 'Updated Dashboard')
        self.assertEqual(updated_dashboard.sort_order, 5)
    
    def test_menu_item_analytics(self):
        """Test menu item analytics endpoint"""
        self.client.force_authenticate(user=self.superuser)  # type: ignore
        
        # Create some click tracking data
        for i in range(5):
            MenuClickTracking.objects.create(
                menu_item=self.dashboard_item,
                user=self.student if i % 2 == 0 else self.instructor,
                ip_address=f'192.168.1.{i}',
                clicked_at=timezone.now() - timedelta(days=i)
            )
        
        response = self.client.get(  # type: ignore
            reverse('navigation:menuitem-analytics', kwargs={'pk': self.dashboard_item.id})  # type: ignore
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertEqual(response.data['menu_item_id'], self.dashboard_item.id)  # type: ignore
        self.assertEqual(response.data['click_count'], 5)  # type: ignore
        self.assertEqual(response.data['unique_users'], 2)  # type: ignore
    
    def test_menu_group_validation(self):
        """Test menu group structure validation"""
        self.client.force_authenticate(user=self.superuser)  # type: ignore
        
        response = self.client.get(  # type: ignore
            reverse('navigation:menugroup-validate-structure', kwargs={'pk': self.menu_group.id})  # type: ignore
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertIn('is_valid', response.data)  # type: ignore
    
    def test_list_menu_configurations(self):
        """Test listing menu configurations"""
        self.client.force_authenticate(user=self.superuser)  # type: ignore
        
        response = self.client.get(reverse('navigation:menuconfiguration-list'))  # type: ignore
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertGreater(len(response.data), 0)  # type: ignore
    
    def test_create_menu_configuration(self):
        """Test creating menu configuration"""
        self.client.force_authenticate(user=self.superuser)  # type: ignore
        
        data = {
            'key': 'api_settings',
            'config_type': 'api',
            'description': 'API configuration',
            'value': '{"rate_limit": 1000}',
            'is_active': True
        }
        
        response = self.client.post(reverse('navigation:menuconfiguration-list'), data)  # type: ignore
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # type: ignore
        self.assertEqual(response.data['key'], 'api_settings')  # type: ignore
    
    def test_search_menu_items(self):
        """Test searching menu items"""
        self.client.force_authenticate(user=self.superuser)  # type: ignore
        
        response = self.client.get(  # type: ignore
            reverse('navigation:search_menu_items'),
            {'q': 'Dashboard'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type: ignore
        self.assertGreater(len(response.data), 0)  # type: ignore
        
        # Check that results contain the searched item
        found_items = [item for item in response.data if item['title'] == 'Dashboard']  # type: ignore
        self.assertEqual(len(found_items), 1)


class NavigationPermissionTests(APITestCase):
    """Test cases for navigation permissions"""
    
    def setUp(self):
        """Set up test data"""
        # Use APIClient for API tests
        self.client = APIClient()
        
        # Create users
        self.superuser = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='testpass123'
        )
        self.instructor = User.objects.create_user(
            email='instructor@example.com',
            username='instructor',
            password='testpass123',
            role='instructor'
        )
        self.student = User.objects.create_user(
            email='student@example.com',
            username='student',
            password='testpass123',
            role='student'
        )
        
        # Create menu group
        self.menu_group = MenuGroup.objects.create(
            name='Admin Navigation',
            slug='admin-nav',
            group_type=MenuGroup.GroupType.ADMIN,
            min_role_level=70,
            created_by=self.superuser
        )
        
        # Create menu item
        self.admin_item = MenuItem.objects.create(
            menu_group=self.menu_group,
            title='Admin Only Item',
            target_type=MenuItem.TargetType.INTERNAL,
            url_name='admin:index',
            min_role_level=70,
            created_by=self.superuser
        )
    
    def test_student_cannot_create_menu_group(self):
        """Test that students cannot create menu groups"""
        self.client.force_authenticate(user=self.student)  # type: ignore
        
        data = {
            'name': 'Student Menu',
            'slug': 'student-menu',
            'group_type': 'main',
            'min_role_level': 10
        }
        
        response = self.client.post(reverse('navigation:menugroup-list'), data)  # type: ignore
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # type: ignore
    
    def test_instructor_cannot_create_menu_group(self):
        """Test that instructors cannot create menu groups"""
        self.client.force_authenticate(user=self.instructor)  # type: ignore
        
        data = {
            'name': 'Instructor Menu',
            'slug': 'instructor-menu',
            'group_type': 'main',
            'min_role_level': 10
        }
        
        response = self.client.post(reverse('navigation:menugroup-list'), data)  # type: ignore
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # type: ignore
    
    def test_student_cannot_access_admin_menu_items(self):
        """Test that students cannot access admin menu items"""
        self.client.force_authenticate(user=self.student)  # type: ignore
        
        # Try to get the admin menu item directly
        response = self.client.get(  # type: ignore
            reverse('navigation:menuitem-detail', kwargs={'pk': self.admin_item.id})  # type: ignore
        )
        # Should either be 404 (not found) or not include sensitive data
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])  # type: ignore
    
    def test_student_cannot_update_menu_item(self):
        """Test that students cannot update menu items"""
        self.client.force_authenticate(user=self.student)  # type: ignore
        
        data = {'title': 'Hacked Title'}
        response = self.client.patch(  # type: ignore
            reverse('navigation:menuitem-detail', kwargs={'pk': self.admin_item.id}),  # type: ignore
            data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # type: ignore


class NavigationUtilityTests(TestCase):
    """Test cases for navigation utility functions"""
    
    def setUp(self):
        """Set up test data"""
        self.superuser = User.objects.create_superuser(  # type: ignore
            email='admin@example.com',
            username='admin',
            password='testpass123'
        )
        
        # Create menu group
        self.menu_group = MenuGroup.objects.create(
            name='Test Navigation',
            slug='test-nav',
            min_role_level=10,
            created_by=self.superuser
        )
        
        # Create menu items with hierarchy
        self.root_item = MenuItem.objects.create(
            menu_group=self.menu_group,
            title='Root Item',
            min_role_level=10,
            created_by=self.superuser
        )
        
        self.child_item = MenuItem.objects.create(
            menu_group=self.menu_group,
            parent=self.root_item,
            title='Child Item',
            min_role_level=10,
            created_by=self.superuser
        )
        
        self.grandchild_item = MenuItem.objects.create(
            menu_group=self.menu_group,
            parent=self.child_item,
            title='Grandchild Item',
            min_role_level=10,
            created_by=self.superuser
        )
    
    def test_menu_structure_validation_no_circular_reference(self):
        """Test menu structure validation with no circular references"""
        from navigation.utils import validate_menu_structure
        
        result = validate_menu_structure(self.menu_group)
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['issues']), 0)
    
    def test_menu_structure_validation_circular_reference(self):
        """Test menu structure validation with circular references"""
        from navigation.utils import validate_menu_structure
        
        # Create circular reference
        self.root_item.parent = self.grandchild_item
        self.root_item.save()
        
        result = validate_menu_structure(self.menu_group)
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['issues']), 0)
        self.assertIn('Circular reference', result['issues'][0])
    
    def test_menu_export_structure(self):
        """Test menu structure export"""
        from navigation.utils import export_menu_structure
        
        export_data = export_menu_structure(self.menu_group)
        
        self.assertEqual(export_data['menu_group']['name'], 'Test Navigation')
        self.assertEqual(len(export_data['items']), 1)  # Only root items
        self.assertEqual(export_data['items'][0]['title'], 'Root Item')
        self.assertEqual(len(export_data['items'][0]['children']), 1)
        self.assertEqual(export_data['items'][0]['children'][0]['title'], 'Child Item')
    
    def test_get_user_role_level(self):
        """Test user role level utility function"""
        from navigation.utils import get_user_role_level
        
        # Test superuser
        self.assertEqual(get_user_role_level(self.superuser), 100)
        
        # Test unauthenticated user
        self.assertEqual(get_user_role_level(None), 10)
