import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Profile
from accounts.utils import compute_security_stats
from dashboard.models import SecurityScoreSnapshot
from training.models import TrainingModule, UserProgress
from phishing.models import EmailTemplate, PhishingCampaign, PhishingResult

PASSWORD = 'testpass123'

EMPLOYEES = [
    ('jane_employee', 'Jane', 'Smith'),
    ('mark_employee', 'Mark', 'Johnson'),
    ('priya_employee', 'Priya', 'Patel'),
    ('carlos_employee', 'Carlos', 'Reyes'),
    ('sara_employee', 'Sara', 'Connor'),
]

CAMPAIGNS = [
    {'name': 'Q1 Email Phishing Test', 'start_days_ago': 90, 'end_days_ago': 83},
    {'name': 'Smishing Awareness Drill', 'start_days_ago': 60, 'end_days_ago': 53},
    {'name': 'Vishing Response Test', 'start_days_ago': 30, 'end_days_ago': 23},
]


class Command(BaseCommand):
    help = 'Seeds realistic, varied phishing + training analytics demo data.'

    def handle(self, *args, **options):
        random.seed()  # fresh variety each run, but each (employee, campaign) pair is independently rolled

        users = self._create_employees()
        template = self._get_or_create_template()
        created_by = self._pick_created_by(users)
        campaigns = self._create_campaigns(template, created_by)
        results_created = self._create_results(campaigns, users)
        progress_created = self._create_progress(users)
        snapshots_created = self._create_snapshots(users)

        self.stdout.write(self.style.SUCCESS(
            "\nSeed complete:\n"
            f"  Employee users available: {len(users)}\n"
            f"  Phishing campaigns: {len(campaigns)}\n"
            f"  Phishing results (re)created: {results_created}\n"
            f"  Training progress records (re)created: {progress_created}\n"
            f"  Security score snapshots (re)created: {snapshots_created}\n"
            f"\nLogin as any employee with password: {PASSWORD}\n"
            f"  Usernames: {', '.join(u.username for u in users)}"
        ))

    def _create_employees(self):
        users = []
        for username, first_name, last_name in EMPLOYEES:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@techstart-sme.example',
                    'first_name': first_name,
                    'last_name': last_name,
                },
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
                self.stdout.write(f'  Created user: {username}')
            else:
                self.stdout.write(f'  User already exists, reusing: {username}')

            Profile.objects.get_or_create(user=user, defaults={'role': 'employee'})
            users.append(user)
        return users

    def _get_or_create_template(self):
        template = EmailTemplate.objects.first()
        if template:
            return template
        return EmailTemplate.objects.create(
            name='IT Support Password Reset',
            subject_line='Action required: verify your password before it expires',
            sender_name='IT Support',
            sender_email='security@company-support.example',
            body_content=(
                'Your password is set to expire in 24 hours. Please '
                '[LINK]verify your account here[/LINK] to keep your access active.'
            ),
            link_text='Verify Account',
        )

    def _pick_created_by(self, users):
        admin_profile = Profile.objects.filter(role='admin').first()
        if admin_profile:
            return admin_profile.user
        superuser = User.objects.filter(is_superuser=True).first()
        if superuser:
            return superuser
        return users[0]

    def _create_campaigns(self, template, created_by):
        now = timezone.now()
        campaigns = []
        for spec in CAMPAIGNS:
            campaign, created = PhishingCampaign.objects.get_or_create(
                name=spec['name'],
                defaults={
                    'description': f"Simulated phishing exercise: {spec['name']}.",
                    'template': template,
                    'created_by': created_by,
                    'status': 'completed',
                    'start_date': now - timedelta(days=spec['start_days_ago']),
                    'end_date': now - timedelta(days=spec['end_days_ago']),
                },
            )
            if created:
                self.stdout.write(f"  Created campaign: {campaign.name}")
            else:
                self.stdout.write(f"  Campaign already exists, reusing: {campaign.name}")
            campaigns.append(campaign)
        return campaigns

    def _create_results(self, campaigns, users):
        created_count = 0
        for campaign in campaigns:
            # This command owns the results for the campaigns it seeds — clear and
            # regenerate them each run so re-running stays varied and never duplicates.
            campaign.results.filter(employee__in=users).delete()

            for employee in users:
                roll = random.random()
                if roll < 0.40:
                    clicked, reported = True, False
                elif roll < 0.70:
                    clicked, reported = False, True
                else:
                    clicked, reported = False, False

                clicked_at = None
                if clicked:
                    window = max((campaign.end_date - campaign.start_date).total_seconds(), 3600)
                    clicked_at = campaign.start_date + timedelta(seconds=random.uniform(0, window))

                PhishingResult.objects.create(
                    campaign=campaign,
                    employee=employee,
                    clicked_link=clicked,
                    clicked_at=clicked_at,
                    reported_suspicious=reported,
                )
                created_count += 1
        return created_count

    def _create_progress(self, users):
        modules = list(TrainingModule.objects.all())
        if not modules:
            self.stdout.write('  No TrainingModule records found — skipping training progress seed.')
            return 0

        UserProgress.objects.filter(user__in=users, module__in=modules).delete()

        created_count = 0
        for user in users:
            num_to_assign = random.randint(1, len(modules))
            chosen_modules = random.sample(modules, num_to_assign)
            for module in chosen_modules:
                completed = random.random() < 0.7
                score = random.randint(55, 100) if completed else 0
                UserProgress.objects.create(
                    user=user,
                    module=module,
                    completed=completed,
                    score=score,
                    completed_at=timezone.now() - timedelta(days=random.randint(1, 60)) if completed else None,
                )
                created_count += 1
        return created_count

    def _create_snapshots(self, users):
        """Backfill 4-5 weekly SecurityScoreSnapshot rows per user, gently trending
        up toward their current computed score, so the "over time" charts have
        something real to plot immediately."""
        SecurityScoreSnapshot.objects.filter(user__in=users).delete()

        now = timezone.now()
        created_count = 0
        for user in users:
            final_score = compute_security_stats(user)['security_score']
            num_points = random.randint(4, 5)
            start_score = max(final_score - random.randint(15, 30), 5)

            for i in range(num_points):
                days_ago = (num_points - 1 - i) * 7 + random.randint(-1, 1)
                progress_fraction = i / (num_points - 1) if num_points > 1 else 1
                score = start_score + (final_score - start_score) * progress_fraction
                score = round(max(0, min(100, score + random.uniform(-3, 3))))

                snapshot = SecurityScoreSnapshot.objects.create(user=user, score=score)
                SecurityScoreSnapshot.objects.filter(pk=snapshot.pk).update(
                    recorded_at=now - timedelta(days=max(days_ago, 0))
                )
                created_count += 1
        return created_count
