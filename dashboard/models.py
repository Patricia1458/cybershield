from django.db import models
from django.contrib.auth.models import User


class SecurityScoreSnapshot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_score_snapshots')
    score = models.IntegerField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.score} @ {self.recorded_at:%Y-%m-%d}"
