from django.contrib import admin
from .models import Profile, ActivityLog, Organization

admin.site.register(Profile)
admin.site.register(ActivityLog)
admin.site.register(Organization)