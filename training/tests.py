from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Organization, Profile
from .models import Certificate, QuizQuestion, TrainingModule, UserProgress


def _make_module(pass_mark=70):
    return TrainingModule.objects.create(
        title='Recognizing Phishing',
        category='phishing',
        description='desc',
        scenario='scenario',
        pass_mark=pass_mark,
    )


def _make_question(module, correct='a'):
    return QuizQuestion.objects.create(
        module=module,
        question_text='Is this suspicious?',
        option_a='Yes', option_b='No', option_c='Maybe', option_d='Unsure',
        correct_option=correct,
    )


class UserProgressStagedProgressTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Acme')
        self.user = User.objects.create_user(username='progressuser', password='SecurePass123!')
        Profile.objects.create(user=self.user, role='employee', organization=self.org)
        self.module = _make_module()

    def test_no_record_defaults_not_started(self):
        # No UserProgress row at all — templates handle this as 0% / Not Started
        # themselves (there's no instance to call the method on).
        self.assertFalse(UserProgress.objects.filter(user=self.user, module=self.module).exists())

    def test_nothing_viewed_is_not_started(self):
        progress = UserProgress.objects.create(user=self.user, module=self.module)
        self.assertEqual(progress.progress_percent(), 0)
        self.assertEqual(progress.progress_label(), 'Not Started · 0%')
        self.assertEqual(progress.progress_badge_class(), 'badge-neutral')

    def test_content_viewed_is_33_percent(self):
        progress = UserProgress.objects.create(user=self.user, module=self.module, viewed_content=True)
        self.assertEqual(progress.progress_percent(), 33)
        self.assertEqual(progress.progress_label(), 'In Progress · 33%')
        self.assertEqual(progress.progress_badge_class(), 'badge-warning')

    def test_content_and_scenario_viewed_is_66_percent(self):
        progress = UserProgress.objects.create(
            user=self.user, module=self.module, viewed_content=True, viewed_scenario=True,
        )
        self.assertEqual(progress.progress_percent(), 66)
        self.assertEqual(progress.progress_label(), 'In Progress · 66%')
        self.assertEqual(progress.progress_badge_class(), 'badge-warning')

    def test_completed_with_perfect_score_shows_completed_pill(self):
        progress = UserProgress.objects.create(
            user=self.user, module=self.module, completed=True, score=100,
            viewed_content=True, viewed_scenario=True,
        )
        self.assertEqual(progress.progress_percent(), 100)
        self.assertEqual(progress.progress_label(), 'Completed · 100%')
        self.assertEqual(progress.progress_badge_class(), 'badge-success')

    def test_completed_with_partial_score_shows_bare_score(self):
        progress = UserProgress.objects.create(
            user=self.user, module=self.module, completed=True, score=70,
            viewed_content=True, viewed_scenario=True,
        )
        self.assertEqual(progress.progress_percent(), 70)
        self.assertEqual(progress.progress_label(), '70%')
        self.assertEqual(progress.progress_badge_class(), 'badge-warning')


@override_settings(AXES_ENABLED=False)
class MarkViewedTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Acme')
        self.user = User.objects.create_user(username='vieweruser', password='SecurePass123!')
        Profile.objects.create(user=self.user, role='employee', organization=self.org)
        self.client.login(username='vieweruser', password='SecurePass123!')
        self.module = _make_module()

    def test_marking_content_viewed_creates_progress_record(self):
        response = self.client.post(reverse('mark_viewed', args=[self.module.id, 'content']))
        self.assertEqual(response.status_code, 200)
        progress = UserProgress.objects.get(user=self.user, module=self.module)
        self.assertTrue(progress.viewed_content)
        self.assertFalse(progress.viewed_scenario)
        self.assertEqual(response.json()['progress_percent'], 33)

    def test_marking_both_tabs_viewed_reaches_66_percent(self):
        self.client.post(reverse('mark_viewed', args=[self.module.id, 'content']))
        response = self.client.post(reverse('mark_viewed', args=[self.module.id, 'scenario']))
        progress = UserProgress.objects.get(user=self.user, module=self.module)
        self.assertTrue(progress.viewed_content)
        self.assertTrue(progress.viewed_scenario)
        self.assertEqual(response.json()['progress_percent'], 66)

    def test_invalid_tab_rejected(self):
        response = self.client.post(reverse('mark_viewed', args=[self.module.id, 'nonsense']))
        self.assertEqual(response.status_code, 400)

    def test_get_not_allowed(self):
        response = self.client.get(reverse('mark_viewed', args=[self.module.id, 'content']))
        self.assertEqual(response.status_code, 405)


