# Hybrid LMS - Learning Management System API

A comprehensive Learning Management System that combines the self-paced learning model of Udemy with the structured classroom approach of Google Classroom.

## Features

### 🎓 Student Features

- **Course Discovery**: Browse courses with advanced search and filtering
- **Self-Paced Learning**: Udemy-style courses with lifetime access
- **Structured Classes**: Google Classroom-style batch-based learning
- **Progress Tracking**: Visual progress indicators and completion certificates
- **Interactive Learning**: Video lessons, quizzes, and assignments
- **Q&A Forums**: Ask questions and interact with instructors and peers
- **Reviews & Ratings**: Rate and review completed courses

### 👨‍🏫 Instructor Features

- **Course Creation**: Create both self-paced and structured courses
- **Batch Management**: Schedule and manage classroom-style batches
- **Content Management**: Upload videos, create lessons, and assignments
- **Student Analytics**: Track student progress and engagement
- **Revenue Management**: Monitor earnings and payout history
- **Grading System**: Grade assignments with rubrics and feedback

### ⚙️ Admin Features

- **User Management**: Manage students, instructors, and verification
- **Content Moderation**: Review and approve courses and content
- **Financial Management**: Handle payments, refunds, and instructor payouts
- **Analytics Dashboard**: Platform-wide metrics and reporting
- **System Configuration**: Manage categories, coupons, and settings

## Technology Stack

- **Backend**: Django 5.0, Django REST Framework
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: JWT with SimpleJWT
- **File Storage**: Local storage (development), AWS S3 (production)
- **Task Queue**: Celery with Redis
- **API Documentation**: DRF Spectacular (OpenAPI/Swagger)

## Project Structure

```
hybrid_lms/
├── accounts/          # User management and authentication
├── courses/           # Course and enrollment management
├── lessons/           # Lesson content and progress tracking
├── assignments/       # Assignment and grading system
├── forums/            # Discussion forums and Q&A
├── payments/          # E-commerce and payment processing
├── notifications/     # Notification system
├── analytics/         # Analytics and reporting
├── gamification/      # Badges, points, and leaderboards
└── hybrid_lms/        # Project settings and configuration
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/login/` - User login
- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/refresh/` - Refresh JWT token
- `POST /api/v1/auth/logout/` - User logout
- `POST /api/v1/auth/verify-email/` - Email verification
- `POST /api/v1/auth/password/reset/` - Password reset request

### Courses

- `GET /api/v1/courses/` - List all courses with filters
- `GET /api/v1/courses/featured/` - Featured courses
- `GET /api/v1/courses/{slug}/` - Course details
- `POST /api/v1/courses/create/` - Create new course (instructors)
- `POST /api/v1/courses/{id}/enroll/` - Enroll in course
- `GET /api/v1/courses/enrollments/` - Student's enrolled courses

### User Management

- `GET /api/v1/auth/profile/` - Get user profile
- `PUT /api/v1/auth/profile/` - Update user profile
- `GET /api/v1/auth/dashboard/` - Dashboard data
- `POST /api/v1/auth/instructor/apply/` - Apply to become instructor

## Installation

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup

1. **Clone the repository**

```bash
git clone <repository-url>
cd hybridLms
```

2. **Create and activate virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Environment configuration**

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser**

```bash
python manage.py createsuperuser
```

7. **Run development server**

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## API Documentation

Interactive API documentation is available at:

- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- OpenAPI Schema: `http://localhost:8000/api/schema/`

## Course Types

### Self-Paced Courses (Udemy Style)

- Students can purchase and access anytime
- Learn at their own pace
- Lifetime access to content
- Asynchronous Q&A and discussions
- Certificate upon completion

### Structured Classes (Google Classroom Style)

- Batch-based enrollment with specific dates
- Scheduled lessons and assignments
- Real-time interaction and discussions
- Graded assignments with feedback
- Cohort-based learning experience

## User Roles

### Student

- Enroll in courses (free or paid)
- Track learning progress
- Participate in discussions
- Submit assignments (structured courses)
- Rate and review courses

### Instructor

- Create and manage courses
- Upload content and resources
- Manage batches and schedules
- Grade assignments and provide feedback
- Interact with students through forums
- Monitor analytics and earnings

### Admin

- Manage all users and content
- Approve instructor applications
- Moderate courses and forums
- Handle financial transactions
- Generate platform reports
- Configure system settings

## Payment System

The system supports:

- Course purchases with multiple payment methods
- Shopping cart functionality
- Discount coupons and promotions
- Instructor revenue sharing
- Automated payout processing
- Refund management

## Forum System

### Course Forums

- General discussions
- Q&A sections
- Assignment discussions
- Announcements

### Features

- Threaded discussions
- Vote system for helpful answers
- Instructor highlighting
- Content moderation
- Search and filtering

## Development

### Running Tests

```bash
python manage.py test
```

### Code Coverage

```bash
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Creating Sample Data

```bash
python manage.py loaddata fixtures/sample_data.json
```

## Deployment

### Development Server

For development purposes, you can use Django's built-in development server:

```bash
python manage.py runserver
```

**Note**: The development server displays a warning about not using it in production. This is normal and expected during development.

### Production Deployment

For production deployment, please refer to the detailed guide in [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md).

Key components for production deployment include:

1. **Web Server**: Use Gunicorn with Nginx as a reverse proxy
2. **Database**: Migrate from SQLite to PostgreSQL
3. **Static Files**: Use WhiteNoise or serve through Nginx
4. **Caching**: Implement Redis for caching and Celery broker
5. **Security**: Configure HTTPS, security headers, and proper authentication
6. **Monitoring**: Set up health checks and logging
7. **Scaling**: Configure load balancing for high traffic

### Production Settings

1. Set `DEBUG=False` in environment
2. Configure PostgreSQL database
3. Set up AWS S3 for file storage
4. Configure Redis for Celery
5. Set up email service (SMTP/SendGrid)
6. Configure payment gateways (Stripe)

### Environment Variables

```
DEBUG=False
SECRET_KEY=your-secret-key
DB_NAME=hybrid_lms_prod
DB_USER=your-db-user
DB_PASSWORD=your-db-password
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
STRIPE_SECRET_KEY=your-stripe-key
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Create an issue on GitHub
- Check the API documentation
- Review the code examples

## Roadmap

### Phase 1 (Current)

- ✅ User authentication and management
- ✅ Course creation and enrollment
- ✅ Basic payment system
- ✅ Forum discussions

### Phase 2

- 🔄 Advanced analytics
- 🔄 Live class integration
- 🔄 Mobile app support
- 🔄 Advanced gamification

### Phase 3

- 📋 AI-powered recommendations
- 📋 Advanced assessment tools
- 📋 Plagiarism detection
- 📋 Multi-language support
