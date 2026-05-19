import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


# =============================================================================
# SOYUT TEMEL MODEL
# Tüm modellere otomatik zaman damgası ekler. Doğrudan kullanılmaz.
# =============================================================================

class TimeStampedModel(models.Model):
    """
    Soyut temel model.
    Tüm modellere otomatik created_at / updated_at alanları ekler.
    Doğrudan kullanılmaz; diğer modeller bu sınıftan kalıtım alır.
    """
    # İlk kayıtta bir kez set edilir, sonradan değiştirilemez
    created_at = models.DateTimeField(auto_now_add=True)
    # Her save() çağrısında otomatik olarak güncellenir
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Veritabanında bu model için ayrı tablo oluşturulmaz
        abstract = True


# =============================================================================
# KULLANICI PROFİLİ
# Django'nun yerleşik User modeline ek bilgiler ekler.
# =============================================================================

class UserProfile(TimeStampedModel):
    """
    Django'nun yerleşik User modeline ek bilgiler ekleyen profil modeli.
    OneToOneField ile User ile birebir ilişki kurulur.
    Sinyal (signal) kullanılarak her yeni User için otomatik oluşturulabilir.
    """

    class RoleChoices(models.TextChoices):
        # Kulüp üyesi rolleri: üye, yönetim kurulu, yönetici
        MEMBER = "member", "Üye"
        BOARD  = "board",  "Yönetim Kurulu"
        ADMIN  = "admin",  "Yönetici"

    # Kullanıcı silinince profil de otomatik olarak silinir (CASCADE)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Kullanıcı"
    )
    # Üniversite öğrenci numarası, her öğrenciye özgü olmalı
    student_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Öğrenci Numarası",
        help_text="Üniversite öğrenci numarası."
    )
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.MEMBER,
        verbose_name="Rol"
    )
    bio = models.TextField(blank=True, verbose_name="Hakkında")
    # Profil fotoğrafı; Pillow paketi kurulu olmalı: pip install Pillow
    profile_image = models.ImageField(
        upload_to="profiles/",
        null=True, blank=True,
        verbose_name="Profil Fotoğrafı"
    )

    class Meta:
        verbose_name        = "Kullanıcı Profili"
        verbose_name_plural = "Kullanıcı Profilleri"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.get_role_display()}"


# =============================================================================
# YÖNETİM KURULU
# Kulüp yönetim kurulu üyelerini temsil eder.
# =============================================================================

class BoardMember(TimeStampedModel):
    """
    Kulüp yönetim kurulu üyelerini temsil eden model.
    Sıralama alanı sayesinde başkan en üstte görüntülenebilir.
    """

    full_name = models.CharField(max_length=150, verbose_name="Ad Soyad")
    # Fotoğraf zorunlu değil; boş bırakılabilir
    photo = models.ImageField(
        upload_to="board/",
        blank=True, null=True,
        verbose_name="Fotoğraf"
    )
    # Örn: "Kulüp Başkanı", "Genel Sekreter"
    title = models.CharField(max_length=150, verbose_name="Unvan")
    # Küçük sayı = listenin başına yakın (başkan için 0 verilir)
    order = models.IntegerField(default=0, verbose_name="Sıralama")

    class Meta:
        verbose_name        = "Yönetim Kurulu Üyesi"
        verbose_name_plural = "Yönetim Kurulu Üyeleri"
        ordering            = ["order"]

    def __str__(self):
        return f"{self.full_name} - {self.title}"


# =============================================================================
# KOORDİNATÖRLÜK
# Kulüp bünyesindeki koordinatörlükleri temsil eder.
# =============================================================================

class Department(TimeStampedModel):
    """
    Kulüp bünyesindeki koordinatörlükleri temsil eden model.
    Her koordinatörlüğün bir yönetim kurulu üyesi başkanı olabilir.
    """

    name = models.CharField(max_length=150, verbose_name="Koordinatörlük Adı")
    description = models.CharField(max_length=250, verbose_name="Kısa Açıklama")
    # Logo/ikon zorunlu değil
    logo = models.ImageField(
        upload_to="departments/",
        blank=True, null=True,
        verbose_name="Logo/İkon"
    )
    # Koordinatörlük başkanı silinirse alan NULL kalır, koordinatörlük silinmez
    head = models.ForeignKey(
        BoardMember,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="departments",
        verbose_name="Koordinatörlük Başkanı"
    )
    order = models.IntegerField(default=0, verbose_name="Sıralama")

    class Meta:
        verbose_name        = "Koordinatörlük"
        verbose_name_plural = "Koordinatörlükler"
        ordering            = ["order"]

    def __str__(self):
        return self.name


