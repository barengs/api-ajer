# Hybrid LMS API - Testing Guide

This guide provides comprehensive testing instructions and examples for all API endpoints.

## Base URL

```
Local Development: http://localhost:8000/api/v1
Production: https://your-domain.com/api/v1
```

## Authentication

### Register User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "username": "student1",
    "password": "securepassword123",
    "full_name": "John Student",
    "role": "student"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "securepassword123"
  }'
```

Response:

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "student@example.com",
    "username": "student1",
    "role": "student"
  }
}
```

## Course Management

### List Courses

```bash
curl -X GET http://localhost:8000/api/v1/courses/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create Course (Instructor)

```bash
curl -X POST http://localhost:8000/api/v1/courses/create/ \
  -H "Authorization: Bearer INSTRUCTOR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python Programming Basics",
    "description": "Learn Python from scratch",
    "course_type": "self_paced",
    "category": 1,
    "price": 99.99,
    "is_free": false,
    "level": "beginner"
  }'
```

### Enroll in Course

```bash
curl -X POST http://localhost:8000/api/v1/courses/1/enroll/ \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

### Course Search

```bash
curl -X GET "http://localhost:8000/api/v1/courses/?search=python&level=beginner&is_free=false" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Lesson Management

### Get Course Lessons

```bash
curl -X GET http://localhost:8000/api/v1/lessons/course/1/sections/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Mark Lesson Complete

```bash
curl -X POST http://localhost:8000/api/v1/lessons/1/complete/ \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

### Create Lesson (Instructor)

```bash
curl -X POST http://localhost:8000/api/v1/lessons/create/ \
  -H "Authorization: Bearer INSTRUCTOR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "section": 1,
    "title": "Variables and Data Types",
    "content": "In this lesson, we will learn about...",
    "lesson_type": "video",
    "video_url": "https://youtube.com/watch?v=...",
    "duration_minutes": 15,
    "is_preview": false
  }'
```

## Assignment System

### List Assignments

```bash
curl -X GET http://localhost:8000/api/v1/assignments/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Submit Assignment

```bash
curl -X POST http://localhost:8000/api/v1/assignments/1/submit/ \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN" \
  -F "submission_file=@assignment.pdf" \
  -F "submission_text=Here is my solution..."
```

### Grade Assignment (Instructor)

```bash
curl -X POST http://localhost:8000/api/v1/assignments/submissions/1/grade/ \
  -H "Authorization: Bearer INSTRUCTOR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "score": 85,
    "feedback": "Good work! Consider improving the error handling."
  }'
```

## Forum System

### List Forum Posts

```bash
curl -X GET http://localhost:8000/api/v1/forums/course/1/posts/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create Forum Post

```bash
curl -X POST http://localhost:8000/api/v1/forums/posts/create/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "course": 1,
    "title": "Question about loops",
    "content": "Can someone explain how while loops work?",
    "post_type": "question"
  }'
```

### Vote on Post

```bash
curl -X POST http://localhost:8000/api/v1/forums/posts/1/vote/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vote_type": "upvote"}'
```

## Payment System

### Add to Cart

```bash
curl -X POST http://localhost:8000/api/v1/payments/cart/add/ \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"course": 1, "quantity": 1}'
```

### View Cart

```bash
curl -X GET http://localhost:8000/api/v1/payments/cart/ \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

### Create Order

```bash
curl -X POST http://localhost:8000/api/v1/payments/orders/create/ \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "billing_address": "123 Main St",
    "billing_city": "New York",
    "billing_country": "US",
    "payment_method": "stripe"
  }'
```

## Live Sessions

### List Live Sessions

```bash
curl -X GET http://localhost:8000/api/v1/live-sessions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create Live Session (Instructor)

```bash
curl -X POST http://localhost:8000/api/v1/live-sessions/ \
  -H "Authorization: Bearer INSTRUCTOR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "course": 1,
    "title": "Live Q&A Session",
    "description": "Weekly Q&A for Python course",
    "scheduled_start": "2024-01-15T15:00:00Z",
    "scheduled_end": "2024-01-15T16:00:00Z",
    "platform": "zoom",
    "meeting_url": "https://zoom.us/j/123456789"
  }'
```

### Join Session (Student)

```bash
curl -X POST http://localhost:8000/api/v1/live-sessions/1/join/ \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

### Send Chat Message

```bash
curl -X POST http://localhost:8000/api/v1/live-sessions/1/chat/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Great explanation, thanks!",
    "message_type": "message"
  }'
```

## Analytics

### Student Dashboard

