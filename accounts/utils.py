from training.models import TrainingModule, UserProgress
from phishing.models import PhishingResult


def compute_security_stats(user):
    """Real, database-computed training/phishing stats for one user.

    Shared by the profile page, the employee "My Progress" page, and the
    security-score snapshot logging, so all three agree on one definition.
    """
    total_modules = TrainingModule.objects.count()
    progress = UserProgress.objects.filter(user=user)

    completed_count = progress.filter(completed=True).count()
    completion_rate = round((completed_count / total_modules) * 100) if total_modules else 0

    completed_scores = list(progress.filter(completed=True).values_list('score', flat=True))
    avg_quiz_score = round(sum(completed_scores) / len(completed_scores)) if completed_scores else 0

    # There is no "legitimate control message" concept in this data model
    # (no EmailTemplate.is_legitimate field) — every PhishingResult here is a
    # real simulated phishing test, so all of a user's results count.
    results = PhishingResult.objects.filter(employee=user)
    total_results = results.count()
    reported_count = results.filter(reported_suspicious=True).count()
    detection_rate = round((reported_count / total_results) * 100) if total_results else 0

    security_score = round((completion_rate + avg_quiz_score + detection_rate) / 3)

    return {
        'completion_rate': completion_rate,
        'avg_quiz_score': avg_quiz_score,
        'detection_rate': detection_rate,
        'security_score': security_score,
        'reported_count': reported_count,
        'total_results': total_results,
        'completed_count': completed_count,
        'total_modules': total_modules,
    }


def compute_badges(user, stats=None):
    """The 5 achievement badges, computed dynamically from real data (no Badge model)."""
    stats = stats or compute_security_stats(user)
    progress = UserProgress.objects.filter(user=user)
    url_inspector_earned = (
        progress.filter(module__category='popup_phishing', completed=True).exists()
        and progress.filter(module__category='evil_twin_phishing', completed=True).exists()
    )

    return [
        {'label': 'Phishing Detective', 'earned': stats['reported_count'] >= 1},
        {'label': 'Security Guardian', 'earned': stats['security_score'] >= 80},
        {'label': 'URL Inspector', 'earned': url_inspector_earned},
        {'label': 'Threat Reporter', 'earned': stats['reported_count'] >= 3},
        {'label': 'Phish Hunter', 'earned': stats['detection_rate'] == 100 and stats['total_results'] >= 3},
    ]


def log_activity(organization, user, action):
    """Record one line of org activity. No-op if there's no organization to attach it to."""
    from .models import ActivityLog
    if organization is None:
        return None
    return ActivityLog.objects.create(organization=organization, user=user, action=action)


def record_security_snapshot(user):
    """Compute the user's current security score and store a snapshot of it."""
    from dashboard.models import SecurityScoreSnapshot
    stats = compute_security_stats(user)
    SecurityScoreSnapshot.objects.create(user=user, score=stats['security_score'])
    return stats
