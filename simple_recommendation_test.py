import os
import sys
import django

# Setup Django environment
sys.path.append('/Users/ROFI/Develop/proyek/hybridLms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

# Import Django models and services
from django.contrib.auth import get_user_model
from recommendations.models import RecommendationSettings
from recommendations.services import RecommendationService

def test_recommendation_system():
    print("Testing recommendation system...")
    
    # Test 1: Check if we can access recommendation settings
    try:
        settings = RecommendationSettings.get_settings()
        print(f"✓ Recommendation settings loaded. Default algorithm: {settings.default_algorithm}")
    except Exception as e:
        print(f"✗ Failed to load recommendation settings: {e}")
        return False
    
    # Test 2: Check if we can create recommendation service
    try:
        service = RecommendationService()
        print("✓ Recommendation service created successfully")
    except Exception as e:
        print(f"✗ Failed to create recommendation service: {e}")
        return False
    
    print("All basic tests passed!")
    return True

if __name__ == "__main__":
    test_recommendation_system()