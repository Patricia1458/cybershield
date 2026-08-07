from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Organization, Profile
from .models import EmailTemplate, PhishingCampaign, PhishingResult


def _make_campaign(created_by, name='Q1 Phishing Test'):
    template = EmailTemplate.objects.create(
        name=f'{name} Template',
        subject_line='Urgent',
        sender_name='IT Support',
        body_content='Please [LINK]verify your account[/LINK] now.',
    )
    now = timezone.now()
    return PhishingCampaign.objects.create(
        name=name,
        template=template,
        created_by=created_by,
        status='active',
        start_date=now,
        end_date=now + timezone.timedelta(days=7),
    )


class PhishingResultTrackingTokenTests(TestCase):
    def test_tracking_token_is_generated_and_unique(self):
        org = Organization.objects.create(name='Acme')
        admin = User.objects.create_user(username='tokenadmin', password='x')
        Profile.objects.create(user=admin, role='admin', organization=org)
        campaign = _make_campaign(admin)

        employee1 = User.objects.create_user(username='tokenemp1', password='x')
        employee2 = User.objects.create_user(username='tokenemp2', password='x')
        result1 = PhishingResult.objects.create(campaign=campaign, employee=employee1)
        result2 = PhishingResult.objects.create(campaign=campaign, employee=employee2)

        self.assertIsNotNone(result1.tracking_token)
        self.assertNotEqual(result1.tracking_token, result2.tracking_token)


class TrackClickTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Acme')
        self.admin = User.objects.create_user(username='clickadmin', password='x')
        Profile.objects.create(user=self.admin, role='admin', organization=self.org)
        self.campaign = _make_campaign(self.admin)
        self.employee = User.objects.create_user(username='clickemp', password='x')
        self.result = PhishingResult.objects.create(campaign=self.campaign, employee=self.employee)

    def test_visiting_track_click_sets_clicked_link_and_timestamp(self):
        response = self.client.get(reverse('track_click', args=[self.result.tracking_token]))
        self.assertEqual(response.status_code, 200)

        self.result.refresh_from_db()
        self.assertTrue(self.result.clicked_link)
        self.assertIsNotNone(self.result.clicked_at)

    def test_second_visit_does_not_overwrite_original_clicked_at(self):
        self.client.get(reverse('track_click', args=[self.result.tracking_token]))
        self.result.refresh_from_db()
        first_clicked_at = self.result.clicked_at

        self.client.get(reverse('track_click', args=[self.result.tracking_token]))
        self.result.refresh_from_db()

        self.assertEqual(self.result.clicked_at, first_clicked_at)


class ReportSuspiciousTests(TestCase):
    def test_report_suspicious_sets_flag(self):
        org = Organization.objects.create(name='Acme')
        admin = User.objects.create_user(username='reportadmin', password='x')
        Profile.objects.create(user=admin, role='admin', organization=org)
        campaign = _make_campaign(admin)
        employee = User.objects.create_user(username='reportemp', password='x')
        result = PhishingResult.objects.create(campaign=campaign, employee=employee)

        response = self.client.post(reverse('report_suspicious', args=[result.tracking_token]))
        self.assertEqual(response.status_code, 200)

        result.refresh_from_db()
        self.assertTrue(result.reported_suspicious)


# self.client.login() bypasses the request object django-axes needs; disabled
# here since these tests are about data isolation, not login/lockout behavior.
@override_settings(AXES_ENABLED=False)
class MyPhishingViewIsolationTests(TestCase):
    def test_employee_only_sees_own_results(self):
        org = Organization.objects.create(name='Acme')
        admin = User.objects.create_user(username='isoadmin', password='x')
        Profile.objects.create(user=admin, role='admin', organization=org)
        campaign = _make_campaign(admin)

        employee1 = User.objects.create_user(username='isoemp1', password='SecurePass123!')
        Profile.objects.create(user=employee1, role='employee', organization=org)
        employee2 = User.objects.create_user(username='isoemp2', password='SecurePass123!')
        Profile.objects.create(user=employee2, role='employee', organization=org)

        result1 = PhishingResult.objects.create(campaign=campaign, employee=employee1)
        result2 = PhishingResult.objects.create(campaign=campaign, employee=employee2)

        self.client.login(username='isoemp1', password='SecurePass123!')
        response = self.client.get(reverse('my_simulations'))

        results_shown = list(response.context['results'])
        self.assertIn(result1, results_shown)
        self.assertNotIn(result2, results_shown)


@override_settings(AXES_ENABLED=False)
class CampaignAccessTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Acme')
        self.admin = User.objects.create_user(username='campadmin', password='SecurePass123!')
        Profile.objects.create(user=self.admin, role='admin', organization=self.org)
        self.employee = User.objects.create_user(username='campemp', password='SecurePass123!')
        Profile.objects.create(user=self.employee, role='employee', organization=self.org)
        self.campaign = _make_campaign(self.admin)

    def test_employee_blocked_from_campaign_list(self):
        self.client.login(username='campemp', password='SecurePass123!')
        response = self.client.get(reverse('campaign_list'))
        self.assertIn(response.status_code, (302, 403))

    def test_employee_blocked_from_campaign_detail(self):
        self.client.login(username='campemp', password='SecurePass123!')
        response = self.client.get(reverse('campaign_detail', args=[self.campaign.id]))
        self.assertIn(response.status_code, (302, 403))

    def test_admin_can_access_campaign_list(self):
        self.client.login(username='campadmin', password='SecurePass123!')
        response = self.client.get(reverse('campaign_list'))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_campaign_detail(self):
        self.client.login(username='campadmin', password='SecurePass123!')
        response = self.client.get(reverse('campaign_detail', args=[self.campaign.id]))
        self.assertEqual(response.status_code, 200)
