import csv
import calendar
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import CustomUser, Subject, Attendance, Mark, Notification, Doubt
from .models import CustomUser, Subject, Attendance, Mark, Notification, Doubt, InterventionLog

def check_and_trigger_attendance_warning(student, subject):
    """Utility function to calculate subject attendance and notify if sub-75%."""
    total_classes = Attendance.objects.filter(student=student, subject=subject).count()
    if total_classes == 0:
        return 100.0, False

    present_classes = Attendance.objects.filter(student=student, subject=subject, status='PRESENT').count()
    percentage = (present_classes / total_classes) * 100

    if percentage < 75.0:
        title = f"⚠️ Low Attendance Warning: {subject.name}"
        already_notified = Notification.objects.filter(
            user=student,
            title=title,
            is_read=False
        ).exists()

        if not already_notified:
            Notification.objects.create(
                user=student,
                title=title,
                message=f"Your attendance in {subject.name} has fallen to {percentage:.1f}% ({present_classes}/{total_classes} classes). Minimum required is 75%."
            )
            
    return round(percentage, 1), percentage < 75.0

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
def student_dashboard(request):
    if not request.user.is_student():
        return redirect('teacher_dashboard')

    # ... (Keep existing attendance & heatmap logic here) ...
    now = datetime.now()
    year = int(request.GET.get('year', now.year))
    month = int(request.GET.get('month', now.month))

    cal = calendar.monthcalendar(year, month)
    all_attendances = Attendance.objects.filter(student=request.user)
    total_classes = all_attendances.count()
    present_classes = all_attendances.filter(status='PRESENT').count()
    overall_attendance = round((present_classes / total_classes * 100), 1) if total_classes > 0 else 100.0

    month_attendances = all_attendances.filter(date__year=year, date__month=month)
    attendance_map = {att.date.day: att.status for att in month_attendances}

    calendar_weeks = []
    for week in cal:
        week_days = []
        for day in week:
            if day == 0:
                week_days.append({'day': 0, 'status': None})
            else:
                week_days.append({'day': day, 'status': attendance_map.get(day, None)})
        calendar_weeks.append(week_days)

    months_list = [(i, calendar.month_name[i]) for i in range(1, 13)]

    subjects = Subject.objects.all()
    subject_stats = []
    for subject in subjects:
        total = all_attendances.filter(subject=subject).count()
        present = all_attendances.filter(subject=subject, status='PRESENT').count()
        pct = (present / total * 100) if total > 0 else 100.0
        subject_stats.append({
            'subject': subject, 'total': total, 'present': present,
            'percentage': round(pct, 1), 'is_low': pct < 75.0 and total > 0
        })

    # --- Dynamic Exam Progression & Trend Analysis ---
    raw_marks = Mark.objects.filter(student=request.user).select_related('subject').order_by('subject', 'id')
    
    # Group marks by subject to calculate progression between sequential exams
    marks_with_trends = []
    subject_previous_pct = {}

    for mark in raw_marks:
        current_pct = round((mark.marks_obtained / mark.max_marks * 100), 1) if mark.max_marks > 0 else 0.0
        sub_id = mark.subject.id
        
        trend = "Baseline"
        delta = 0.0
        if sub_id in subject_previous_pct:
            prev_pct = subject_previous_pct[sub_id]
            delta = round(current_pct - prev_pct, 1)
            if delta > 0:
                trend = f"↗ +{delta}% Improving"
            elif delta < 0:
                trend = f"↘ {delta}% Declining"
            else:
                trend = "→ Stable"
        
        subject_previous_pct[sub_id] = current_pct
        
        marks_with_trends.append({
            'subject': mark.subject.name,
            'exam_type': mark.get_exam_type_display(),
            'obtained': mark.marks_obtained,
            'max_marks': mark.max_marks,
            'percentage': current_pct,
            'trend': trend,
            'delta': delta,
            'is_improving': delta > 0,
            'is_declining': delta < 0
        })

    total_obtained = sum(m.marks_obtained for m in raw_marks)
    total_max = sum(m.max_marks for m in raw_marks)
    overall_grade_pct = round((total_obtained / total_max * 100), 1) if total_max > 0 else 0.0

    if total_max == 0:
        performance_tier = "Pending Evaluation"
        tier_color = "#64748b"
    elif overall_grade_pct >= 80:
        performance_tier = "High Performer (A)"
        tier_color = "#16a34a"
    elif overall_grade_pct >= 60:
        performance_tier = "Satisfactory (B)"
        tier_color = "#2563eb"
    elif overall_grade_pct >= 40:
        performance_tier = "Needs Improvement (C)"
        tier_color = "#d97706"
    else:
        performance_tier = "Critical Academic Risk (F)"
        tier_color = "#dc2626"

    profile = getattr(request.user, 'student_profile', None)
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    doubts = Doubt.objects.filter(student=request.user).select_related('subject').order_by('-created_at')

    return render(request, 'core/student_dashboard.html', {
        'profile': profile,
        'subject_stats': subject_stats,
        'overall_attendance': overall_attendance,
        'total_classes': total_classes,
        'present_classes': present_classes,
        'calendar_weeks': calendar_weeks,
        'year': year, 'month': month, 'months_list': months_list,
        'marks_with_trends': marks_with_trends,
        'overall_grade_pct': overall_grade_pct,
        'performance_tier': performance_tier,
        'tier_color': tier_color,
        'notifications': notifications,
        'doubts': doubts,
    })
