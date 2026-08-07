from django.db import models
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .fields import EncryptedCharField


class Organization(models.Model):
    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('employee', 'Employee'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('invited', 'Invited'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    company_name = models.CharField(max_length=100, default='TechStart SME')
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='profiles'
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    # Encrypted-at-rest mirror of user.email. Django's built-in User model can't be
    # modified directly, so this field is kept in sync (see save() below and the
    # post_save signal on User) and used anywhere the app displays the user's email.
    encrypted_email = EncryptedCharField(blank=True, default='')

    def save(self, *args, **kwargs):
        if self.user_id:
            self.encrypted_email = self.user.email
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class ActivityLog(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='activity_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    action = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.action


@receiver(post_save, sender=User)
def sync_profile_encrypted_email(sender, instance, **kwargs):
    """Keep Profile.encrypted_email in sync whenever the linked User's email changes."""
    Profile.objects.filter(user=instance).update(encrypted_email=instance.email)


@receiver(user_logged_in)
def activate_profile_on_first_login(sender, user, request, **kwargs):
    """An invited employee's status flips from 'invited' to 'active' the first time they log in."""
    Profile.objects.filter(user=user, status='invited').update(status='active')