class ModuleQuestionLinkTests(TestCase):
    def test_module_questions_related_manager_returns_correct_count(self):
        module = _make_module()
        _make_question(module)
        _make_question(module)
        _make_question(module)
        self.assertEqual(module.questions.all().count(), 3)
        self.assertEqual(list(module.questions.all()), list(QuizQuestion.objects.filter(module=module)))


# self.client.login() bypasses the request object django-axes needs; disabled
# here since these tests are about quiz-taking, not login/lockout behavior.
@override_settings(AXES_ENABLED=False)
class TakeQuizTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Acme')
        self.user = User.objects.create_user(username='quiztaker', password='SecurePass123!')
        Profile.objects.create(user=self.user, role='employee', organization=self.org)
        self.client.login(username='quiztaker', password='SecurePass123!')

        self.module = _make_module(pass_mark=70)
        self.q1 = _make_question(self.module, correct='a')
        self.q2 = _make_question(self.module, correct='b')

    def test_all_correct_answers_completes_and_passes(self):
        response = self.client.post(reverse('take_quiz', args=[self.module.id]), {
            f'question_{self.q1.id}': 'a',
            f'question_{self.q2.id}': 'b',
        })
        self.assertEqual(response.status_code, 200)

        progress = UserProgress.objects.get(user=self.user, module=self.module)
        self.assertTrue(progress.completed)
        self.assertEqual(progress.score, 100)
        self.assertTrue(progress.passed)

    def test_failing_score_does_not_create_certificate(self):
        self.client.post(reverse('take_quiz', args=[self.module.id]), {
            f'question_{self.q1.id}': 'b',  # wrong
            f'question_{self.q2.id}': 'a',  # wrong
        })
        progress = UserProgress.objects.get(user=self.user, module=self.module)
        self.assertFalse(progress.passed)
        self.assertFalse(Certificate.objects.filter(user=self.user, module=self.module).exists())

    def test_passing_score_creates_certificate(self):
        self.client.post(reverse('take_quiz', args=[self.module.id]), {
            f'question_{self.q1.id}': 'a',
            f'question_{self.q2.id}': 'b',
        })
        self.assertTrue(Certificate.objects.filter(user=self.user, module=self.module).exists())

    def test_unauthenticated_user_redirected_from_take_quiz(self):
        self.client.logout()
        response = self.client.get(reverse('take_quiz', args=[self.module.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


# self.client.login() bypasses the request object django-axes needs; disabled
# here since these tests are about certificate access control, not login/lockout.
@override_settings(AXES_ENABLED=False)
class CertificatePdfTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Acme')
        self.owner = User.objects.create_user(
            username='certowner', password='SecurePass123!', first_name='Casey', last_name='Owner',
        )
        Profile.objects.create(user=self.owner, role='employee', organization=self.org)

        self.other_org = Organization.objects.create(name='OtherCo')
        self.stranger = User.objects.create_user(username='certstranger', password='SecurePass123!')
        Profile.objects.create(user=self.stranger, role='employee', organization=self.other_org)

        self.module = _make_module()
        self.certificate = Certificate.objects.create(user=self.owner, module=self.module)

    def test_owner_can_download_pdf(self):
        self.client.login(username='certowner', password='SecurePass123!')
        response = self.client.get(reverse('certificate_pdf', args=[self.certificate.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])

    def test_other_user_denied(self):
        self.client.login(username='certstranger', password='SecurePass123!')
        response = self.client.get(reverse('certificate_pdf', args=[self.certificate.id]))
        self.assertEqual(response.status_code, 403)
