"""
Tests for the OAuth app
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


class OAuthTestCase(TestCase):
    """Test cases for OAuth functionality"""
    
    def setUp(self):
        """Set up test dependencies"""
        self.client = APIClient()
        
    def test_google_oauth_url_exists(self):
        """Test that the Google OAuth URL is properly configured"""
        url = reverse('google_oauth_login')
        self.assertEqual(url, '/api/v1/oauth/google/')
        
    def test_google_oauth_endpoint_requires_post(self):
        """Test that the Google OAuth endpoint only accepts POST requests"""
        url = reverse('google_oauth_login')
        response = self.client.get(url)
        # Should return method not allowed or bad request
        self.assertIn(response.status_code, [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_400_BAD_REQUEST])
        
    def test_google_oauth_missing_token(self):
        """Test that the Google OAuth endpoint returns error for missing token"""
        url = reverse('google_oauth_login')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)