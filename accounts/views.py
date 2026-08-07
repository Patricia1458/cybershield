import secrets
import string
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import RegisterForm, ProfileEditForm
from .models import Profile, Organization
from .utils import compute_security_stats, compute_badges, log_activity
from training.models import TrainingModule, UserProgress, TrainingAssignment
from phishing.models import PhishingResult


def _generate_temp_password(length=12):
    # Django's User.objects.make_random_password() was removed in this Django
    # version, so temporary passwords are generated with the `secrets` module instead.
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _employee_metrics(user, total_modules):
    """Real, database-computed training/phishing stats for one employee."""
    progress = UserProgress.objects.filter(user=user)
    completed_count = progress.filter(completed=True).count()
    completion_rate = round((completed_count / total_modules) * 100, 1) if total_modules else 0

    completed_scores = list(progress.filter(completed=True).values_list('score', flat=True))
    avg_quiz_score = round(sum(completed_scores) / len(completed_scores), 1) if completed_scores else 0

    results = PhishingResult.objects.filter(employee=user)
    total_results = results.count()
    click_rate = round((results.filter(clicked_link=True).count() / total_results) * 100, 1) if total_results else 0
    report_rate = round((results.filter(reported_suspicious=True).count() / total_results) * 100, 1) if total_results else 0

    if click_rate > 30:
        risk = 'high'
    elif click_rate >= 15:
        risk = 'medium'
    else:
        risk = 'low'

    return {
        'completion_rate': completion_rate,
        'avg_quiz_score': avg_quiz_score,
        'click_rate': click_rate,
        'report_rate': report_rate,
        'risk': risk,
    }


def is_admin(user):
    return Profile.objects.filter(user=user, role='admin').exists()

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            organization = Organization.objects.create(name=form.cleaned_data['organization_name'])
            Profile.objects.create(
                user=user,
                role='admin',
                organization=organization,
                company_name=organization.name,
            )
            # The user was just created directly (not via authenticate()), and with
            # django-axes' backend also configured, login() can no longer infer
            # which backend to associate — ModelBackend is the correct one here.
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('dashboard_home')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def dashboard_home(request):
    return redirect('dashboard')


@login_required
def profile_view(request):
    stats = compute_security_stats(request.user)
    badges = compute_badges(request.user, stats=stats)

    return render(request, 'accounts/profile.html', {
        **stats,
        'badges': badges,
    })


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was updated.')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})


def _org_members(organization, total_modules, search=''):
    """Same metrics as _employee_metrics, computed for every employee in the org
    in a fixed number of queries instead of ~5 queries per employee (N+1)."""
    profiles = list(Profile.objects.filter(organization=organization, role='employee').select_related('user'))
    user_ids = [p.user_id for p in profiles]

    scores_by_user = defaultdict(list)
    for user_id, score in UserProgress.objects.filter(user_id__in=user_ids, completed=True).values_list('user_id', 'score'):
        scores_by_user[user_id].append(score)

    results_by_user = defaultdict(lambda: {'total': 0, 'clicked': 0, 'reported': 0})
    for user_id, clicked, reported in PhishingResult.objects.filter(employee_id__in=user_ids).values_list('employee_id', 'clicked_link', 'reported_suspicious'):
        bucket = results_by_user[user_id]
        bucket['total'] += 1
        bucket['clicked'] += int(clicked)
        bucket['reported'] += int(reported)

    members = []
    for profile in profiles:
        scores = scores_by_user.get(profile.user_id, [])
        completed_count = len(scores)
        completion_rate = round((completed_count / total_modules) * 100, 1) if total_modules else 0
        avg_quiz_score = round(sum(scores) / len(scores), 1) if scores else 0

        bucket = results_by_user.get(profile.user_id, {'total': 0, 'clicked': 0, 'reported': 0})
        total_results = bucket['total']
        click_rate = round((bucket['clicked'] / total_results) * 100, 1) if total_results else 0
        report_rate = round((bucket['reported'] / total_results) * 100, 1) if total_results else 0

        if click_rate > 30:
            risk = 'high'
        elif click_rate >= 15:
            risk = 'medium'
        else:
            risk = 'low'

        members.append({
            'profile': profile,
            'completion_rate': completion_rate,
            'avg_quiz_score': avg_quiz_score,
            'click_rate': click_rate,
            'report_rate': report_rate,
            'risk': risk,
            'has_clicked': bucket['clicked'] > 0,
            'has_reported': bucket['reported'] > 0,
        })

    if search:
        search = search.lower()
        members = [
            m for m in members
            if search in m['profile'].user.username.lower()
            or search in (m['profile'].user.first_name or '').lower()
            or search in (m['profile'].user.last_name or '').lower()
        ]
    return members


