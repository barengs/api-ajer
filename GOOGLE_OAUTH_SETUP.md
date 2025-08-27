# Google OAuth Integration Setup

## Overview

This document explains how to set up Google OAuth authentication for the Hybrid LMS application. This feature allows users to log in or register using their Google accounts.

## Prerequisites

1. Google Cloud Platform account
2. Google OAuth 2.0 Client ID and Client Secret
3. Properly configured Django settings

## Setup Instructions

### 1. Create Google OAuth Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth client ID"
5. Select "Web application" as the application type
6. Add the following authorized redirect URIs:
   - `http://localhost:8000/api/v1/auth/oauth/complete/google-oauth2/` (for development)
   - `http://127.0.0.1:8000/api/v1/auth/oauth/complete/google-oauth2/` (for development)
   - Add your production URLs as needed
7. Save and note the Client ID and Client Secret

### 2. Configure Environment Variables

Add the following to your `.env` file:

```env
GOOGLE_OAUTH2_KEY=your-google-client-id
GOOGLE_OAUTH2_SECRET=your-google-client-secret
```

### 3. Install Required Packages

Make sure the following packages are in your `requirements.txt`:

```
social-auth-app-django==5.4.0
```

Install with:

```bash
pip install -r requirements.txt
```

### 4. Update Django Settings

The following settings should already be configured in `settings.py`:

```python
INSTALLED_APPS = [
    # ... other apps
    'social_django',
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'accounts.backends.CaseInsensitiveAuth',
    'social_core.backends.google.GoogleOAuth2',
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('GOOGLE_OAUTH2_KEY', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('GOOGLE_OAUTH2_SECRET', default='')

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'accounts.pipeline.save_profile',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
```

### 5. URL Configuration

The following URLs should be included in your main `urls.py`:

```python
urlpatterns = [
    # ... other URLs
    path('api/v1/auth/oauth/', include('social_django.urls', namespace='social')),
]
```

And in `accounts/urls.py`:

```python
urlpatterns = [
    # ... other URLs
    path('google/', views.google_oauth_login, name='google_oauth_login'),
]
```

## API Endpoints

### Google OAuth Login/Register

- **URL**: `POST /api/v1/auth/google/`
- **Description**: Authenticate or register a user using Google OAuth token
- **Request Body**:
  ```json
  {
    "access_token": "google_oauth_access_token"
  }
  ```
- **Response**:
  ```json
  {
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "student",
      "profile_image": "/media/profiles/image.jpg"
    },
    "is_new_user": false
  }
  ```

## Frontend Integration

To integrate Google OAuth in your frontend application:

1. Load the Google Platform Library:

   ```html
   <script src="https://accounts.google.com/gsi/client" async defer></script>
   ```

2. Add a Google Sign-In button:

   ```html
   <div
     id="g_id_onload"
     data-client_id="your-google-client-id"
     data-callback="handleCredentialResponse"
   ></div>
   <div class="g_id_signin"></div>
   ```

3. Handle the credential response:
   ```javascript
   function handleCredentialResponse(response) {
     // Send the access token to your backend
     fetch("/api/v1/auth/google/", {
       method: "POST",
       headers: {
         "Content-Type": "application/json",
       },
       body: JSON.stringify({
         access_token: response.credential,
       }),
     })
       .then((response) => response.json())
       .then((data) => {
         // Handle successful authentication
         // Store JWT tokens and user data
       })
       .catch((error) => {
         // Handle error
       });
   }
   ```

## Testing

To test the Google OAuth integration:

1. Make sure your Google OAuth credentials are properly configured
2. Start your Django development server
3. Use the Google Sign-In button to authenticate
4. Check that the user is properly created or authenticated
5. Verify that JWT tokens are returned correctly

## Troubleshooting

### Common Issues

1. **Invalid Client ID/Secret**: Double-check your Google OAuth credentials in the `.env` file
2. **Redirect URI Mismatch**: Ensure the redirect URIs in Google Cloud Console match your application URLs
3. **CORS Issues**: Make sure your frontend domain is added to `CORS_ALLOWED_ORIGINS` in settings

### Debugging Tips

1. Enable Django debug mode to see detailed error messages
2. Check the Django logs for authentication errors
3. Use Django admin to inspect created users and their profiles
