from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, BoardMember, Department, Sponsor,
    Event, EventPhoto, Announcement,
    UyeBasvurusu, IletisimMesaji,
)


# =============================================================================
# YARDIMCI SERİALİZER
# User modelinin yalnızca temel alanlarını döndürür.
# İç içe (nested) kullanım için tasarlanmıştır; bağımsız endpoint değildir.
# =============================================================================

class UserMinimalSerializer(serializers.ModelSerializer):
    """
    User modelinin yalnızca temel alanlarını döndüren hafif serializer.
    İç içe (nested) kullanım için tasarlandı; tam User endpoint'i değildir.
    """
    class Meta:
        model  = User
        fields = ("id", "username", "first_name", "last_name")
        read_only_fields = fields  # Bu serializer sadece okuma amaçlıdır


# =============================================================================
# KULLANICI PROFİLİ SERİALİZER
# UserProfile modeline ait tüm alanları serileştirir.
# Kullanıcı bilgileri nested olarak gösterilir.
# =============================================================================

class UserProfileSerializer(serializers.ModelSerializer):
    """
    UserProfile modeli için serializer.
    Kullanıcı bilgileri okunurken UserMinimalSerializer ile gösterilir.
    profile_image alanı isteğe bağlı dosya yüklemesini destekler.
    """
    # Kullanıcı bilgisi nested olarak döner (salt-okunur)
    user = UserMinimalSerializer(read_only=True)

    # Tam adı kolayca almak için salt-okunur hesaplanan alan
    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = UserProfile
        fields = (
            "id", "user", "full_name",
            "student_number", "role",
            "bio", "profile_image",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "user", "created_at", "updated_at")

    def get_full_name(self, obj) -> str:
        """User modelindeki ad-soyad birleşimini döndürür."""
        return obj.user.get_full_name() or obj.user.username


# =============================================================================
# YÖNETİM KURULU ÜYESİ SERİALİZER
# BoardMember modeline ait tüm alanları serileştirir.
# =============================================================================

