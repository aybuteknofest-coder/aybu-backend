from django.contrib import admin
from .models import (
    UserProfile,
    BoardMember,
    Department,
    Sponsor,
    Event,
    EventPhoto,
    Announcement,
    UyeBasvurusu,
    IletisimMesaji,
)


# =============================================================================
# KULLANICI PROFİLİ
# =============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Kullanıcı profili yönetim paneli.
    raw_id_fields: çok sayıda kullanıcı varsa User seçimini
                   açılır liste yerine ID arama kutusuna çevirir.
    """
    list_display    = ("user", "student_number", "role", "created_at")
    list_filter     = ("role",)
    search_fields   = ("user__username", "user__email", "student_number")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields   = ("user",)  # Büyük kullanıcı tabanlarında performans için

    fieldsets = (
        ("Kullanıcı", {
            "fields": ("user", "student_number", "role")
        }),
        ("Ek Bilgiler", {
            "fields": ("bio", "profile_image")
        }),
        ("Sistem Bilgileri", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )


# =============================================================================
# YÖNETİM KURULU
# =============================================================================

@admin.register(BoardMember)
class BoardMemberAdmin(admin.ModelAdmin):
    """
    Yönetim kurulu üyeleri yönetim paneli.
    list_editable ile sıralama doğrudan listeden değiştirilebilir.
    """
    list_display    = ("full_name", "title", "order", "created_at")
    list_editable   = ("order",)  # Listeden hızlı sıralama düzenleme
    list_filter     = ("title",)
    search_fields   = ("full_name", "title")
    readonly_fields = ("created_at", "updated_at")
    ordering        = ("order",)

    fieldsets = (
        ("Temel Bilgiler", {
            "fields": ("full_name", "title", "photo")
        }),
        ("Sıralama", {
            "fields": ("order",),
            "description": "Küçük sayı = listenin başına yakın. Başkan için 0 kullanın."
        }),
        ("Sistem Bilgileri", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )


# =============================================================================
# KOORDİNATÖRLÜK
# =============================================================================

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """
    Koordinatörlük yönetim paneli.
    Koordinatörlük başkanı seçimi için raw_id_fields kullanılır.
    """
    list_display    = ("name", "head", "order", "created_at")
    list_editable   = ("order",)
    list_filter     = ("head",)
    search_fields   = ("name", "description", "head__full_name")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields   = ("head",)
    ordering        = ("order",)

    fieldsets = (
        ("Temel Bilgiler", {
            "fields": ("name", "description", "logo")
        }),
        ("Yönetim", {
            "fields": ("head", "order")
        }),
        ("Sistem Bilgileri", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )


# =============================================================================
# SPONSOR
# =============================================================================

@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    """
    Sponsor yönetim paneli.
    list_editable ile aktiflik durumu ve sıralama listeden düzenlenebilir.
    """
    list_display    = ("name", "website", "order", "is_active", "created_at")
    list_editable   = ("order", "is_active")
    list_filter     = ("is_active",)
    search_fields   = ("name", "website")
    readonly_fields = ("created_at", "updated_at")
    ordering        = ("order",)

    fieldsets = (
        ("Temel Bilgiler", {
            "fields": ("name", "logo", "website")
        }),
        ("Görüntülenme Ayarları", {
            "fields": ("order", "is_active")
        }),
        ("Sistem Bilgileri", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )


# =============================================================================
# ETKİNLİK & ETKİNLİK FOTOĞRAFI
# =============================================================================

class EventPhotoInline(admin.TabularInline):
    """
    Etkinlik detay sayfasında galeri fotoğraflarını satır içi düzenleme.
    extra=1: varsayılan olarak 1 boş yükleme alanı gösterir.
    """
    model  = EventPhoto
    extra  = 1
    readonly_fields = ("created_at",)
    fields = ("photo", "created_at")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Etkinlik yönetim paneli.
    list_display: tabloda gösterilecek sütunlar
    list_filter: sağ kenar çubuğundaki filtreler
    search_fields: arama çubuğunun baktığı alanlar
    prepopulated_fields: slug alanını title'dan otomatik doldurur
    readonly_fields: UUID ve tarih alanlarını düzenlemeye karşı korur
    inlines: etkinlik fotoğrafları satır içi düzenlenir
    """
    list_display    = ("title", "status", "organizer", "start_date", "created_at")
    list_filter     = ("status", "start_date")
    search_fields   = ("title", "description", "location", "organizer__username")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("id", "created_at", "updated_at")
    ordering        = ("-start_date",)
    date_hierarchy  = "start_date"  # Tarihe göre hiyerarşik gezinme
    inlines         = [EventPhotoInline]

    # Detay sayfasında alanları mantıklı gruplara ayırır
    fieldsets = (
        ("Temel Bilgiler", {
            "fields": ("id", "title", "slug", "description", "organizer")
        }),
        ("Tarih & Konum", {
            "fields": ("start_date", "end_date", "location")
        }),
        ("Görsel", {
            "fields": ("cover_image",),
            "description": "Etkinlik listelerinde gösterilecek kapak fotoğrafı."
        }),
        ("Durum", {
            "fields": ("status",)
        }),
        ("Sistem Bilgileri", {
            "classes": ("collapse",),  # Varsayılan olarak kapalı
            "fields": ("created_at", "updated_at")
        }),
    )


