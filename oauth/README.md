# OAuth App

This Django app handles all social authentication functionality for the Hybrid LMS platform.

## Overview

The OAuth app provides a centralized location for managing social authentication providers, including Google OAuth, Facebook, GitHub, and others that may be added in the future.

## Current Features

### Google OAuth Login/Register

- **Endpoint**: `POST /api/v1/oauth/google/`
- **Description**: Allows users to authenticate using their Google accounts
- **Request**: Requires a Google OAuth access token
- **Response**: Returns JWT tokens and user data

## Structure

```
oauth/
├── __init__.py
├── admin.py
├── apps.py
├── migrations/
├── models.py
├── pipeline.py
├── tests.py
├── urls.py
└── views.py
```

## Implementation Details

### Views

The `views.py` file contains the `google_oauth_login` function which:

1. Accepts a Google OAuth access token
2. Authenticates the user with Google's OAuth backend
3. Creates a new user if one doesn't exist
4. Generates JWT tokens for the authenticated user
5. Returns user data and tokens in the response

### Pipeline

The `pipeline.py` file contains the `save_profile` function which:

1. Creates a user profile if one doesn't exist
2. Updates user information with data from Google
3. Saves the profile with any available Google data

### URLs

The `urls.py` file defines the URL patterns for OAuth endpoints:

- `/google/` - Google OAuth login/register endpoint

## Configuration

The OAuth app is configured through the main Django settings:

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'oauth',
    'social_django',
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'accounts.backends.CaseInsensitiveAuth',
    'social_core.backends.google.GoogleOAuth2',
)

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'oauth.pipeline.save_profile',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)
```

## Future Extensions

This app can be easily extended to support additional OAuth providers by:

1. Adding the provider's backend to `AUTHENTICATION_BACKENDS`
2. Adding the provider's configuration to settings
3. Creating provider-specific views if needed
4. Updating the pipeline if special handling is required

## Testing

To test the OAuth functionality:

1. Ensure the Google OAuth credentials are properly configured
2. Start the Django development server
3. Send a POST request to `/api/v1/oauth/google/` with a valid access token
4. Verify that the response contains the expected JWT tokens and user data
