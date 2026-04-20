from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event, Announcement, UserProfile
from .serializers import EventSerializer, AnnouncementSerializer, UserProfileSerializer

# Not: django-filter paketi gereklidir → pip install django-filter
# INSTALLED_APPS'e 'django_filters' eklemeyi unutmayın.


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
    queryset           = Event.objects.select_related("organizer").all()
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


class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    Duyurular için tam CRUD API.
    Anonim kullanıcılar yalnızca aktif duyuruları görebilir.
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
        qs = super().get_queryset()
        if not self.request.user.is_authenticated:
            return qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    Kullanıcı profilleri için API.
    Profiller yalnızca giriş yapmış kullanıcılara açıktır.
    """
    queryset           = UserProfile.objects.select_related("user").all()
    serializer_class   = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends  = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["role"]
    search_fields    = ["user__username", "user__first_name", "student_number"]
