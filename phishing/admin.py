from django.contrib import admin
from .models import EmailTemplate, PhishingCampaign, PhishingResult

admin.site.register(EmailTemplate)
admin.site.register(PhishingCampaign)
admin.site.register(PhishingResult)