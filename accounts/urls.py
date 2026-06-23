# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from home.views import default_home
from mpesa.views import token_purchase, stk
#from dataset.views import home

urlpatterns = [
    # Existing URLs
    path('', views.login_signup_page, name='login_signup'),
    path('login/', views.authenticate_login, name='authenticate_login'),
    path('signup/', views.process_signup, name='process_signup'),
    path('home/', views.home, name='home'),
    path('logout/', views.logout_user, name='logout'),
    
    # Email verification URLs
    path('verify-email/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),

    # Password Reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset_form.html', success_url='/accounts/password-reset/done/', email_template_name='accounts/password_reset_email.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html', success_url='/accounts/password-reset-complete/'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),


    #default home
    path('default_home/', default_home, name='default_home'),
    #path('default_home/', views.home, name='default_home'),

    #alias
    path('login_signup/', views.login_signup_page),  # no need for a new name

    # Profile URLs
    path('workspace/', views.workspace_view, name='workspace'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/<int:user_id>/', views.public_profile_view, name='public_profile'),

    # Token and Referral URLs (MISSING)
    path('purchase/', token_purchase, name='token_purchase'),
    path('stk/', stk, name='stk'),
    path('tokens/', views.token_dashboard, name='token_dashboard'),
    path('referrals/', views.referrals_view, name='referrals'),

     # API URLs
    path('api/check-email/', views.check_email_exists, name='check_email_exists'),
    path('api/check-username/', views.check_username_exists, name='check_username_exists'),
    path('api/check-referral/', views.check_referral_code, name='check_referral_code'),  # MISSING

    # Static Pages
    path('settings/', views.settings, name='settings'),
    path('data-standards/', views.data_standards, name='data_standards'),
    path('data-license/', views.data_license, name='data_license'),
    

    #download license PDF
    path('download-license/', views.download_license_pdf, name='download_license_pdf'),
]