from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin paneli
    path("admin/", admin.site.urls),

    # DRF tarama arayüzü (browsable API) için oturum açma/kapama URL'leri
    # Yalnızca geliştirme ortamında aktif edilmesi önerilir
    path("api-auth/", include("rest_framework.urls")),

    # Tüm core API uç noktaları /api/ önekiyle gruplandırıldı
    path("api/", include("core.urls")),
]

# Geliştirme ortamında yüklenen medya dosyalarını (profil fotoğrafları vb.) sun
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
