from collections import defaultdict

from django.db.models import Avg
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from accounts.views import is_admin, _org_members
from accounts.models import ActivityLog
from accounts.utils import compute_security_stats, compute_badges
from training.models import TrainingModule, UserProgress
from phishing.models import PhishingResult
from .models import SecurityScoreSnapshot


@login_required
def dashboard_view(request):
    if is_admin(request.user):
        return _admin_dashboard(request)

    # Employee dashboard — unchanged from before the admin dashboard rebuild.
    progress = UserProgress.objects.filter(user=request.user).select_related('module')
    total_modules = TrainingModule.objects.count()
    completed_count = progress.filter(completed=True).count()
    completion_rate = round((completed_count / total_modules) * 100, 1) if total_modules else 0
    avg_quiz_score = round(
        progress.filter(completed=True).aggregate(avg=Avg('score'))['avg'] or 0, 1
    )
    results = PhishingResult.objects.filter(employee=request.user)

    total_sent = results.count()
    click_rate = round((results.filter(clicked_link=True).count() / total_sent) * 100, 1) if total_sent else 0
    report_rate = round((results.filter(reported_suspicious=True).count() / total_sent) * 100, 1) if total_sent else 0

    return render(request, 'dashboard/dashboard.html', {
        'progress': progress,
        'completion_rate': completion_rate,
        'avg_quiz_score': avg_quiz_score,
        'click_rate': click_rate,
        'report_rate': report_rate,
        'is_admin': False,
    })


def _admin_dashboard(request):
    organization = request.user.profile.organization
    total_modules = TrainingModule.objects.count()
    all_members = _org_members(organization, total_modules)
    total_employees = len(all_members)

    def org_avg(key):
        return round(sum(m[key] for m in all_members) / total_employees, 1) if total_employees else 0

    completion_rate = org_avg('completion_rate')
    avg_quiz_score = org_avg('avg_quiz_score')
    click_rate = org_avg('click_rate')
    report_rate = org_avg('report_rate')
    at_risk_count = sum(1 for m in all_members if m['risk'] == 'high')

    risk_order = {'high': 0, 'medium': 1, 'low': 2}
    attention_rows = sorted(all_members, key=lambda m: risk_order.get(m['risk'], 3))[:5]

    org_user_ids = [m['profile'].user_id for m in all_members]

    now = timezone.now()
    weekly_buckets = defaultdict(list)
    for snapshot in SecurityScoreSnapshot.objects.filter(user_id__in=org_user_ids):
        weeks_ago = (now - snapshot.recorded_at).days // 7
        weekly_buckets[weeks_ago].append(snapshot.score)
    sorted_weeks = sorted(weekly_buckets.keys(), reverse=True)
    progress_chart = {
        'labels': ['This week' if w == 0 else f'{w}w ago' for w in sorted_weeks],
        'scores': [round(sum(weekly_buckets[w]) / len(weekly_buckets[w])) for w in sorted_weeks],
    }

    org_results = PhishingResult.objects.filter(employee_id__in=org_user_ids)
    sent = org_results.count()
    reported = org_results.filter(reported_suspicious=True).count()
    clicked_only = org_results.filter(clicked_link=True, reported_suspicious=False).count()
    no_action = sent - reported - clicked_only
    phishing_chart = {
        'labels': ['Sent', 'Clicked', 'Reported', 'No Action'],
        'values': [sent, clicked_only, reported, no_action],
    }

    recent_activity = ActivityLog.objects.filter(organization=organization).select_related('user').order_by('-created_at')[:5]

    return render(request, 'dashboard/admin_dashboard.html', {
        'organization': organization,
        'total_employees': total_employees,
        'completion_rate': completion_rate,
        'avg_quiz_score': avg_quiz_score,
        'click_rate': click_rate,
        'report_rate': report_rate,
        'at_risk_count': at_risk_count,
        'attention_rows': attention_rows,
        'progress_chart': progress_chart,
        'has_progress_chart': bool(sorted_weeks),
        'phishing_chart': phishing_chart,
        'has_phishing_data': sent > 0,
        'recent_activity': recent_activity,
    })


@login_required
def my_progress_view(request):
    stats = compute_security_stats(request.user)
    badges = compute_badges(request.user, stats=stats)
    earned_count = sum(1 for b in badges if b['earned'])

    snapshots = list(SecurityScoreSnapshot.objects.filter(user=request.user).order_by('recorded_at'))
    chart_data = {
        'labels': [s.recorded_at.strftime('%b %d').replace(' 0', ' ') for s in snapshots],
        'scores': [s.score for s in snapshots],
    }
    growth = (snapshots[-1].score - snapshots[0].score) if len(snapshots) >= 2 else 0

    category_labels = dict(TrainingModule.CATEGORY_CHOICES)
    completed_progress = UserProgress.objects.filter(
        user=request.user, completed=True
    ).select_related('module')

    category_scores = {}
    for p in completed_progress:
        category_scores.setdefault(p.module.category, []).append(p.score)

    categories = []
    for category, scores in category_scores.items():
        categories.append({
            'category': category,
            'label': category_labels.get(category, category),
            'avg_score': round(sum(scores) / len(scores)),
        })
    categories.sort(key=lambda c: c['avg_score'])

    weakest_category = categories[0] if categories else None
    weakest_module = None
    if weakest_category:
        weakest_module = TrainingModule.objects.filter(category=weakest_category['category']).first()

    return render(request, 'dashboard/my_progress.html', {
        **stats,
        'badges': badges,
        'earned_count': earned_count,
        'chart_data': chart_data,
        'growth': growth,
        'has_snapshots': len(snapshots) >= 2,
        'categories': categories,
        'weakest_category': weakest_category,
        'weakest_module': weakest_module,
    })


@login_required
def my_analytics_view(request):
    modules = TrainingModule.objects.all()
    progress_by_module = {
        p.module_id: p for p in UserProgress.objects.filter(user=request.user)
    }

    module_progress = []
    for module in modules:
        p = progress_by_module.get(module.id)
        module_progress.append({
            'module': module,
            'completed': p.completed if p else False,
            'score': p.score if p else 0,
        })

    total_modules = len(module_progress)
    completed_count = sum(1 for m in module_progress if m['completed'])
    completion_rate = round((completed_count / total_modules) * 100, 1) if total_modules else 0

    completed_scores = [m['score'] for m in module_progress if m['completed']]
    avg_quiz_score = round(sum(completed_scores) / len(completed_scores), 1) if completed_scores else 0

    results = PhishingResult.objects.filter(employee=request.user)
    total_received = results.count()
    reported_count = results.filter(reported_suspicious=True).count()
    clicked_only_count = results.filter(clicked_link=True, reported_suspicious=False).count()
    no_action_count = total_received - reported_count - clicked_only_count
    detection_rate = round((reported_count / total_received) * 100, 1) if total_received else 0

    chart_data = {
        'labels': ['Clicked', 'Reported', 'No Action'],
        'values': [clicked_only_count, reported_count, no_action_count],
    }

    return render(request, 'dashboard/my_analytics.html', {
        'module_progress': module_progress,
        'total_modules': total_modules,
        'completed_count': completed_count,
        'completion_rate': completion_rate,
        'avg_quiz_score': avg_quiz_score,
        'total_received': total_received,
        'reported_count': reported_count,
        'clicked_only_count': clicked_only_count,
        'no_action_count': no_action_count,
        'detection_rate': detection_rate,
        'chart_data': chart_data,
    })
