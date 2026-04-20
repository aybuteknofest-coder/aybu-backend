from django.contrib import admin
from .models import Event, Announcement, UserProfile


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Etkinlik yönetim paneli.
    list_display: tabloda gösterilecek sütunlar
    list_filter: sağ kenar çubuğundaki filtreler
    search_fields: arama çubuğunun baktığı alanlar
    prepopulated_fields: slug alanını title'dan otomatik doldurur
    readonly_fields: UUID ve tarih alanlarını düzenlemeye karşı korur
    """
    list_display    = ("title", "status", "organizer", "start_date", "created_at")
    list_filter     = ("status", "start_date")
    search_fields   = ("title", "description", "location", "organizer__username")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("id", "created_at", "updated_at")
    ordering        = ("-start_date",)
    date_hierarchy  = "start_date"  # Tarihe göre hiyerarşik gezinme

    # Detay sayfasında alanları mantıklı gruplara ayırır
    fieldsets = (
        ("Temel Bilgiler", {
            "fields": ("id", "title", "slug", "description", "organizer")
        }),
        ("Tarih & Konum", {
            "fields": ("start_date", "end_date", "location")
        }),
        ("Durum", {
            "fields": ("status",)
        }),
        ("Sistem Bilgileri", {
            "classes": ("collapse",),  # Varsayılan olarak kapalı
            "fields": ("created_at", "updated_at")
        }),
    )


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """
    Duyuru yönetim paneli.
    list_editable: liste görünümünden doğrudan düzenleme sağlar.
    """
    list_display    = ("title", "priority", "is_active", "author", "created_at")
    list_filter     = ("priority", "is_active")
    list_editable   = ("is_active", "priority")  # Listeden hızlı düzenleme
    search_fields   = ("title", "content", "author__username")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("id", "created_at", "updated_at")
    ordering        = ("-priority", "-created_at")

    fieldsets = (
        ("Temel Bilgiler", {
            "fields": ("id", "title", "slug", "content", "author")
        }),
        ("Yayın Ayarları", {
            "fields": ("priority", "is_active")
        }),
        ("Sistem Bilgileri", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )


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