import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afridata.settings')
django.setup()

from accounts.models import CustomUser

def verify_users():
    users = CustomUser.objects.filter(is_verified=False)
    count = users.count()
    users.update(is_verified=True)
    print(f"Successfully verified {count} existing users.")

if __name__ == '__main__':
    verify_users()
