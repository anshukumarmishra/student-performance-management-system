from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STUDENT')

    def is_teacher(self):
        return self.role == 'TEACHER'

    def is_student(self):
        return self.role == 'STUDENT'

class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    roll_number = models.CharField(max_length=50, unique=True)
    course = models.CharField(max_length=100)
    semester = models.IntegerField()

    def __str__(self):
        return f"{self.user.username} ({self.roll_number})"

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='subjects',null=True, blank=True)
    

    def __str__(self):
        return f"{self.code}: {self.name}"

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
    )
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='attendances')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('student', 'subject', 'date')

class Mark(models.Model):
    EXAM_CHOICES = (
        ('MIDTERM', 'Mid-Term'),
        ('ENDTERM', 'End-Term'),
        ('MINTERM', 'Min-Term'),
    )
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='marks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_type = models.CharField(max_length=20, choices=EXAM_CHOICES)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
class Doubt(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='doubts')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='doubts')
    question = models.TextField()
    answer = models.TextField(blank=True, null=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Doubt by {self.student.username} on {self.subject.name}"

class InterventionLog(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='intervention_logs', limit_choices_to={'role': 'STUDENT'})
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='given_interventions', limit_choices_to={'role': 'TEACHER'})
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    note = models.TextField()
    action_taken = models.CharField(max_length=200, help_text="e.g., One-on-one counseling, Extra assignments given")
    status = models.CharField(max_length=50, choices=[
        ('UNDER_OBSERVATION', 'Under Observation'),
        ('IMPROVING', 'Showing Improvement'),
        ('RESOLVED', 'Resolved / Closed')
    ], default='UNDER_OBSERVATION')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Intervention for {self.student.username} by {self.teacher.username} ({self.status})"