class BoardMemberSerializer(serializers.ModelSerializer):
    """
    Yönetim kurulu üyelerini serileştiren serializer.
    Tüm alanlar döndürülür; photo alanı dosya yüklemesini destekler.
    """
    class Meta:
        model  = BoardMember
        fields = (
            "id", "full_name", "photo",
            "title", "order",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


# =============================================================================
# KOORDİNATÖRLÜK SERİALİZER
# Department modeline ait tüm alanları serileştirir.
# Koordinatörlük başkanı nested olarak gösterilir.
# =============================================================================

class DepartmentSerializer(serializers.ModelSerializer):
    """
    Koordinatörlük modeli için serializer.
    - head alanı okunurken BoardMemberSerializer ile genişletilmiş gösterilir.
    - Yazma işlemlerinde head_id ile yalnızca ID kabul edilir.
    """
    # Okuma: Koordinatörlük başkanını genişletilmiş göster
    head = BoardMemberSerializer(read_only=True)
    # Yazma: Sadece başkan ID'si kabul et
    head_id = serializers.PrimaryKeyRelatedField(
        queryset=BoardMember.objects.all(),
        source="head",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model  = Department
        fields = (
            "id", "name", "description",
            "logo", "head", "head_id",
            "order",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


# =============================================================================
# SPONSOR SERİALİZER
# Sponsor modeline ait tüm alanları serileştirir.
# =============================================================================

class SponsorSerializer(serializers.ModelSerializer):
    """
    Sponsor modeli için serializer.
    is_active alanı ile aktif/pasif sponsor durumu yönetilir.
    """
    class Meta:
        model  = Sponsor
        fields = (
            "id", "name", "logo",
            "website", "order", "is_active",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


# =============================================================================
# ETKİNLİK FOTOĞRAFI SERİALİZER
# EventPhoto modelini serileştirir.
# EventSerializer içinde nested olarak kullanılır.
# =============================================================================

class EventPhotoSerializer(serializers.ModelSerializer):
    """
    Etkinlik galeri fotoğraflarını serileştiren serializer.
    EventSerializer içinde iç içe (nested) olarak kullanılır.
    """
    class Meta:
        model  = EventPhoto
        fields = ("id", "photo", "created_at")
        read_only_fields = ("id", "created_at")


# =============================================================================
# ETKİNLİK SERİALİZER
# Event modeline ait tüm alanları serileştirir.
# photos alanı ile etkinliğe ait galeri fotoğrafları nested olarak döner.
# =============================================================================

class EventSerializer(serializers.ModelSerializer):
    """
    Event modeli için tam CRUD serializer.
    - organizer alanı okunurken genişletilmiş (nested) kullanıcı bilgisi döner.
    - Yazma işlemlerinde organizer_id ile sadece ID kabul edilir.
    - photos alanı ilgili etkinliğin galeri fotoğraflarını nested olarak listeler.
    """
    # Okuma: organizer nesnesini genişletilmiş göster
    organizer = UserMinimalSerializer(read_only=True)
    # Yazma: sadece organizer ID'si kabul et
    organizer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="organizer",
        write_only=True,
        required=False,
        allow_null=True,
    )
    # Etkinliğe ait galeri fotoğrafları (nested, salt-okunur)
    photos = EventPhotoSerializer(many=True, read_only=True)

    class Meta:
        model  = Event
        fields = (
            "id", "title", "slug", "description",
            "location", "start_date", "end_date",
            "cover_image", "status",
            "organizer", "organizer_id",
            "photos",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")


# =============================================================================
# DUYURU SERİALİZER
# Announcement modeline ait tüm alanları serileştirir.
# =============================================================================

# =============================================================================
# DUYURU SERİALİZER
# Announcement modeline ait tüm alanları serileştirir.
# =============================================================================

class AnnouncementSerializer(serializers.ModelSerializer):
    """
    Announcement modeli için serializer.
    is_active alanı varsayılan olarak True gelir; admin dışında
    değiştirilemez hale getirmek için view katmanında izin kontrolü yapılabilir.
    """
    # Okuma: yazar bilgisini genişletilmiş göster
    author = UserMinimalSerializer(read_only=True)
    # Yazma: sadece yazar ID'si kabul et
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="author",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model  = Announcement
        fields = (
            "id", "title", "slug", "content",
            "location", "event_date",  # <--- YENİ EKLENEN KELİMELER 
            "priority", "is_active",
            "author", "author_id",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")


# =============================================================================
# ÜYELİK BAŞVURUSU SERİALİZER
# UyeBasvurusu modeline ait tüm alanları serileştirir.
# Halka açık form gönderimi için kullanılır.
# =============================================================================

class UyeBasvurusuSerializer(serializers.ModelSerializer):
    """
    Üyelik başvurusu modeli için serializer.
    Başvuru durumu (status) varsayılan olarak 'beklemede' atanır.
    Ziyaretçiler yalnızca başvuru oluşturabilir; durum güncellemesi
    yönetim tarafından yapılır.
    """
    class Meta:
        model  = UyeBasvurusu
        fields = (
            "id", "full_name", "email",
            "phone", "student_number",
            "department", "motivation", "status",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "status", "created_at", "updated_at")


# =============================================================================
# İLETİŞİM MESAJI SERİALİZER
# IletisimMesaji modeline ait tüm alanları serileştirir.
# Halka açık iletişim formu gönderimi için kullanılır.
# =============================================================================

class IletisimMesajiSerializer(serializers.ModelSerializer):
    """
    İletişim mesajı modeli için serializer.
    is_read alanı yalnızca yönetici tarafından güncellenir; API'den
    varsayılan olarak salt-okunur döner.
    """
    class Meta:
        model  = IletisimMesaji
        fields = (
            "id", "full_name", "email",
            "subject", "message", "is_read",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "is_read", "created_at", "updated_at")