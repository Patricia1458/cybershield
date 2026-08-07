from django.db import models
from django.contrib.auth.models import User


class TrainingModule(models.Model):
    CATEGORY_CHOICES = [
        ('phishing', 'Phishing'),
        ('smishing', 'Smishing'),
        ('vishing', 'Vishing'),
        ('social_engineering', 'Social Engineering'),
        ('password_security', 'Password Security'),
        ('popup_phishing', 'Pop-up Phishing'),
        ('evil_twin_phishing', 'Evil Twin Phishing'),
    ]
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='phishing')
    description = models.TextField()
    scenario = models.TextField()
    content = models.TextField(blank=True)
    best_practices = models.TextField(blank=True)
    difficulty = models.CharField(max_length=15, choices=DIFFICULTY_CHOICES, default='beginner')
    estimated_minutes = models.IntegerField(default=15)
    pass_mark = models.IntegerField(default=70)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class QuizQuestion(models.Model):
    module = models.ForeignKey(TrainingModule, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=300)
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_option = models.CharField(max_length=1, choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')])

    def __str__(self):
        return self.question_text


class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(TrainingModule, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.module.title}"


class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    module = models.ForeignKey(TrainingModule, on_delete=models.CASCADE, related_name='certificates')
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'module')

    def __str__(self):
        return f"{self.user.username} — {self.module.title}"


class TrainingAssignment(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_assignments')
    module = models.ForeignKey(TrainingModule, on_delete=models.CASCADE, related_name='assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.username} assigned {self.module.title}"
