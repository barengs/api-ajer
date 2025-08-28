#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append('/Users/ROFI/Develop/proyek/hybridLms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

def test_recommendations_fix():
    print("Testing recommendations fix...")
    
    # Test 1: Import models
    try:
        from recommendations.models import RecommendationSettings
        print("✓ Recommendation models imported successfully")
    except Exception as e:
        print(f"✗ Failed to import recommendation models: {e}")
        return False
    
    # Test 2: Access settings
    try:
        settings = RecommendationSettings.get_settings()
        print(f"✓ Recommendation settings accessed successfully: {settings.default_algorithm}")
    except Exception as e:
        print(f"✗ Failed to access recommendation settings: {e}")
        return False
    
    # Test 3: Create service
    try:
        from recommendations.services import RecommendationService
        service = RecommendationService()
        print("✓ Recommendation service created successfully")
    except Exception as e:
        print(f"✗ Failed to create recommendation service: {e}")
        return False
    
    print("All tests passed! The fix should resolve the migration issue.")
    return True

if __name__ == "__main__":
    test_recommendations_fix()