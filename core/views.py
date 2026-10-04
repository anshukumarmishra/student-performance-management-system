from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import CustomUser, Subject, Attendance, Mark

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    if request.user.is_teacher():
        return redirect('teacher_dashboard')
    return redirect('student_dashboard')

@login_required
def teacher_dashboard(request):
    if not request.user.is_teacher():
        return redirect('student_dashboard')
    
    subjects = Subject.objects.filter(teacher=request.user)
    students = CustomUser.objects.filter(role='STUDENT')
    return render(request, 'core/teacher_dashboard.html', {
        'subjects': subjects,
        'students': students
    })

@login_required
def student_dashboard(request):
    if not request.user.is_student():
        return redirect('teacher_dashboard')
    
    attendances = Attendance.objects.filter(student=request.user)
    total_classes = attendances.count()
    present_classes = attendances.filter(status='PRESENT').count()
    attendance_percentage = (present_classes / total_classes * 100) if total_classes > 0 else 0

    marks = Mark.objects.filter(student=request.user)
    profile = getattr(request.user, 'student_profile', None)

    return render(request, 'core/student_dashboard.html', {
        'attendances': attendances,
        'attendance_percentage': round(attendance_percentage, 1),
        'total_classes': total_classes,
        'present_classes': present_classes,
        'marks': marks,
        'profile': profile,
    })

@login_required
def mark_attendance(request):
    if not request.user.is_teacher():
        return redirect('student_dashboard')
    
    subjects = Subject.objects.filter(teacher=request.user)
    students = CustomUser.objects.filter(role='STUDENT')

    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        date = request.POST.get('date')
        subject = get_object_or_404(Subject, id=subject_id)

        for student in students:
            status = request.POST.get(f'status_{student.id}', 'ABSENT')
            Attendance.objects.update_or_create(
                student=student,
                subject=subject,
                date=date,
                defaults={'status': status}
            )
        return redirect('teacher_dashboard')

    return render(request, 'core/mark_attendance.html', {
        'subjects': subjects,
        'students': students
    })

@login_required
def enter_marks(request):
    if not request.user.is_teacher():
        return redirect('student_dashboard')
    
    subjects = Subject.objects.filter(teacher=request.user)
    students = CustomUser.objects.filter(role='STUDENT')

    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        student_id = request.POST.get('student')
        exam_type = request.POST.get('exam_type')
        marks_obtained = request.POST.get('marks_obtained')
        max_marks = request.POST.get('max_marks', 100)

        subject = get_object_or_404(Subject, id=subject_id)
        student = get_object_or_404(CustomUser, id=student_id)

        Mark.objects.create(
            student=student,
            subject=subject,
            exam_type=exam_type,
            marks_obtained=marks_obtained,
            max_marks=max_marks
        )
        return redirect('teacher_dashboard')

    return render(request, 'core/enter_marks.html', {
        'subjects': subjects,
        'students': students
    })