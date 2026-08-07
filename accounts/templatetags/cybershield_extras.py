from django import template
from django.utils import timezone

register = template.Library()


@register.simple_tag
def time_greeting():
    """Local-time-aware greeting: morning <12:00, afternoon 12:00-16:59, evening >=17:00."""
    hour = timezone.localtime().hour
    if hour < 12:
        return 'Good morning'
    if hour < 17:
        return 'Good afternoon'
    return 'Good evening'