@login_required
def teacher_dashboard(request):
    if not request.user.is_teacher():
        return redirect('student_dashboard')

    teacher_subjects = Subject.objects.filter(teacher=request.user)
    students = CustomUser.objects.filter(role='STUDENT').select_related('student_profile')

    # 1. Unified Academic Intervention Matrix (Attendance < 75% OR Marks < 50%)
    intervention_list = []
    for student in students:
        for subject in teacher_subjects:
            total_att = Attendance.objects.filter(student=student, subject=subject).count()
            present_att = Attendance.objects.filter(student=student, subject=subject, status='PRESENT').count()
            att_pct = round((present_att / total_att * 100), 1) if total_att > 0 else 100.0
            low_att = total_att > 0 and att_pct < 75.0

            sub_marks = Mark.objects.filter(student=student, subject=subject)
            obt = sum(m.marks_obtained for m in sub_marks)
            mx = sum(m.max_marks for m in sub_marks)
            mark_pct = round((obt / mx * 100), 1) if mx > 0 else None
            low_marks = mark_pct is not None and mark_pct < 50.0

            if low_att or low_marks:
                reasons = []
                if low_att:
                    reasons.append(f"Attendance: {att_pct}%")
                if low_marks:
                    reasons.append(f"Marks: {mark_pct}%")

                intervention_list.append({
                    'student': student,
                    'subject': subject,
                    'att_pct': att_pct if total_att > 0 else "N/A",
                    'mark_pct': f"{mark_pct}%" if mark_pct is not None else "No Marks",
                    'risk_reason': " | ".join(reasons),
                    'is_critical': low_att and low_marks
                })

    # 2. Fetch past Student Counseling & Intervention Logs
    intervention_logs = InterventionLog.objects.filter(
        subject__teacher=request.user
    ).select_related('student', 'subject', 'teacher').order_by('-created_at')

    # 3. Notifications and Doubts Queue
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    doubts = Doubt.objects.filter(subject__teacher=request.user, is_resolved=False).select_related('student', 'subject')

    return render(request, 'core/teacher_dashboard.html', {
        'subjects': teacher_subjects,
        'students': students,
        'intervention_list': intervention_list,
        'intervention_logs': intervention_logs,
        'notifications': notifications,
        'doubts': doubts,
    })
@login_required
def mark_attendance(request):
    if not request.user.is_teacher():
        return redirect('student_dashboard')
    
    subjects = Subject.objects.filter(teacher=request.user)
    students = CustomUser.objects.filter(role='STUDENT').select_related('student_profile')

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
            check_and_trigger_attendance_warning(student, subject)

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
    students = CustomUser.objects.filter(role='STUDENT').select_related('student_profile')

    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        student_id = request.POST.get('student')
        exam_type = request.POST.get('exam_type')
        marks_obtained = request.POST.get('marks_obtained')
        max_marks = request.POST.get('max_marks', 100)

        subject = get_object_or_404(Subject, id=subject_id)
        student = get_object_or_404(CustomUser, id=student_id)

        Mark.objects.update_or_create(
            student=student,
            subject=subject,
            exam_type=exam_type,
            defaults={
                'marks_obtained': float(marks_obtained),
                'max_marks': float(max_marks)
            }
        )

        return redirect('teacher_dashboard')

    return render(request, 'core/enter_marks.html', {
        'subjects': subjects,
        'students': students
    })

