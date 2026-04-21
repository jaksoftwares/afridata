"""
App configuration for standardiser.
"""

from django.apps import AppConfig


class StandardiserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'standardiser'
    verbose_name = 'Data Standardiser'
