from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('teacher/mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('teacher/enter-marks/', views.enter_marks, name='enter_marks'),
    path('teacher/post-announcement/', views.post_announcement, name='post_announcement'),

    # Password Reset Routes
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='core/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='core/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('notification/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('teacher/add-subject/', views.add_subject, name='add_subject'),
    path('teacher/export-attendance/', views.export_attendance_csv, name='export_attendance_csv'),
    path('teacher/export-grades/', views.export_grades_csv, name='export_grades_csv'),
    path('student/submit-doubt/', views.submit_doubt, name='submit_doubt'),
    path('teacher/answer-doubt/<int:doubt_id>/', views.answer_doubt, name='answer_doubt'),
    path('student/delete-doubt/<int:doubt_id>/', views.delete_doubt, name='delete_doubt'),
    path('intervention/add/', views.add_intervention_log, name='add_intervention_log'),
]