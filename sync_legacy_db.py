import os
import sys
import django
from django.db import connection
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afridata.settings')
django.setup()

def is_legacy_db():
    try:
        with connection.cursor() as cursor:
            # Check if one of the historical tables exists
            cursor.execute("SHOW TABLES LIKE 'accounts_emailverificationtoken';")
            return cursor.fetchone() is not None
    except Exception as e:
        print(f"Error checking legacy db: {e}")
        return False

def has_applied_migration(app_name, migration_name):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM django_migrations WHERE app=%s AND name=%s;", [app_name, migration_name])
            return cursor.fetchone() is not None
    except Exception:
        return False

if __name__ == '__main__':
    # If the table exists but Django hasn't recorded the migration, it's a legacy out-of-sync database
    if is_legacy_db() and not has_applied_migration('accounts', '0002_emailverificationtoken'):
        print("Legacy database detected! Safely faking historical migrations before running normal migrations...")
        
        # Fake everything up to the point before our recent 'file_hash' addition
        call_command('migrate', 'accounts', fake=True)
        call_command('migrate', 'admin_dashboard', fake=True)
        call_command('migrate', 'api', fake=True)
        call_command('migrate', 'community', fake=True)
        
        # For dataset, we MUST stop faking at 0008, because 0009_dataset_file_hash must run for real
        call_command('migrate', 'dataset', '0008_alter_dataset_dataset_type', fake=True)
        
        call_command('migrate', 'home', fake=True)
        call_command('migrate', 'metadata', fake=True)
        call_command('migrate', 'recommendations', fake=True)
        call_command('migrate', 'standardiser', fake=True)
        
        print("Historical migrations safely faked.")
    else:
        print("Database is clean or already synced. Proceeding normally.")
