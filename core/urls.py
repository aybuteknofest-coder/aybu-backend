from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

# =============================================================================
# API URL YAPILANDIRMASI
# DefaultRouter otomatik olarak liste, detay ve format-suffix URL'leri oluşturur.
# Örnek: /api/events/, /api/events/{pk}/, /api/events.json
# =============================================================================

router = DefaultRouter()

# Kullanıcı profilleri — /api/user-profiles/
router.register(r"user-profiles",    views.UserProfileViewSet,     basename="userprofile")

# Yönetim kurulu üyeleri — /api/board-members/
router.register(r"board-members",    views.BoardMemberViewSet,     basename="boardmember")

# Koordinatörlükler — /api/departments/
router.register(r"departments",      views.DepartmentViewSet,      basename="department")

# Sponsorlar — /api/sponsors/
router.register(r"sponsors",         views.SponsorViewSet,         basename="sponsor")

# Etkinlikler — /api/events/
router.register(r"events",           views.EventViewSet,           basename="event")

# Etkinlik fotoğrafları — /api/event-photos/
router.register(r"event-photos",     views.EventPhotoViewSet,      basename="eventphoto")

# Duyurular — /api/announcements/
router.register(r"announcements",    views.AnnouncementViewSet,    basename="announcement")

# Üyelik başvuruları — /api/uye-basvurulari/
router.register(r"uye-basvurulari",  views.UyeBasvurusuViewSet,   basename="uyebasvurusu")

# İletişim mesajları — /api/iletisim-mesajlari/
router.register(r"iletisim-mesajlari", views.IletisimMesajiViewSet, basename="iletisimmesaji")

urlpatterns = [
    path("", include(router.urls)),
]