@login_required
@user_passes_test(is_admin)
def invite_employee(request):
    organization = request.user.profile.organization
    modules = TrainingModule.objects.all()

    context = {
        'modules': modules,
        'employee_name': '',
        'employee_email': '',
        'personal_message': '',
        'selected_module_ids': [],
    }

    if request.method == 'POST':
        employee_name = request.POST.get('employee_name', '').strip()
        employee_email = request.POST.get('employee_email', '').strip()
        personal_message = request.POST.get('personal_message', '').strip()
        selected_module_ids = request.POST.getlist('modules')

        context.update({
            'employee_name': employee_name,
            'employee_email': employee_email,
            'personal_message': personal_message,
            'selected_module_ids': selected_module_ids,
        })

        if not employee_name or not employee_email:
            messages.error(request, 'Please provide both a name and an email address.')
        elif User.objects.filter(username=employee_email).exists():
            messages.error(request, f'A user with the email "{employee_email}" already exists.')
        else:
            temp_password = _generate_temp_password()
            name_parts = employee_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''

            new_user = User.objects.create_user(
                username=employee_email,
                email=employee_email,
                password=temp_password,
                first_name=first_name,
                last_name=last_name,
            )

            Profile.objects.create(
                user=new_user,
                role='employee',
                status='invited',
                organization=organization,
                company_name=organization.name if organization else 'TechStart SME',
            )

            assigned_modules = list(TrainingModule.objects.filter(id__in=selected_module_ids))
            for module in assigned_modules:
                TrainingAssignment.objects.create(employee=new_user, module=module)

            log_activity(organization, new_user, f"{employee_name} joined the organization")

            message_body = (
                f"Hi {employee_name},\n\n"
                f"You've been added to CyberShield's security awareness training platform.\n\n"
                f"Username: {employee_email}\n"
                f"Temporary password: {temp_password}\n\n"
            )
            if assigned_modules:
                module_lines = '\n'.join(f'- {m.title}' for m in assigned_modules)
                message_body += f"Assigned training modules:\n{module_lines}\n\n"
            if personal_message:
                message_body += f"Message from your admin:\n{personal_message}\n\n"
            message_body += "Please log in and keep this password safe."

            send_mail(
                subject='Welcome to CyberShield',
                message=message_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[employee_email],
                fail_silently=True,
            )

            messages.success(request, f'{employee_name} was added successfully.')
            context.update({
                'invited_name': employee_name,
                'invited_username': employee_email,
                'temp_password': temp_password,
                'assigned_modules': assigned_modules,
                'employee_name': '',
                'employee_email': '',
                'personal_message': '',
                'selected_module_ids': [],
            })

    member_search = request.GET.get('member_search', '').strip()
    context['members'] = _org_members(organization, modules.count(), search=member_search)
    context['member_search'] = member_search

    return render(request, 'accounts/invite_employee.html', context)


