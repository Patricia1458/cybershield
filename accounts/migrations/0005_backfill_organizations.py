from django.db import migrations


def backfill_organizations(apps, schema_editor):
    Profile = apps.get_model('accounts', 'Profile')
    Organization = apps.get_model('accounts', 'Organization')

    # Group existing profiles by their company_name so profiles that already
    # shared a company_name (e.g. everyone on the default "TechStart SME")
    # end up in the SAME Organization, rather than one org per user.
    orgs_by_name = {}

    for profile in Profile.objects.filter(organization__isnull=True):
        name = (profile.company_name or '').strip() or 'TechStart SME'
        org = orgs_by_name.get(name)
        if org is None:
            org = Organization.objects.create(name=name)
            orgs_by_name[name] = org
        profile.organization = org
        profile.save(update_fields=['organization'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_organization_profile_organization'),
    ]

    operations = [
        migrations.RunPython(backfill_organizations, noop_reverse),
    ]
