import uuid
from django.db import models
from django.contrib.auth.models import User


class EmailTemplate(models.Model):
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('voice', 'Voice'),
    ]
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('hard', 'Hard'),
    ]

    name = models.CharField(max_length=150)
    subject_line = models.CharField(max_length=200)
    sender_name = models.CharField(max_length=100, help_text="e.g. 'IT Support'")
    sender_email = models.EmailField(default='security@company-support.example')
    body_content = models.TextField(help_text="The email body shown to the employee")
    link_text = models.CharField(max_length=100, default='Verify Account')
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='email')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class PhishingCampaign(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        return self.name


class PhishingResult(models.Model):
    campaign = models.ForeignKey(PhishingCampaign, on_delete=models.CASCADE, related_name='results')
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    tracking_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email_sent_at = models.DateTimeField(auto_now_add=True)
    clicked_link = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)
    reported_suspicious = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.employee.username} - {self.campaign.name}"
