# Hybrid LMS - Installation Guide

## Quick Start

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Create migrations
python manage.py makemigrations accounts
python manage.py makemigrations courses
python manage.py makemigrations lessons
python manage.py makemigrations assignments
python manage.py makemigrations forums
python manage.py makemigrations payments
python manage.py makemigrations notifications
python manage.py makemigrations analytics
python manage.py makemigrations gamification

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 3. Run Development Server

```bash
python manage.py runserver
```

The API will be available at:

- API Base: http://localhost:8000/api/v1/
- Admin Panel: http://localhost:8000/admin/
- API Documentation: http://localhost:8000/api/docs/

## API Endpoints Overview

### Authentication

- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/login/` - User login
- `GET /api/v1/auth/profile/` - User profile
- `POST /api/v1/auth/instructor/apply/` - Apply as instructor

### Courses

- `GET /api/v1/courses/` - List courses (with search/filter)
- `GET /api/v1/courses/featured/` - Featured courses
- `POST /api/v1/courses/create/` - Create course (instructors)
- `POST /api/v1/courses/{id}/enroll/` - Enroll in course

### Learning

- `GET /api/v1/lessons/course/{id}/sections/` - Course sections
- `GET /api/v1/lessons/{id}/` - Lesson details
- `POST /api/v1/lessons/{id}/complete/` - Mark lesson complete
- `GET /api/v1/lessons/quiz/{id}/` - Quiz details

### Assignments (Structured Courses)

- `GET /api/v1/assignments/course/{id}/` - Course assignments
- `POST /api/v1/assignments/{id}/submit/` - Submit assignment
- `GET /api/v1/assignments/student/` - Student assignments

### Forums & Q&A

- `GET /api/v1/forums/course/{id}/` - Course forums
- `GET /api/v1/forums/{id}/posts/` - Forum posts
- `POST /api/v1/forums/post/{id}/vote/` - Vote on post
- `POST /api/v1/forums/reply/{id}/accept/` - Accept answer

### Payments

- `GET /api/v1/payments/cart/` - Shopping cart
- `POST /api/v1/payments/cart/add/` - Add to cart
- `POST /api/v1/payments/order/create/` - Create order
- `POST /api/v1/payments/order/{id}/pay/` - Process payment

## Testing the API

### 1. Using the API Collection

Import `api_test_collection.json` into Postman or Insomnia for testing.

### 2. Sample API Flow

1. **Register a new user:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \\n  -H \"Content-Type: application/json\" \\n  -d '{
    \"email\": \"student@example.com\",
    \"username\": \"student123\",
    \"password\": \"SecurePass123\",
    \"password_confirm\": \"SecurePass123\",
    \"full_name\": \"John Student\",
    \"role\": \"student\"
  }'
```

2. **Login to get JWT token:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \\n  -H \"Content-Type: application/json\" \\n  -d '{
    \"email\": \"student@example.com\",
    \"password\": \"SecurePass123\"
  }'
```

3. **Browse courses:**

```bash
curl -X GET \"http://localhost:8000/api/v1/courses/?search=python&course_type=self_paced\"
```

4. **Get user profile (authenticated):**

```bash
curl -X GET http://localhost:8000/api/v1/auth/profile/ \\n  -H \"Authorization: Bearer YOUR_JWT_TOKEN\"
```

## Key Features Implemented

### ✅ User Management

- Custom user model with roles (Student, Instructor, Admin)
- JWT authentication with refresh tokens
- Email verification system
- Instructor application and verification
- User profiles and preferences

### ✅ Course System

- **Self-Paced Courses** (Udemy model)
  - Lifetime access
  - Individual enrollment
  - Asynchronous learning
- **Structured Classes** (Google Classroom model)
  - Batch-based enrollment
  - Time-bound courses
  - Scheduled assignments
  - Real-time interaction

### ✅ Learning Experience

- Course sections and lessons
- Multiple content types (video, text, quiz)
- Progress tracking
- Quiz system with auto-grading
- Student notes and bookmarks
- Lesson comments and Q&A

### ✅ Assignment System

- Assignment creation and management
- File upload support
- Rubric-based grading
- Group assignments
- Peer review system
- Due dates and late submissions

### ✅ Forum & Q&A

- Course-specific forums
- Question/answer system with voting
- Instructor response highlighting
- Content moderation and reporting
- Subscription and notifications

### ✅ E-Commerce

- Shopping cart functionality
- Order management
- Payment processing framework
- Coupon and discount system
- Instructor revenue sharing
- Refund management

### ✅ Analytics & Reporting

- Student progress tracking
- Instructor earnings dashboard
- Course performance metrics
- Platform-wide analytics

## Development Notes

### Database Models

The system uses 9 Django apps with comprehensive models:

- **accounts**: User management
- **courses**: Course and enrollment
- **lessons**: Content and progress
- **assignments**: Grading system
- **forums**: Discussions
- **payments**: E-commerce
- **notifications**: Messaging
- **analytics**: Reporting
- **gamification**: Badges/achievements

### API Architecture

- RESTful API design
- Role-based permissions
- Comprehensive filtering and search
- Pagination support
- Error handling and validation

### Security Features

- JWT token authentication
- Role-based access control
- Input validation and sanitization
- CORS configuration
- File upload security

## Next Steps

1. **Frontend Development**: Connect with React/Vue.js
2. **Payment Integration**: Add Stripe/PayPal
3. **Email Service**: Configure SMTP/SendGrid
4. **File Storage**: Set up AWS S3
5. **Video Hosting**: Integrate with video services
6. **Real-time Features**: Add WebSocket support
7. **Mobile App**: Develop mobile client
8. **Production Deployment**: Deploy to cloud

## Support

For questions and support:

1. Check the API documentation at `/api/docs/`
2. Review the comprehensive models in each app
3. Test endpoints using the provided collection
4. Refer to the detailed serializers for data structure", "original_text": "from django.urls import path

urlpatterns = [
# Notifications URLs will be implemented here
]"}]
