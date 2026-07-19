from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("projects/", include("projects.urls")),
    path("stories/", include("stories.urls")),
    path("comments/", include("comments.urls")),
    path("summarizer/", include("summarizer.urls")),
    path("", RedirectView.as_view(pattern_name="projects:project_manager", permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
