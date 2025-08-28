import os
import sys
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from role_management.models import RoleDefinition, UserRoleAssignment

User = get_user_model()

# Create a simple test
class DebugTest(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123'
        )
        self.instructor_role = RoleDefinition.objects.create(
            name=RoleDefinition.RoleType.INSTRUCTOR,
            display_name='Instructor',
            hierarchy_level=50
        )
    
    def test_debug(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('role_management:user-roles', kwargs={'user_id': self.regular_user.id})
        
        data = {
            'role_id': self.instructor_role.pk,
            'reason': 'API test assignment'
        }
        print(f"Sending data: {data}")
        print(f"To URL: {url}")
        response = self.client.post(url, data)
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")

# Run the test
if __name__ == '__main__':
    import unittest
    suite = unittest.TestSuite()
    suite.addTest(DebugTest('test_debug'))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)