@login_required
@user_passes_test(is_admin)
def employee_list(request):
    organization = request.user.profile.organization
    total_modules = TrainingModule.objects.count()
    all_members = _org_members(organization, total_modules)

    total_count = len(all_members)
    active_count = sum(1 for m in all_members if m['profile'].status == 'active')
    pending_count = total_count - active_count
    high_risk_count = sum(1 for m in all_members if m['risk'] == 'high')

    search = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    risk_filter = request.GET.get('risk', '')
    action_filter = request.GET.get('action', '')
    sort_filter = request.GET.get('sort', '')

    rows = all_members
    if search:
        search_lower = search.lower()
        rows = [
            r for r in rows
            if search_lower in r['profile'].user.username.lower()
            or search_lower in (r['profile'].user.first_name or '').lower()
            or search_lower in (r['profile'].user.last_name or '').lower()
        ]
    if status_filter:
        rows = [r for r in rows if r['profile'].status == status_filter]
    if risk_filter:
        rows = [r for r in rows if r['risk'] == risk_filter]
    if action_filter == 'clicked':
        rows = [r for r in rows if r['has_clicked']]
    elif action_filter == 'reported':
        rows = [r for r in rows if r['has_reported']]

    if sort_filter == 'completion_asc':
        rows = sorted(rows, key=lambda r: r['completion_rate'])
    elif sort_filter == 'quiz_asc':
        rows = sorted(rows, key=lambda r: r['avg_quiz_score'])

    return render(request, 'accounts/employee_list.html', {
        'rows': rows,
        'organization': organization,
        'total_count': total_count,
        'active_count': active_count,
        'pending_count': pending_count,
        'high_risk_count': high_risk_count,
        'search': search,
        'status_filter': status_filter,
        'risk_filter': risk_filter,
        'action_filter': action_filter,
        'sort_filter': sort_filter,
    })


@login_required
@user_passes_test(is_admin)
def employee_detail(request, user_id):
    organization = request.user.profile.organization
    profile = get_object_or_404(Profile, user_id=user_id, organization=organization, role='employee')
    employee = profile.user

    total_modules = TrainingModule.objects.count()
    metrics = _employee_metrics(employee, total_modules)

    progress_by_module = {p.module_id: p for p in UserProgress.objects.filter(user=employee)}
    assignments = TrainingAssignment.objects.filter(employee=employee).select_related('module')
    assigned_modules = []
    for assignment in assignments:
        p = progress_by_module.get(assignment.module_id)
        assigned_modules.append({
            'module': assignment.module,
            'progress_percent': p.score if (p and p.completed) else 0,
            'completed': bool(p and p.completed),
        })

    results = PhishingResult.objects.filter(employee=employee).select_related('campaign', 'campaign__template').order_by('-email_sent_at')

    return render(request, 'accounts/employee_detail.html', {
        'profile': profile,
        'employee': employee,
        'metrics': metrics,
        'assigned_modules': assigned_modules,
        'results': results,
    })


@login_required
@user_passes_test(is_admin)
def assign_training(request, user_id):
    organization = request.user.profile.organization
    profile = get_object_or_404(Profile, user_id=user_id, organization=organization, role='employee')
    employee = profile.user

    already_assigned_ids = set(
        TrainingAssignment.objects.filter(employee=employee).values_list('module_id', flat=True)
    )
    modules = TrainingModule.objects.all()

    if request.method == 'POST':
        selected_module_ids = request.POST.getlist('modules')
        new_modules = TrainingModule.objects.filter(id__in=selected_module_ids).exclude(id__in=already_assigned_ids)
        for module in new_modules:
            TrainingAssignment.objects.create(employee=employee, module=module)
        if new_modules:
            messages.success(request, f'Assigned {new_modules.count()} module(s) to {employee.get_full_name() or employee.username}.')
        return redirect('employee_detail', user_id=employee.id)

    return render(request, 'accounts/assign_training.html', {
        'profile': profile,
        'employee': employee,
        'modules': modules,
        'already_assigned_ids': already_assigned_ids,
    })