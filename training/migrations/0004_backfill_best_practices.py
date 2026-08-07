from django.db import migrations

BEST_PRACTICES_TEXT = (
    "Best Practices for Preventing Phishing Attacks\n\n"
    "Pay Attention to the Language in Emails: Social engineering exploits human fallibility, especially "
    "when people feel rushed. Be alert to a fake order (impersonating a courier to steal login "
    "credentials), business email compromise (impersonating an executive to instruct urgent action), and "
    "fake invoices (requesting payment redirected to an attacker's account). If a message urges immediate "
    "action, slow down and verify its authenticity before acting.\n\n"
    "Ongoing Training: Awareness training should be continuous, not a one-time event, using engaging "
    "material like visual guides. Employees should have clear steps to follow when a message seems "
    "suspicious.\n\n"
    "Phishing Drills: Regular simulated phishing campaigns (like the ones on this platform) help ensure "
    "training is actually applied. Drills work best when framed positively — as a challenge to spot the "
    "fake, with constructive feedback and encouragement for anyone who doesn't spot it, rather than "
    "punishment. Aim for drills roughly monthly."
)


def backfill_best_practices(apps, schema_editor):
    TrainingModule = apps.get_model('training', 'TrainingModule')
    TrainingModule.objects.filter(best_practices='').update(best_practices=BEST_PRACTICES_TEXT)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0003_trainingmodule_best_practices_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_best_practices, noop_reverse),
    ]