@login_required
def post_announcement(request):
    if not request.user.is_teacher():
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        
        students = CustomUser.objects.filter(role='STUDENT')
        for student in students:
            Notification.objects.create(
                user=student,
                title=title,
                message=message
            )
        return redirect('teacher_dashboard')
    
    return redirect('teacher_dashboard')

@login_required
def mark_notification_read(request, notification_id):
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'invalid method'}, status=400)

@login_required
def add_subject(request):
    if not request.user.is_teacher():
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        
        Subject.objects.create(
            name=name,
            code=code,
            teacher=request.user
        )
        return redirect('teacher_dashboard')
        
    return render(request, 'core/add_subject.html')

@login_required
def export_attendance_csv(request):
    if not request.user.is_teacher():
        return redirect('student_dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Roll Number', 'Student Name', 'Subject', 'Date', 'Status'])

    attendances = Attendance.objects.filter(subject__teacher=request.user).select_related('student__student_profile', 'subject')
    for att in attendances:
        roll_no = att.student.student_profile.roll_number if hasattr(att.student, 'student_profile') else 'N/A'
        writer.writerow([roll_no, att.student.username, att.subject.name, att.date, att.status])

    return response

@login_required
def export_grades_csv(request):
    if not request.user.is_teacher():
        return redirect('student_dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="grades_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Roll Number', 'Student Name', 'Subject', 'Exam Type', 'Marks Obtained', 'Max Marks'])

    marks = Mark.objects.filter(subject__teacher=request.user).select_related('student__student_profile', 'subject')
    for mark in marks:
        roll_no = mark.student.student_profile.roll_number if hasattr(mark.student, 'student_profile') else 'N/A'
        writer.writerow([
            roll_no, 
            mark.student.username, 
            mark.subject.name, 
            mark.get_exam_type_display(), 
            mark.marks_obtained, 
            mark.max_marks
        ])

    return response

@login_required
def submit_doubt(request):
    if not request.user.is_student():
        return redirect('teacher_dashboard')
    
    subjects = Subject.objects.all()
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        question = request.POST.get('question')
        subject = get_object_or_404(Subject, id=subject_id)
        
        Doubt.objects.create(
            student=request.user,
            subject=subject,
            question=question
        )
        return redirect('student_dashboard')
        
    return render(request, 'core/submit_doubt.html', {'subjects': subjects})

@login_required
def answer_doubt(request, doubt_id):
    if not request.user.is_teacher():
        return redirect('student_dashboard')
        
    doubt = get_object_or_404(Doubt, id=doubt_id)
    if request.method == 'POST':
        answer = request.POST.get('answer')
        doubt.answer = answer
        doubt.is_resolved = True
        doubt.save()
        
        Notification.objects.create(
            user=doubt.student,
            title=f"Doubt Resolved: {doubt.subject.name}",
            message=f"Your teacher answered: {answer}"
        )
        
    return redirect('teacher_dashboard')

@login_required
def delete_doubt(request, doubt_id):
    if not request.user.is_student():
        return redirect('student_dashboard')
        
    doubt = get_object_or_404(Doubt, id=doubt_id, student=request.user)
    if request.method == 'POST':
        doubt.delete()
        
    return redirect('student_dashboard')
@login_required
def add_intervention_log(request):
    if not request.user.is_teacher():
        return redirect('student_dashboard')

    if request.method == 'POST':
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        note = request.POST.get('note')
        action_taken = request.POST.get('action_taken')
        status = request.POST.get('status', 'UNDER_OBSERVATION')

        student = get_object_or_404(CustomUser, id=student_id, role='STUDENT')
        subject = get_object_or_404(Subject, id=subject_id, teacher=request.user)

        InterventionLog.objects.create(
            student=student,
            teacher=request.user,
            subject=subject,
            note=note,
            action_taken=action_taken,
            status=status
        )

        # Notify student about academic counseling/support
        Notification.objects.create(
            user=student,
            title=f"Academic Support Log: {subject.name}",
            message=f"Your teacher ({request.user.username}) recorded an intervention note: '{action_taken}'. Status: {status.replace('_', ' ')}"
        )

    return redirect('teacher_dashboard')