from django.urls import path
from . import views

urlpatterns = [
    # Course sections and lessons
    path('course/<int:course_id>/sections/', views.CourseSectionListView.as_view(), name='course_sections'),
    path('<int:pk>/', views.LessonDetailView.as_view(), name='lesson_detail'),
    
    # Lesson management (instructors)
    path('instructor/', views.InstructorLessonListView.as_view(), name='instructor_lessons'),
    path('create/', views.LessonCreateView.as_view(), name='lesson_create'),
    
    # Progress tracking
    path('<int:lesson_id>/progress/', views.LessonProgressUpdateView.as_view(), name='lesson_progress'),
    path('<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),
    path('progress/course/<int:course_id>/', views.student_progress_overview, name='student_progress_overview'),
    
    # Quizzes
    path('quiz/<int:pk>/', views.QuizDetailView.as_view(), name='quiz_detail'),
    path('quiz/<int:quiz_id>/attempt/', views.QuizAttemptCreateView.as_view(), name='quiz_attempt_create'),
    path('quiz/attempt/<int:attempt_id>/submit/', views.QuizSubmissionView.as_view(), name='quiz_submit'),
    
    # Lesson comments and discussions
    path('<int:lesson_id>/comments/', views.LessonCommentListView.as_view(), name='lesson_comments'),
    path('comment/<int:comment_id>/reply/', views.LessonCommentReplyView.as_view(), name='comment_reply'),
    
    # Student notes
    path('<int:lesson_id>/notes/', views.StudentNoteListView.as_view(), name='lesson_notes'),
    path('note/<int:pk>/', views.StudentNoteDetailView.as_view(), name='note_detail'),
]