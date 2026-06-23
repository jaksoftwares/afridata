import os
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "afridata.settings")
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import UserProfile

User = get_user_model()

admins_data = [
    {
        "email": "info.jhub@jkuat.ac.ke",
        "username": "info.jhub",
        "password": "JHubAdminPassword2026!",
        "full_name": "JHub Admin",
        "bio": "Official JHub Administrator",
        "organization": "JKUAT",
        "job_title": "System Administrator",
    },
    {
        "email": "jaksoftwares05@gmail.com",
        "username": "jaksoftwares05",
        "password": "JakAdminPassword2026!",
        "full_name": "Jak Softwares",
        "bio": "Lead DevOps and System Administrator",
        "organization": "Jak Softwares",
        "job_title": "Lead DevOps",
    }
]

def create_admins():
    for data in admins_data:
        email = data['email']
        if not User.objects.filter(email=email).exists():
            print(f"Creating superuser: {email}...")
            user = User.objects.create_superuser(
                email=email,
                username=data['username'],
                password=data['password'],
                full_name=data['full_name'],
                bio=data['bio'],
                is_verified=True
            )
            
            # Profile is automatically created via the post_save signal in accounts/models.py
            if hasattr(user, 'profile'):
                user.profile.organization = data['organization']
                user.profile.job_title = data['job_title']
                user.profile.is_premium_subscriber = True  # Give admins premium access
                user.profile.save()
                
            print(f"Superuser {email} created successfully. Password: {data['password']}")
        else:
            print(f"Superuser {email} already exists.")

if __name__ == "__main__":
    create_admins()
