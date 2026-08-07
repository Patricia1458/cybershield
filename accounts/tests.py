from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Organization, Profile
from .views import is_admin


class RegistrationTests(TestCase):
    def test_register_creates_user_profile_and_organization(self):
        response = self.client.post(reverse('register'), {
            'username': 'neworgadmin',
            'email': 'neworgadmin@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'organization_name': 'Test Org',
            'terms': 'on',
        })
        self.assertEqual(response.status_code, 302)

        user = User.objects.get(username='neworgadmin')
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.role, 'admin')
        self.assertIsNotNone(profile.organization)
        self.assertEqual(profile.organization.name, 'Test Org')
        self.assertTrue(Organization.objects.filter(name='Test Org').exists())


# django-axes' backend requires a real request object to check lockout status,
# which the self.client.login() shortcut doesn't provide — so tests that use
# that shortcut (rather than posting to the login view) disable axes, since
# they're testing unrelated things. Axes' own behavior is covered separately
# by AxesLockoutTests below, which posts to the real login view.
@override_settings(AXES_ENABLED=False)
class LoginTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Acme')
        self.user = User.objects.create_user(username='loginadmin', password='SecurePass123!')
        Profile.objects.create(user=self.user, role='admin', organization=self.org)

    def test_login_success(self):
        self.assertTrue(self.client.login(username='loginadmin', password='SecurePass123!'))

    def test_login_wrong_password_fails(self):
        self.assertFalse(self.client.login(username='loginadmin', password='WrongPassword1!'))


class IsAdminHelperTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Acme')

    def test_is_admin_true_for_admin_profile(self):
        user = User.objects.create_user(username='adminhelper', password='x')
        Profile.objects.create(user=user, role='admin', organization=self.org)
        self.assertTrue(is_admin(user))

    def test_is_admin_false_for_employee_profile(self):
        user = User.objects.create_user(username='employeehelper', password='x')
        Profile.objects.create(user=user, role='employee', organization=self.org)
        self.assertFalse(is_admin(user))


@override_settings(AXES_ENABLED=False)
class InviteEmployeeTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Acme')
        self.admin = User.objects.create_user(username='inviteadmin', password='SecurePass123!')
        Profile.objects.create(user=self.admin, role='admin', organization=self.org)
        self.client.login(username='inviteadmin', password='SecurePass123!')

    def test_invite_creates_employee_linked_to_organization(self):
        response = self.client.post(reverse('invite_employee'), {
            'employee_name': 'Jane Doe',
            'employee_email': 'jane.doe@acme.example',
            'personal_message': '',
        })
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(username='jane.doe@acme.example')
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.role, 'employee')
        self.assertEqual(profile.organization, self.org)


@override_settings(AXES_ENABLED=False)
class AdminOnlyAccessTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Acme')
        self.admin = User.objects.create_user(username='accessadmin', password='SecurePass123!')
        Profile.objects.create(user=self.admin, role='admin', organization=self.org)
        self.employee = User.objects.create_user(username='accessemployee', password='SecurePass123!')
        Profile.objects.create(user=self.employee, role='employee', organization=self.org)

    def test_employee_cannot_access_employee_list(self):
        self.client.login(username='accessemployee', password='SecurePass123!')
        response = self.client.get(reverse('employee_list'))
        self.assertIn(response.status_code, (302, 403))

    def test_employee_cannot_access_invite_employee(self):
        self.client.login(username='accessemployee', password='SecurePass123!')
        response = self.client.get(reverse('invite_employee'))
        self.assertIn(response.status_code, (302, 403))

    def test_admin_can_access_employee_list(self):
        self.client.login(username='accessadmin', password='SecurePass123!')
        response = self.client.get(reverse('employee_list'))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_invite_employee(self):
        self.client.login(username='accessadmin', password='SecurePass123!')
        response = self.client.get(reverse('invite_employee'))
        self.assertEqual(response.status_code, 200)


class AxesLockoutTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Acme')
        self.user = User.objects.create_user(username='lockoutuser', password='SecurePass123!')
        Profile.objects.create(user=self.user, role='employee', organization=self.org)

    def test_five_failed_logins_locks_account(self):
        for _ in range(5):
            self.client.post(reverse('login'), {
                'username': 'lockoutuser',
                'password': 'WrongPassword!',
            })
        # The account should now be locked out for further attempts from this client.
        response = self.client.post(reverse('login'), {
            'username': 'lockoutuser',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 429)

    def test_sixth_attempt_blocked_even_with_correct_password(self):
        for _ in range(5):
            self.client.post(reverse('login'), {
                'username': 'lockoutuser',
                'password': 'WrongPassword!',
            })
        response = self.client.post(reverse('login'), {
            'username': 'lockoutuser',
            'password': 'SecurePass123!',
        })
        self.assertEqual(response.status_code, 429)
        # The correct-password attempt must not have actually authenticated them
        # (client.login() can't be used here — AxesBackend requires a real
        # request object, which the client.login() shortcut doesn't provide).
        self.assertNotIn('_auth_user_id', self.client.session)
