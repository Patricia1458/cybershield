from django.db import migrations


def backfill_encrypted_email(apps, schema_editor):
    Profile = apps.get_model('accounts', 'Profile')
    # Save each profile through the real model (not the historical one) so the
    # EncryptedCharField descriptor actually encrypts the value on write.
    from accounts.models import Profile as RealProfile
    for profile_id, user_id in Profile.objects.values_list('id', 'user_id'):
        real_profile = RealProfile.objects.get(pk=profile_id)
        real_profile.save()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_profile_encrypted_email'),
    ]

    operations = [
        migrations.RunPython(backfill_encrypted_email, noop_reverse),
    ]
