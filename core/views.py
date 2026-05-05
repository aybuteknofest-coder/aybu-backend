from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    UserProfile, BoardMember, Department, Sponsor,
    Event, EventPhoto, Announcement,
    UyeBasvurusu, IletisimMesaji,
)
from .serializers import (
    UserProfileSerializer, BoardMemberSerializer,
    DepartmentSerializer, SponsorSerializer,
    EventSerializer, EventPhotoSerializer,
    AnnouncementSerializer,
    UyeBasvurusuSerializer, IletisimMesajiSerializer,
)

# Not: django-filter paketi gereklidir → pip install django-filter
# INSTALLED_APPS'e 'django_filters' eklemeyi unutmayın.


# =============================================================================
# KULLANICI PROFİLİ VIEWSET
# Giriş yapmış kullanıcılar profil bilgilerine erişebilir.
# =============================================================================

class UserProfileViewSet(viewsets.ModelViewSet):
    """
    Kullanıcı profilleri için API.
    Profiller yalnızca giriş yapmış kullanıcılara açıktır.

    Filtreleme: ?role=member
    Arama:      ?search=ali
    """
    queryset           = UserProfile.objects.select_related("user").all()
    serializer_class   = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Arama ve filtreleme backend'leri
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["role"]
    search_fields    = ["user__username", "user__first_name", "student_number"]


# =============================================================================
# YÖNETİM KURULU ÜYESİ VIEWSET
# Yönetim kurulu üyelerini herkese açık olarak listeler.
# Oluşturma/güncelleme/silme yalnızca giriş yapmış kullanıcılar içindir.
# =============================================================================

class BoardMemberViewSet(viewsets.ModelViewSet):
    """
    Yönetim kurulu üyeleri için API.

    GET    /api/board-members/        → liste (herkes)
    POST   /api/board-members/        → oluştur (giriş gerekli)
    GET    /api/board-members/{id}/   → detay (herkes)
    PUT    /api/board-members/{id}/   → güncelle (giriş gerekli)
    DELETE /api/board-members/{id}/   → sil (giriş gerekli)

    Sıralama: ?ordering=order
    """
    queryset           = BoardMember.objects.all()
    serializer_class   = BoardMemberSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["order", "created_at"]
    ordering        = ["order"]  # Varsayılan sıralama


# =============================================================================
# KOORDİNATÖRLÜK VIEWSET
# Koordinatörlükleri herkese açık olarak listeler.
# =============================================================================

class DepartmentViewSet(viewsets.ModelViewSet):
    """
    Koordinatörlükler için API.
    Koordinatörlük başkanı bilgisi nested olarak döner.

    Sıralama: ?ordering=order
    Arama:    ?search=yazılım
    """
    queryset           = Department.objects.select_related("head").all()
    serializer_class   = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ["name", "description"]
    ordering_fields  = ["order", "created_at"]
    ordering         = ["order"]


# =============================================================================
# SPONSOR VIEWSET
# Aktif sponsorları herkese açık olarak listeler.
# =============================================================================

class SponsorViewSet(viewsets.ModelViewSet):
    """
    Sponsorlar için API.
    Anonim kullanıcılar yalnızca aktif sponsorları görebilir.

    Filtreleme: ?is_active=true
    Sıralama:   ?ordering=order
    """
    queryset           = Sponsor.objects.all()
    serializer_class   = SponsorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends  = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["is_active"]
    ordering_fields  = ["order", "created_at"]
    ordering         = ["order"]

    def get_queryset(self):
        """Anonim kullanıcılar yalnızca aktif sponsorları görür."""
        qs = super().get_queryset()
        if not self.request.user.is_authenticated:
            return qs.filter(is_active=True)
        return qs


# =============================================================================
# ETKİNLİK VIEWSET
# Etkinlikler için tam CRUD API.
# Yayınlanmış etkinlikler herkese açık; taslak/iptal yalnızca giriş yapanlara.
# =============================================================================

class EventViewSet(viewsets.ModelViewSet):
    """
    Etkinlikler için tam CRUD API.

    GET    /api/events/          → liste
    POST   /api/events/          → yeni oluştur
    GET    /api/events/{id}/     → detay
    PUT    /api/events/{id}/     → tam güncelle
    PATCH  /api/events/{id}/     → kısmi güncelle
    DELETE /api/events/{id}/     → sil

    Filtreleme: ?status=published
    Arama:      ?search=bahar
    Sıralama:   ?ordering=start_date
    """
    queryset           = Event.objects.select_related("organizer").prefetch_related("photos").all()
    serializer_class   = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # Arama ve filtreleme backend'leri
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status"]                          # ?status=published
    search_fields    = ["title", "description", "location"] # ?search=...
    ordering_fields  = ["start_date", "created_at"]        # ?ordering=start_date
    ordering         = ["-start_date"]                     # Varsayılan sıralama

    def get_queryset(self):
        """
        Yayına alınmış (published) etkinlikler herkese açık.
        Taslak ve iptal edilmişler yalnızca giriş yapmış kullanıcılara görünür.
        """
        qs = super().get_queryset()
        if not self.request.user.is_authenticated:
            return qs.filter(status=Event.StatusChoices.PUBLISHED)
        return qs

    def perform_create(self, serializer):
        """Yeni etkinlik oluşturulurken organizatörü otomatik ata."""
        serializer.save(organizer=self.request.user)


