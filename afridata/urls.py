from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from schema_graph.views import Schema

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin_dashboard/', include('admin_dashboard.urls')),
    path('', include('home.urls')),
    path('api/', include('api.urls')),
    path('api/metadata/', include('metadata.api.urls')),
    path('api/recommendations/', include('recommendations.api.urls')),
    path('accounts/', include('accounts.urls')),
    path('dataset/', include('dataset.urls')),
    path('community/', include('community.urls')),
    path('mpesa/', include('mpesa.urls')),
    path('standardiser/', include('standardiser.urls', namespace='standardiser')),

    #url to schema diagram
    path("schema/", Schema.as_view()),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)

# Reload trigger comment to refresh runserver URL cache
