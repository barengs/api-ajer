#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/Users/ROFI/Develop/proyek/hybridLms')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

# Now we can import Django models
from django.contrib.auth import get_user_model
from recommendations.models import RecommendationSettings
from recommendations.services import RecommendationService

User = get_user_model()

def test_recommendation_system():
    print("Testing recommendation system...")
    
    # Test getting settings
    try:
        settings = RecommendationSettings.get_settings()
        print(f"✓ Recommendation settings loaded: {settings.default_algorithm}")
    except Exception as e:
        print(f"✗ Failed to load recommendation settings: {e}")
        return False
    
    # Test creating a recommendation service
    try:
        service = RecommendationService()
        print("✓ Recommendation service created successfully")
    except Exception as e:
        print(f"✗ Failed to create recommendation service: {e}")
        return False
    
    print("All tests passed!")
    return True

if __name__ == "__main__":
    test_recommendation_system()