# =============================================================================
# SPONSOR
# Kulübün sponsorlarını temsil eder.
# =============================================================================

class Sponsor(TimeStampedModel):
    """
    Kulüp sponsorlarını temsil eden model.
    Aktif olmayan sponsorlar API ve sitede gösterilmez.
    """

    name = models.CharField(max_length=150, verbose_name="Firma Adı")
    # Logo için Pillow paketi kurulu olmalı: pip install Pillow
    logo = models.ImageField(upload_to="sponsors/", verbose_name="Firma Logosu")
    # İsteğe bağlı web sitesi bağlantısı
    website = models.URLField(blank=True, null=True, verbose_name="Web Sitesi Linki")
    # Küçük sayı = listede daha önce görünür
    order = models.IntegerField(default=0, verbose_name="Görüntülenme Sırası")
    # False yapılırsa sponsor sitede listelenmez
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")

    class Meta:
        verbose_name        = "Sponsor"
        verbose_name_plural = "Sponsorlar"
        ordering            = ["order"]

    def __str__(self):
        return self.name


# =============================================================================
# ETKİNLİK (eski Event modeli ile birleştirildi)
# Kulüp etkinliklerini ve etkinlik fotoğraflarını temsil eder.
# =============================================================================

class Event(TimeStampedModel):
    """
    Kulüp etkinliklerini temsil eden model.
    Her etkinlik benzersiz bir UUID ve URL-dostu slug ile tanımlanır.
    Kapak fotoğrafı ve birden fazla galeri fotoğrafı desteklenir.
    """

    class StatusChoices(models.TextChoices):
        # Taslak: henüz yayınlanmamış; Yayında: herkese görünür; İptal: etkinlik iptal edildi
        DRAFT     = "draft",     "Taslak"
        PUBLISHED = "published", "Yayında"
        CANCELLED = "cancelled", "İptal Edildi"

    # UUID birincil anahtar; her etkinlik için otomatik ve benzersiz üretilir
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Otomatik oluşturulan evrensel benzersiz tanımlayıcı."
    )
    title = models.CharField(max_length=255, verbose_name="Başlık")
    # Boş bırakılırsa save() metodunda başlıktan otomatik üretilir
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text="URL'de kullanılacak kısa etiket. Boş bırakılırsa başlıktan üretilir."
    )
    description = models.TextField(verbose_name="Açıklama", blank=True)
    location    = models.CharField(max_length=255, verbose_name="Konum", blank=True)
    start_date  = models.DateTimeField(verbose_name="Başlangıç Tarihi")
    # Bitiş tarihi zorunlu değil; tek günlük etkinlikler için boş bırakılabilir
    end_date    = models.DateTimeField(verbose_name="Bitiş Tarihi", null=True, blank=True)
    # Etkinlik listelerinde öne çıkan fotoğraf
    cover_image = models.ImageField(
        upload_to="event_covers/",
        blank=True, null=True,
        verbose_name="Kapak Fotoğrafı"
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
        verbose_name="Durum"
    )
    # Organizatör silinirse etkinlik sahipsiz (NULL) kalır, etkinlik silinmez
    organizer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="organized_events",
        verbose_name="Organizatör"
    )

    class Meta:
        verbose_name        = "Etkinlik"
        verbose_name_plural = "Etkinlikler"
        # En yakın tarihli etkinlik listenin başında yer alır
        ordering            = ["-start_date"]

    def save(self, *args, **kwargs):
        # Slug alanı boşsa başlıktan otomatik olarak üret
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class EventPhoto(TimeStampedModel):
    """
    Bir etkinliğe ait galeri fotoğraflarını temsil eden model.
    related_name='photos' sayesinde etkinlik.photos.all() şeklinde erişilebilir.
    """

    # Etkinlik silinirse bağlı tüm fotoğraflar da silinir (CASCADE)
    event = models.ForeignKey(
        Event,
        related_name="photos",
        on_delete=models.CASCADE,
        verbose_name="Etkinlik"
    )
    photo = models.ImageField(upload_to="event_photos/", verbose_name="Fotoğraf")

    class Meta:
        verbose_name        = "Etkinlik Fotoğrafı"
        verbose_name_plural = "Etkinlik Fotoğrafları"
        # En son yüklenen fotoğraf en üstte görünür
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.event.title} - Fotoğraf {self.id}"


# =============================================================================
# DUYURU
# Kulüp duyurularını öncelik seviyesine göre yönetir.
# =============================================================================

# =============================================================================
# DUYURU
# Kulüp duyurularını öncelik seviyesine göre yönetir.
# =============================================================================

