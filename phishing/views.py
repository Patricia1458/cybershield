import re

from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe

from accounts.views import is_admin
from accounts.utils import log_activity
from .models import PhishingCampaign, PhishingResult

# Marks the phrase in EmailTemplate.body_content that should render as the
# actual tracked link, e.g. "...please [LINK]verify your account here[/LINK]..."
_INLINE_LINK_PATTERN = re.compile(r'\[LINK\](.*?)\[/LINK\]')


def _render_body_with_inline_link(body_content, track_url):
    """Escape the plain-text body, then turn its [LINK]...[/LINK] marker (if any)
    into a real anchor tag, so the malicious link reads as an ordinary inline
    hyperlink within the sentence rather than a separate labeled button."""
    escaped = escape(body_content)

    def _replace(match):
        return f'<a href="{track_url}" class="phishing-inline-link">{match.group(1)}</a>'

    return mark_safe(_INLINE_LINK_PATTERN.sub(_replace, escaped))


@login_required
@user_passes_test(is_admin)
def campaign_list(request):
    organization = request.user.profile.organization
    campaigns = PhishingCampaign.objects.filter(created_by__profile__organization=organization)
    return render(request, 'phishing/campaign_list.html', {'campaigns': campaigns})


@login_required
@user_passes_test(is_admin)
def campaign_detail(request, campaign_id):
    organization = request.user.profile.organization
    campaign = get_object_or_404(
        PhishingCampaign, id=campaign_id, created_by__profile__organization=organization
    )
    results = campaign.results.select_related('employee').all()

    results_with_links = []
    for result in results:
        link = request.build_absolute_uri(reverse('track_click', args=[result.tracking_token]))
        results_with_links.append({'result': result, 'link': link})

    return render(request, 'phishing/campaign_detail.html', {
        'campaign': campaign,
        'results_with_links': results_with_links,
    })


def _next_unactioned_result(employee, current_result):
    """The next PhishingResult for this employee that hasn't been clicked or
    reported yet — used to drive the "Next Simulation" link after one is actioned."""
    return (
        PhishingResult.objects.filter(employee=employee, clicked_link=False, reported_suspicious=False)
        .exclude(id=current_result.id)
        .order_by('email_sent_at')
        .first()
    )


def track_click(request, token):
    result = get_object_or_404(PhishingResult, tracking_token=token)
    if not result.clicked_link:
        result.clicked_link = True
        result.clicked_at = timezone.now()
        result.save()

        organization = getattr(getattr(result.employee, 'profile', None), 'organization', None)
        display_name = result.employee.get_full_name() or result.employee.username
        log_activity(organization, result.employee, f"{display_name} clicked a simulated phishing link")

    next_result = _next_unactioned_result(result.employee, result)
    return render(request, 'phishing/caught.html', {'result': result, 'next_result': next_result})


@login_required
def my_phishing_view(request):
    results = PhishingResult.objects.filter(employee=request.user).select_related('campaign', 'campaign__template').order_by('-email_sent_at')
    return render(request, 'phishing/my_simulations.html', {'results': results})


@login_required
def simulation_detail(request, token):
    result = get_object_or_404(
        PhishingResult.objects.select_related('campaign', 'campaign__template'),
        tracking_token=token,
        employee=request.user,
    )

    voicemail_duration = None
    if result.campaign.template.channel == 'voice':
        # A short, plausible-looking call duration for the training UI — purely
        # cosmetic flavor text, not a claimed real statistic.
        seconds = 20 + (len(result.campaign.template.body_content) % 40)
        voicemail_duration = f"0:{seconds:02d}"

    track_url = reverse('track_click', args=[result.tracking_token])
    body_html = _render_body_with_inline_link(result.campaign.template.body_content, track_url)

    next_result = None
    if result.clicked_link or result.reported_suspicious:
        next_result = _next_unactioned_result(result.employee, result)

    return render(request, 'phishing/simulation_detail.html', {
        'result': result,
        'voicemail_duration': voicemail_duration,
        'body_html': body_html,
        'next_result': next_result,
    })


@require_POST
def report_suspicious(request, token):
    result = get_object_or_404(PhishingResult, tracking_token=token)
    if not result.reported_suspicious:
        # If they already clicked, reporting after the fact doesn't undo that —
        # clicked_link stays as-is — but it's still worth recording that they
        # eventually recognized it, so reported_suspicious can still be set.
        result.reported_suspicious = True
        result.save()

        organization = getattr(getattr(result.employee, 'profile', None), 'organization', None)
        display_name = result.employee.get_full_name() or result.employee.username
        log_activity(organization, result.employee, f"{display_name} reported a simulated phishing email")

    next_result = _next_unactioned_result(result.employee, result)
    return render(request, 'phishing/reported.html', {'result': result, 'next_result': next_result})


@login_required
@user_passes_test(is_admin)
def analytics_view(request):
    organization = request.user.profile.organization
    campaigns = list(
        PhishingCampaign.objects.filter(created_by__profile__organization=organization)
        .annotate(
            sent_count=Count('results'),
            clicked_count=Count('results', filter=Q(results__clicked_link=True)),
            reported_count=Count('results', filter=Q(results__reported_suspicious=True)),
        )
        .order_by('start_date')
    )
    all_results = PhishingResult.objects.filter(
        employee__profile__organization=organization
    ).select_related('campaign', 'employee')

    total_campaigns = len(campaigns)
    total_sent = all_results.count()
    total_clicked = all_results.filter(clicked_link=True).count()
    total_reported = all_results.filter(reported_suspicious=True).count()
    overall_click_rate = round((total_clicked / total_sent) * 100, 1) if total_sent else 0
    overall_report_rate = round((total_reported / total_sent) * 100, 1) if total_sent else 0

    chart_labels = []
    click_rates = []
    report_rates = []
    for campaign in campaigns:
        sent = campaign.sent_count
        chart_labels.append(campaign.name)
        click_rates.append(round((campaign.clicked_count / sent) * 100, 1) if sent else 0)
        report_rates.append(round((campaign.reported_count / sent) * 100, 1) if sent else 0)

    chart_data = {
        'labels': chart_labels,
        'click_rates': click_rates,
        'report_rates': report_rates,
    }

    employee_ids = all_results.values_list('employee_id', flat=True).distinct()
    employees = User.objects.filter(id__in=employee_ids).order_by('username')
    results_by_pair = {(r.employee_id, r.campaign_id): r for r in all_results}

    heatmap_rows = []
    for employee in employees:
        cells = []
        for campaign in campaigns:
            result = results_by_pair.get((employee.id, campaign.id))
            if result and result.reported_suspicious:
                status = 'reported'
            elif result and result.clicked_link:
                status = 'clicked'
            else:
                status = 'neutral'
            cells.append({'campaign': campaign, 'status': status})
        heatmap_rows.append({'employee': employee, 'cells': cells})

    return render(request, 'phishing/analytics.html', {
        'total_campaigns': total_campaigns,
        'total_sent': total_sent,
        'overall_click_rate': overall_click_rate,
        'overall_report_rate': overall_report_rate,
        'campaigns': campaigns,
        'heatmap_rows': heatmap_rows,
        'chart_data': chart_data,
    })
