from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

# DefaultRouter otomatik olarak liste, detay ve format-suffix URL'leri oluşturur.
# Örnek: /api/events/, /api/events/{pk}/, /api/events.json
router = DefaultRouter()
router.register(r"events",        views.EventViewSet,       basename="event")
router.register(r"announcements", views.AnnouncementViewSet, basename="announcement")
router.register(r"user-profiles", views.UserProfileViewSet,  basename="userprofile")

urlpatterns = [
    path("", include(router.urls)),
]