# =============================================================================
# ETKİNLİK FOTOĞRAFI VIEWSET
# Etkinlik galeri fotoğrafları için CRUD API.
# =============================================================================

class EventPhotoViewSet(viewsets.ModelViewSet):
    """
    Etkinlik galeri fotoğrafları için API.
    Fotoğraflar herkese açık olarak görüntülenebilir;
    yükleme/silme işlemleri giriş yapmış kullanıcılar içindir.

    Filtreleme: ?event={uuid}  → belirli bir etkinliğin fotoğrafları
    """
    queryset           = EventPhoto.objects.select_related("event").all()
    serializer_class   = EventPhotoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends  = [DjangoFilterBackend]
    filterset_fields = ["event"]  # ?event=<uuid> ile etkinliğe göre filtrele


# =============================================================================
# DUYURU VIEWSET
# Duyurular için tam CRUD API.
# Anonim kullanıcılar yalnızca aktif duyuruları görür.
# =============================================================================

class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    Duyurular için tam CRUD API.
    Anonim kullanıcılar yalnızca aktif duyuruları görebilir.

    Filtreleme: ?priority=3&is_active=true
    Arama:      ?search=kayıt
    Sıralama:   ?ordering=-created_at
    """
    queryset           = Announcement.objects.select_related("author").all()
    serializer_class   = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["priority", "is_active"]
    search_fields    = ["title", "content"]
    ordering_fields  = ["priority", "created_at"]
    ordering         = ["-priority", "-created_at"]

    def get_queryset(self):
        """Anonim kullanıcılar yalnızca aktif duyuruları görür."""
        qs = super().get_queryset()
        if not self.request.user.is_authenticated:
            return qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        """Yeni duyuru oluşturulurken yazarı otomatik ata."""
        serializer.save(author=self.request.user)


# =============================================================================
# ÜYELİK BAŞVURUSU VIEWSET
# Herkes başvuru oluşturabilir; listeleme/güncelleme giriş gerektirir.
# =============================================================================

class UyeBasvurusuViewSet(viewsets.ModelViewSet):
    """
    Üyelik başvuruları için API.
    Herkes başvuru oluşturabilir (AllowAny POST).
    Listeleme, detay görüntüleme ve durum güncelleme yalnızca
    giriş yapmış kullanıcılara açıktır.

    Filtreleme: ?status=beklemede
    Arama:      ?search=ahmet
    Sıralama:   ?ordering=-created_at
    """
    queryset           = UyeBasvurusu.objects.all()
    serializer_class   = UyeBasvurusuSerializer

    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status"]
    search_fields    = ["full_name", "email", "student_number"]
    ordering_fields  = ["created_at"]
    ordering         = ["-created_at"]

    def get_permissions(self):
        """
        Başvuru oluşturma (POST) herkesin yapabilmesi için AllowAny;
        diğer tüm işlemler giriş gerektirir.
        """
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


# =============================================================================
# İLETİŞİM MESAJI VIEWSET
# Herkes mesaj gönderebilir; listeleme yalnızca giriş yapanlar içindir.
# =============================================================================

class IletisimMesajiViewSet(viewsets.ModelViewSet):
    """
    İletişim mesajları için API.
    Herkes mesaj gönderebilir (AllowAny POST).
    Listeleme, detay ve güncelleme (okundu işaretleme) yalnızca
    giriş yapmış kullanıcılara açıktır.

    Filtreleme: ?is_read=false
    Arama:      ?search=bilgi
    Sıralama:   ?ordering=-created_at
    """
    queryset           = IletisimMesaji.objects.all()
    serializer_class   = IletisimMesajiSerializer

    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_read"]
    search_fields    = ["full_name", "email", "subject", "message"]
    ordering_fields  = ["created_at"]
    ordering         = ["-created_at"]

    def get_permissions(self):
        """
        Mesaj gönderme (POST) herkesin yapabilmesi için AllowAny;
        diğer tüm işlemler giriş gerektirir.
        """
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
