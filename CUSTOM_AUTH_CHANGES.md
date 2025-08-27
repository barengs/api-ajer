# Custom User Authentication with Additional User Data

## Overview

This document describes the changes made to implement a custom user authentication system that includes `full_name`, `role`, and `profile_image` data during login.

## Changes Made

### 1. Updated Custom Token Serializer

**File**: `accounts/serializers.py`

- Modified `CustomTokenObtainPairSerializer` to include additional user data in JWT token claims
- Added `profile_image` to the token payload
- Used Django's `static()` function to provide a default profile image when none is set

### 2. Enhanced Login View

**File**: `accounts/views.py`

- Updated `CustomTokenObtainPairView` to include detailed user information in the login response
- Added user data object with `id`, `email`, `full_name`, `role`, and `profile_image`
- Maintained backward compatibility with existing token structure

### 3. Updated Registration View

**File**: `accounts/views.py`

- Enhanced `UserRegistrationView` to include user data in the registration response
- Consistent user data structure between login and registration responses

## New Response Structure

### Login Response

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "student",
    "profile_image": "/media/profiles/image.jpg"
  }
}
```

### Token Claims

The JWT access token now includes the following custom claims:

- `email`: User's email address
- `role`: User's role (student, instructor, admin)
- `full_name`: User's full name or username
- `profile_image`: URL to user's profile image or default image

## Usage

### Frontend Integration

Frontend applications can now access user data immediately after login without additional API calls:

```javascript
// Login request
const response = await fetch("/api/v1/auth/login/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    email: "user@example.com",
    password: "password123",
  }),
});

const data = await response.json();

// Access user data directly from login response
const { id, email, full_name, role, profile_image } = data.user;

// Store user data in application state
storeUserData({
  id,
  email,
  fullName: full_name,
  role,
  profileImage: profile_image,
});
```

### Token Usage

The JWT token can also be decoded to access user information:

```javascript
// Decode JWT token to access user claims
const tokenPayload = JSON.parse(atob(token.split(".")[1]));
const { email, role, full_name, profile_image } = tokenPayload;
```

## Testing

### Management Command

Test the authentication functionality using the Django management command:

```bash
python manage.py test_auth
```

### API Testing

Test the login API endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "password": "password123"
     }'
```

## Benefits

1. **Reduced API Calls**: Frontend applications no longer need to make additional requests to get user data after login
2. **Consistent Data Structure**: User data is consistently structured across login and registration responses
3. **Enhanced User Experience**: Faster access to user information improves application responsiveness
4. **Token-Based Access**: User data is available directly from the JWT token for stateless applications

## Backward Compatibility

All changes maintain backward compatibility with existing implementations:

- Existing token structure is preserved
- Additional user data is provided without removing existing fields
- Applications that only use the token can continue to function as before
