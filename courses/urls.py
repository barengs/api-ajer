from django.urls import path
from . import views

urlpatterns = [
    # Course discovery and browsing
    path('', views.CourseListView.as_view(), name='course_list'),
    path('featured/', views.featured_courses, name='featured_courses'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    
    # Course details
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('<int:course_id>/stats/', views.course_stats, name='course_stats'),
    
    # Course enrollment
    path('<int:course_id>/enroll/', views.CourseEnrollmentView.as_view(), name='course_enroll'),
    path('<int:course_id>/batches/', views.CourseBatchListView.as_view(), name='course_batches'),
    
    # Course reviews
    path('<int:course_id>/reviews/', views.CourseReviewListView.as_view(), name='course_reviews'),
    
    # Wishlist
    path('<int:course_id>/wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', views.student_wishlist, name='student_wishlist'),
    
    # Student enrollments
    path('enrollments/', views.StudentEnrollmentListView.as_view(), name='student_enrollments'),
    
    # Instructor course management
    path('instructor/', views.InstructorCourseListView.as_view(), name='instructor_courses'),
    path('instructor/<int:pk>/', views.InstructorCourseDetailView.as_view(), name='instructor_course_detail'),
    path('create/', views.CourseCreateView.as_view(), name='course_create'),
]