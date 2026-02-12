# Migration to fix django_session.expire_date type (text -> timestamptz)
# Required after SQLite-to-PostgreSQL import - the column may be text/timestamp

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0006_alter_company_email'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE django_session
            ALTER COLUMN expire_date TYPE timestamp with time zone
            USING (expire_date::text)::timestamp AT TIME ZONE 'UTC';
            """,
            reverse_sql=migrations.RunSQL.noop,
            state_operations=[],
        ),
    ]