class Announcement(TimeStampedModel):
    """
    Kulüp duyurularını temsil eden model.
    Öncelik seviyesine göre sıralanır; is_active=False olanlar sitede gösterilmez.
    """

    class PriorityChoices(models.IntegerChoices):
        # Yüksek öncelikli duyurular listenin başında yer alır
        LOW    = 1, "Düşük"
        MEDIUM = 2, "Orta"
        HIGH   = 3, "Yüksek"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    title   = models.CharField(max_length=255, verbose_name="Başlık")
    slug    = models.SlugField(max_length=255, unique=True, blank=True)
    content = models.TextField(verbose_name="İçerik")
    
    # --- VİTRİN (FRONTEND) İÇİN EKLENEN YENİ ALANLAR ---
    location = models.CharField(max_length=255, verbose_name="Konum", blank=True, null=True)
    event_date = models.DateTimeField(verbose_name="Etkinlik Tarihi ve Saati", blank=True, null=True)
    # --------------------------------------------------

    priority = models.IntegerField(
        choices=PriorityChoices.choices,
        default=PriorityChoices.MEDIUM,
        verbose_name="Öncelik"
    )
    # False yapılırsa duyuru API ve sitede listelenmez
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif mi?",
        help_text="İşaretsiz duyurular API ve sitede gösterilmez."
    )
    # Duyuruyu yayınlayan kullanıcı silinirse alan NULL kalır
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="announcements",
        verbose_name="Yazar"
    )

    class Meta:
        verbose_name        = "Duyuru"
        verbose_name_plural = "Duyurular"
        # Önce yüksek öncelikli, aynı öncelikliler arasında en yeni önce
        ordering            = ["-priority", "-created_at"]

    def save(self, *args, **kwargs):
        # Slug alanı boşsa başlıktan otomatik olarak üret
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


# =============================================================================
# ÜYELİK BAŞVURUSU
# Web sitesi üzerinden yapılan kulüp üyelik başvurularını saklar.
# =============================================================================

class UyeBasvurusu(TimeStampedModel):
    """
    Kulüp üyelik başvurularını temsil eden model.
    Web sitesi üzerinden yapılan başvurular burada saklanır.
    Yönetim kurulu tarafından onay/red işlemi yapılır.
    """

    class DurumChoices(models.TextChoices):
        BEKLEMEDE  = "beklemede",  "Beklemede"
        ONAYLANDI  = "onaylandi",  "Onaylandı"
        REDDEDILDI = "reddedildi", "Reddedildi"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    full_name = models.CharField(max_length=150, verbose_name="Ad Soyad")
    email = models.EmailField(verbose_name="E-posta Adresi")
    phone = models.CharField(
        max_length=20, blank=True,
        verbose_name="Telefon Numarası"
    )
    student_number = models.CharField(
        max_length=20,
        verbose_name="Öğrenci Numarası"
    )
    department = models.CharField(
        max_length=150,
        verbose_name="Bölüm",
        help_text="Başvuranın üniversitedeki bölümü."
    )
    motivation = models.TextField(
        blank=True,
        verbose_name="Motivasyon Yazısı",
        help_text="Neden bu kulübe katılmak istiyorsunuz?"
    )
    status = models.CharField(
        max_length=20,
        choices=DurumChoices.choices,
        default=DurumChoices.BEKLEMEDE,
        verbose_name="Başvuru Durumu"
    )

    class Meta:
        verbose_name        = "Üyelik Başvurusu"
        verbose_name_plural = "Üyelik Başvuruları"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} — {self.get_status_display()}"


# =============================================================================
# İLETİŞİM MESAJI
# Web sitesindeki iletişim formundan gelen mesajları saklar.
# =============================================================================

class IletisimMesaji(TimeStampedModel):
    """
    İletişim formundan gelen mesajları temsil eden model.
    Ziyaretçiler giriş yapmadan mesaj gönderebilir.
    is_read alanı yönetim panelinde okundu/okunmadı takibi için kullanılır.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    full_name = models.CharField(max_length=150, verbose_name="Ad Soyad")
    email = models.EmailField(verbose_name="E-posta Adresi")
    subject = models.CharField(max_length=255, verbose_name="Konu")
    message = models.TextField(verbose_name="Mesaj İçeriği")
    is_read = models.BooleanField(
        default=False,
        verbose_name="Okundu mu?",
        help_text="Yönetici tarafından okunup okunmadığını gösterir."
    )

    class Meta:
        verbose_name        = "İletişim Mesajı"
        verbose_name_plural = "İletişim Mesajları"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.subject} — {self.full_name}"