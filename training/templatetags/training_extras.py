from django import template

register = template.Library()

# Category -> illustrative red-flags diagram, relative to the static root.
# Categories with no entry here simply show no diagram section.
CATEGORY_DIAGRAMS = {
    'phishing': 'img/diagrams/phishing_email_red_flags.svg',
    'smishing': 'img/diagrams/smishing_red_flags.svg',
    'vishing': 'img/diagrams/vishing_red_flags.svg',
    'social_engineering': 'img/diagrams/social_engineering_red_flags.svg',
    'password_security': 'img/diagrams/password_security_red_flags.svg',
    'popup_phishing': 'img/diagrams/popup_phishing_red_flags.svg',
    'evil_twin_phishing': 'img/diagrams/evil_twin_red_flags.svg',
}


@register.simple_tag
def category_diagram(category):
    """Static path of the red-flags diagram for a module category, or '' if none exists."""
    return CATEGORY_DIAGRAMS.get(category, '')
