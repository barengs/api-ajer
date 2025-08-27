from django.urls import path
from . import views

urlpatterns = [
    # Course assignments
    path('course/<int:course_id>/', views.CourseAssignmentListView.as_view(), name='course_assignments'),
    path('<int:pk>/', views.AssignmentDetailView.as_view(), name='assignment_detail'),
    
    # Assignment management (instructors)
    path('instructor/', views.InstructorAssignmentListView.as_view(), name='instructor_assignments'),
    path('instructor/<int:pk>/', views.InstructorAssignmentDetailView.as_view(), name='instructor_assignment_detail'),
    path('create/', views.AssignmentCreateView.as_view(), name='assignment_create'),
    
    # Assignment submissions
    path('<int:assignment_id>/submit/', views.AssignmentSubmissionCreateView.as_view(), name='assignment_submit'),
    path('<int:assignment_id>/submissions/', views.AssignmentSubmissionListView.as_view(), name='assignment_submissions'),
    path('submission/<int:pk>/', views.AssignmentSubmissionDetailView.as_view(), name='submission_detail'),
    path('submission/<int:submission_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('submission/<int:pk>/grade/', views.AssignmentGradeView.as_view(), name='grade_submission'),
    
    # Student assignments
    path('student/', views.StudentAssignmentListView.as_view(), name='student_assignments'),
    
    # Assignment groups
    path('<int:assignment_id>/groups/', views.AssignmentGroupListView.as_view(), name='assignment_groups'),
    path('group/<int:group_id>/join/', views.join_assignment_group, name='join_group'),
    
    # Assignment rubrics
    path('<int:assignment_id>/rubric/', views.AssignmentRubricView.as_view(), name='assignment_rubric'),
    
    # Assignment statistics
    path('<int:assignment_id>/stats/', views.assignment_statistics, name='assignment_statistics'),
]