```bash
curl -X GET http://localhost:8000/api/v1/analytics/dashboard/ \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

### Instructor Analytics

```bash
curl -X GET http://localhost:8000/api/v1/analytics/instructor/courses/ \
  -H "Authorization: Bearer INSTRUCTOR_ACCESS_TOKEN"
```

### Revenue Report (Instructor)

```bash
curl -X GET http://localhost:8000/api/v1/analytics/instructor/revenue/ \
  -H "Authorization: Bearer INSTRUCTOR_ACCESS_TOKEN"
```

## Gamification

### User Achievements

```bash
curl -X GET http://localhost:8000/api/v1/gamification/achievements/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Leaderboard

```bash
curl -X GET http://localhost:8000/api/v1/gamification/leaderboard/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### User Points

```bash
curl -X GET http://localhost:8000/api/v1/gamification/points/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Admin Endpoints

### User Management (Admin)

```bash
curl -X GET http://localhost:8000/api/v1/auth/admin/users/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

### Approve Instructor (Admin)

```bash
curl -X POST http://localhost:8000/api/v1/auth/admin/users/1/approve-instructor/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

### Course Moderation (Admin)

```bash
curl -X GET http://localhost:8000/api/v1/courses/admin/pending/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

## Error Handling

All API endpoints return standardized error responses:

```json
{
  "error": "Error message",
  "details": {
    "field": ["Specific field error"]
  },
  "status_code": 400
}
```

Common status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

## Pagination

List endpoints support pagination:

```bash
curl -X GET "http://localhost:8000/api/v1/courses/?page=2&page_size=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response:

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/courses/?page=3",
  "previous": "http://localhost:8000/api/v1/courses/?page=1",
  "results": [...]
}
```

## Filtering and Search

### Course Filtering

```bash
# By category
curl -X GET "http://localhost:8000/api/v1/courses/?category=1"

# By level
curl -X GET "http://localhost:8000/api/v1/courses/?level=beginner"

# By price range
curl -X GET "http://localhost:8000/api/v1/courses/?min_price=10&max_price=100"

# Full text search
curl -X GET "http://localhost:8000/api/v1/courses/?search=python programming"

# Combined filters
curl -X GET "http://localhost:8000/api/v1/courses/?search=python&level=beginner&is_free=false"
```

### Assignment Filtering

```bash
# By course
curl -X GET "http://localhost:8000/api/v1/assignments/?course=1"

# By due date
curl -X GET "http://localhost:8000/api/v1/assignments/?due_date_after=2024-01-01"

# By status
curl -X GET "http://localhost:8000/api/v1/assignments/?status=pending"
```

## File Uploads

### Upload Profile Image

```bash
curl -X PATCH http://localhost:8000/api/v1/auth/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "profile_image=@profile.jpg"
```

### Upload Assignment File

```bash
curl -X POST http://localhost:8000/api/v1/assignments/1/submit/ \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN" \
  -F "submission_file=@assignment.pdf" \
  -F "submission_text=My solution explanation"
```

### Upload Lesson Video

```bash
curl -X POST http://localhost:8000/api/v1/lessons/create/ \
  -H "Authorization: Bearer INSTRUCTOR_ACCESS_TOKEN" \
  -F "video_file=@lesson1.mp4" \
  -F "title=Introduction to Variables" \
  -F "section=1" \
  -F "lesson_type=video"
```

## Postman Collection

Import this collection into Postman for easier testing:

```json
{
  "info": {
    "name": "Hybrid LMS API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{access_token}}",
        "type": "string"
      }
    ]
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000/api/v1"
    },
    {
      "key": "access_token",
      "value": ""
    }
  ]
}
```

## Testing Checklist

### Authentication Flow

- [ ] User registration
- [ ] Email verification
- [ ] User login
- [ ] Token refresh
- [ ] Password reset

### Course Management

- [ ] List courses
- [ ] Course details
- [ ] Course search and filtering
- [ ] Course enrollment
- [ ] Instructor course creation

### Learning Experience

- [ ] View lessons
- [ ] Mark lessons complete
- [ ] Progress tracking
- [ ] Quiz completion
- [ ] Certificate generation

### Interaction Features

- [ ] Forum posts and replies
- [ ] Q&A system
- [ ] Course reviews
- [ ] Live sessions

### Payment System

- [ ] Add to cart
- [ ] Checkout process
- [ ] Payment processing
- [ ] Order history

### Admin Features

- [ ] User management
- [ ] Course moderation
- [ ] Analytics dashboard
- [ ] Financial reports

This comprehensive testing guide covers all major API endpoints and functionality of the Hybrid LMS system.
