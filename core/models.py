import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    """
    Soyut temel model.
    Tüm modellere otomatik created_at / updated_at alanları ekler.
    Doğrudan kullanılmaz; diğer modeller bu sınıftan kalıtım alır.
    """
    created_at = models.DateTimeField(auto_now_add=True)  # İlk kayıtta bir kez set edilir
    updated_at = models.DateTimeField(auto_now=True)       # Her save() çağrısında güncellenir

    class Meta:
        abstract = True  # Veritabanında bu model için ayrı tablo oluşturulmaz


class Event(TimeStampedModel):
    """
    Kulüp etkinliklerini temsil eden model.
    Her etkinlik benzersiz bir UUID ve URL-dostu slug ile tanımlanır.
    """

    class StatusChoices(models.TextChoices):
        DRAFT     = "draft",     "Taslak"
        PUBLISHED = "published", "Yayında"
        CANCELLED = "cancelled", "İptal Edildi"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Otomatik oluşturulan evrensel benzersiz tanımlayıcı."
    )
    title = models.CharField(max_length=255, verbose_name="Başlık")
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,  # save() metodunda otomatik doldurulacak
        help_text="URL'de kullanılacak kısa etiket. Boş bırakılırsa başlıktan üretilir."
    )
    description = models.TextField(verbose_name="Açıklama", blank=True)
    location    = models.CharField(max_length=255, verbose_name="Konum", blank=True)
    start_date  = models.DateTimeField(verbose_name="Başlangıç Tarihi")
    end_date    = models.DateTimeField(verbose_name="Bitiş Tarihi", null=True, blank=True)
    status      = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
        verbose_name="Durum"
    )
    # Etkinliği oluşturan kulüp üyesi; silinirse etkinlik sahipsiz (NULL) kalır
    organizer   = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="organized_events",
        verbose_name="Organizatör"
    )

    class Meta:
        verbose_name        = "Etkinlik"
        verbose_name_plural = "Etkinlikler"
        ordering            = ["-start_date"]  # En yakın tarihli önce

    def save(self, *args, **kwargs):
        # Slug yoksa başlıktan otomatik üret
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Announcement(TimeStampedModel):
    """
    Kulüp duyurularını temsil eden model.
    Duyurular öncelik seviyesine göre sıralanabilir.
    """

    class PriorityChoices(models.IntegerChoices):
        LOW    = 1, "Düşük"
        MEDIUM = 2, "Orta"
        HIGH   = 3, "Yüksek"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    title    = models.CharField(max_length=255, verbose_name="Başlık")
    slug     = models.SlugField(max_length=255, unique=True, blank=True)
    content  = models.TextField(verbose_name="İçerik")
    priority = models.IntegerField(
        choices=PriorityChoices.choices,
        default=PriorityChoices.MEDIUM,
        verbose_name="Öncelik"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif mi?",
        help_text="İşaretsiz duyurular API ve sitede gösterilmez."
    )
    # Duyuruyu yayınlayan kullanıcı
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
        ordering            = ["-priority", "-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class UserProfile(TimeStampedModel):
    """
    Django'nun yerleşik User modeline ek bilgiler ekleyen profil modeli.
    OneToOneField ile User ile birebir ilişki kurulur.
    Sinyal (signal) kullanılarak her yeni User için otomatik oluşturulabilir.
    """

    class RoleChoices(models.TextChoices):
        MEMBER  = "member",  "Üye"
        BOARD   = "board",   "Yönetim Kurulu"
        ADMIN   = "admin",   "Yönetici"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,  # Kullanıcı silinince profil de silinir
        related_name="profile",
        verbose_name="Kullanıcı"
    )
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
    bio           = models.TextField(blank=True, verbose_name="Hakkında")
    profile_image = models.ImageField(
        upload_to="profiles/",
        null=True, blank=True,
        verbose_name="Profil Fotoğrafı"
    )
    # ImageField için Pillow paketi gerekir: pip install Pillow

    class Meta:
        verbose_name        = "Kullanıcı Profili"
        verbose_name_plural = "Kullanıcı Profilleri"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.get_role_display()}"


