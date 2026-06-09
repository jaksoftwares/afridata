"""
Django AppConfig for the metadata app.

The metadata app provides an automatic metadata extraction pipeline
that ingests data from multiple sources (CSV, Excel, SQL), profiles
columns, classifies semantic types, and produces enriched JSON Schema
output via a REST API.

The ready() method ensures that the app is properly initialized.
"""
from django.apps import AppConfig


class MetadataConfig(AppConfig):
    name = 'metadata'
    verbose_name = 'Metadata Extraction Pipeline'
    default_auto_field = 'django.db.models.BigAutoField'
