from django.contrib import admin
from .models import TrainingModule, QuizQuestion, UserProgress, TrainingAssignment, Certificate

admin.site.register(TrainingModule)
admin.site.register(QuizQuestion)
admin.site.register(UserProgress)
admin.site.register(TrainingAssignment)
admin.site.register(Certificate)