@admin.register(EventPhoto)
class EventPhotoAdmin(admin.ModelAdmin):
    """
    Etkinlik fotoğrafları yönetim paneli.
    Tek tek fotoğraf yönetimi için kullanılır.
    (Toplu ekleme için EventAdmin içindeki inline tercih edilir.)
    """
    list_display    = ("__str__", "event", "created_at")
    list_filter     = ("event",)
    search_fields   = ("event__title",)
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields   = ("event",)

    fieldsets = (
        ("Fotoğraf Bilgileri", {
            "fields": ("event", "photo")
        }),
        ("Sistem Bilgileri", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )


# =============================================================================
# DUYURU
# =============================================================================

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """
    Duyuru yönetim paneli.
    list_editable: liste görünümünden doğrudan düzenleme sağlar.
    """
    # Vitrin listesine 'event_date' de ekledik ki dışarıdan bakınca tarihi görebilesin
    list_display    = ("title", "priority", "is_active", "event_date", "author", "created_at")
    list_filter     = ("priority", "is_active")
    list_editable   = ("is_active", "priority")  # Listeden hızlı düzenleme
    search_fields   = ("title", "content", "author__username")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("id", "created_at", "updated_at")
    ordering        = ("-priority", "-created_at")

    fieldsets = (
        ("Temel Bilgiler", {
            # YENİ ALANLAR BURAYA GELDİ: "location" ve "event_date"
            "fields": ("id", "title", "slug", "content", "location", "event_date", "author")
        }),
        ("Yayın Ayarları", {
            "fields": ("priority", "is_active")
        }),
        ("Sistem Bilgileri", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )
    # =============================================================================
# ÜYELİK BAŞVURUSU
# =============================================================================

@admin.register(UyeBasvurusu)
class UyeBasvurusuAdmin(admin.ModelAdmin):
    """
    Üyelik başvuruları yönetim paneli.
    Yönetim kurulu başvuruları inceleyip durumlarını günceller.
    """
    list_display    = ("full_name", "email", "status", "created_at")
    list_filter     = ("status",)
    search_fields   = ("full_name", "email", "student_number")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering        = ("-created_at",)

    fieldsets = (
        ("Başvuran Bilgileri", {
            "fields": ("id", "full_name", "email", "phone",
                       "student_number", "department")
        }),
        ("Motivasyon", {
            "fields": ("motivation",)
        }),
        ("Durum", {
            "fields": ("status",)
        }),
        ("Sistem Bilgileri", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )


# =============================================================================
# İLETİŞİM MESAJI
# =============================================================================

@admin.register(IletisimMesaji)
class IletisimMesajiAdmin(admin.ModelAdmin):
    """
    İletişim mesajları yönetim paneli.
    Yönetici mesajları okuyup is_read alanını güncelleyebilir.
    """
    list_display    = ("full_name", "email", "subject", "is_read", "created_at")
    list_filter     = ("is_read",)
    list_editable   = ("is_read",)
    search_fields   = ("full_name", "email", "subject")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering        = ("-created_at",)

    fieldsets = (
        ("Gönderen Bilgileri", {
            "fields": ("id", "full_name", "email")
        }),
        ("Mesaj İçeriği", {
            "fields": ("subject", "message")
        }),
        ("Durum", {
            "fields": ("is_read",)
        }),
        ("Sistem Bilgileri", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),)