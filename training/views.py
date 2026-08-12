from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.utils import timezone
from accounts.views import is_admin
from accounts.utils import record_security_snapshot, log_activity
from .certificates import render_certificate_pdf
from .models import TrainingModule, QuizQuestion, UserProgress, Certificate


def _can_view_certificate(user, certificate):
    if user == certificate.user:
        return True
    if is_admin(user):
        owner_org = getattr(getattr(certificate.user, 'profile', None), 'organization', None)
        viewer_org = getattr(getattr(user, 'profile', None), 'organization', None)
        return owner_org is not None and owner_org == viewer_org
    return False

@login_required
def module_list(request):
    modules = list(TrainingModule.objects.all())
    progress_by_module_id = {
        p.module_id: p
        for p in UserProgress.objects.filter(user=request.user, module__in=modules)
    }
    for module in modules:
        module.progress = progress_by_module_id.get(module.id)

    return render(request, 'training/module_list.html', {
        'modules': modules,
        'is_admin': is_admin(request.user),
    })


@login_required
def module_detail(request, module_id):
    module = get_object_or_404(TrainingModule, id=module_id)
    progress = UserProgress.objects.filter(user=request.user, module=module).first()
    return render(request, 'training/module_detail.html', {
        'module': module,
        'progress': progress,
    })


@login_required
@require_POST
def mark_viewed(request, module_id, tab):
    """Records that the employee has viewed the Content or Scenario tab of a
    module. Content and Scenario are both rendered in the same page load on
    module_detail.html (just toggled with CSS), so there's no separate
    server request per tab to hook into — the template's tab-switching JS
    pings this endpoint instead, once per tab shown."""
    if tab not in ('content', 'scenario'):
        return HttpResponseBadRequest('Unknown tab')

    module = get_object_or_404(TrainingModule, id=module_id)
    progress, _ = UserProgress.objects.get_or_create(user=request.user, module=module)

    field = 'viewed_content' if tab == 'content' else 'viewed_scenario'
    if not getattr(progress, field):
        setattr(progress, field, True)
        progress.save(update_fields=[field])

    return JsonResponse({'progress_percent': progress.progress_percent()})


@login_required
def take_quiz(request, module_id):
    module = get_object_or_404(TrainingModule, id=module_id)
    questions = module.questions.all()

    if request.method == 'POST':
        score = 0
        total = questions.count()

        for question in questions:
            selected = request.POST.get(f'question_{question.id}')
            if selected == question.correct_option:
                score += 1

        percentage = int((score / total) * 100) if total > 0 else 0

        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            module=module,
        )
        passed = percentage >= module.pass_mark

        progress.completed = True
        progress.score = percentage
        progress.passed = passed
        progress.completed_at = timezone.now()
        progress.save()

        if passed:
            Certificate.objects.get_or_create(user=request.user, module=module)

        record_security_snapshot(request.user)
        organization = getattr(getattr(request.user, 'profile', None), 'organization', None)
        display_name = request.user.get_full_name() or request.user.username
        log_activity(organization, request.user, f"{display_name} completed {module.title}")

        next_module = TrainingModule.objects.filter(id__gt=module.id).order_by('id').first()

        return render(request, 'training/quiz_result.html', {
            'module': module,
            'score': score,
            'total': total,
            'percentage': percentage,
            'passed': passed,
            'next_module': next_module,
        })

    progress = UserProgress.objects.filter(user=request.user, module=module).first()
    return render(request, 'training/take_quiz.html', {
        'module': module,
        'questions': questions,
        'progress': progress,
    })


@login_required
@user_passes_test(is_admin)
def create_module(request):
    if request.method == 'POST':
        module = TrainingModule.objects.create(
            title=request.POST.get('title', ''),
            category=request.POST.get('category', 'phishing'),
            description=request.POST.get('description', ''),
            content=request.POST.get('content', ''),
            scenario=request.POST.get('scenario', ''),
        )

        for i in range(1, 6):
            question_text = request.POST.get(f'q{i}_text', '').strip()
            if not question_text:
                continue
            QuizQuestion.objects.create(
                module=module,
                question_text=question_text,
                option_a=request.POST.get(f'q{i}_a', ''),
                option_b=request.POST.get(f'q{i}_b', ''),
                option_c=request.POST.get(f'q{i}_c', ''),
                option_d=request.POST.get(f'q{i}_d', ''),
                correct_option=request.POST.get(f'q{i}_correct', 'a'),
            )

        return redirect('module_list')

    return render(request, 'training/create_module.html', {
        'categories': TrainingModule.CATEGORY_CHOICES,
    })


@login_required
def my_certificates(request):
    certificates = Certificate.objects.filter(user=request.user).select_related('module').order_by('-issued_at')
    return render(request, 'training/my_certificates.html', {'certificates': certificates})


@login_required
def certificate_detail(request, certificate_id):
    certificate = get_object_or_404(Certificate, id=certificate_id)
    if not _can_view_certificate(request.user, certificate):
        return HttpResponseForbidden("You don't have permission to view this certificate.")
    return render(request, 'training/certificate_detail.html', {'certificate': certificate})


@login_required
def certificate_pdf(request, certificate_id):
    certificate = get_object_or_404(Certificate, id=certificate_id)
    if not _can_view_certificate(request.user, certificate):
        return HttpResponseForbidden("You don't have permission to view this certificate.")

    pdf_bytes = render_certificate_pdf(certificate)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_{certificate.id}.pdf"'
    return response