from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Organization, Profile
from phishing.models import EmailTemplate, PhishingCampaign, PhishingResult
from training.models import TrainingModule, UserProgress


def _make_module(title):
    return TrainingModule.objects.create(
        title=title, category='phishing', description='d', scenario='s',
    )


# self.client.login() bypasses the request object django-axes needs; disabled
# here since these tests are about per-user data isolation, not login/lockout.
@override_settings(AXES_ENABLED=False)
class DashboardIsolationTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Acme')

        self.employee1 = User.objects.create_user(username='dashemp1', password='SecurePass123!')
        Profile.objects.create(user=self.employee1, role='employee', organization=self.org)
        self.employee2 = User.objects.create_user(username='dashemp2', password='SecurePass123!')
        Profile.objects.create(user=self.employee2, role='employee', organization=self.org)

        self.module1 = _make_module('Module One')
        self.module2 = _make_module('Module Two')

        # employee1: one completed module, high score
        UserProgress.objects.create(user=self.employee1, module=self.module1, completed=True, score=100)
        # employee2: one completed module, low score
        UserProgress.objects.create(user=self.employee2, module=self.module1, completed=True, score=20)
        UserProgress.objects.create(user=self.employee2, module=self.module2, completed=True, score=40)

        admin = User.objects.create_user(username='dashadmin', password='x')
        Profile.objects.create(user=admin, role='admin', organization=self.org)
        template = EmailTemplate.objects.create(
            name='T', subject_line='s', sender_name='s', body_content='b',
        )
        now = timezone.now()
        campaign = PhishingCampaign.objects.create(
            name='C', template=template, created_by=admin, status='active',
            start_date=now, end_date=now + timezone.timedelta(days=1),
        )
        PhishingResult.objects.create(campaign=campaign, employee=self.employee1, clicked_link=True)
        PhishingResult.objects.create(campaign=campaign, employee=self.employee2, clicked_link=False)

    def test_dashboard_view_only_reflects_requesting_user(self):
        self.client.login(username='dashemp1', password='SecurePass123!')
        response1 = self.client.get(reverse('dashboard'))
        self.assertEqual(response1.context['avg_quiz_score'], 100)
        self.assertEqual(response1.context['click_rate'], 100.0)

        self.client.login(username='dashemp2', password='SecurePass123!')
        response2 = self.client.get(reverse('dashboard'))
        self.assertEqual(response2.context['avg_quiz_score'], 30)
        self.assertEqual(response2.context['click_rate'], 0.0)

    def test_my_analytics_view_only_reflects_requesting_user(self):
        self.client.login(username='dashemp1', password='SecurePass123!')
        response1 = self.client.get(reverse('my_analytics'))
        self.assertEqual(response1.context['avg_quiz_score'], 100)
        self.assertEqual(response1.context['completed_count'], 1)

        self.client.login(username='dashemp2', password='SecurePass123!')
        response2 = self.client.get(reverse('my_analytics'))
        self.assertEqual(response2.context['avg_quiz_score'], 30)
        self.assertEqual(response2.context['completed_count'], 2)
