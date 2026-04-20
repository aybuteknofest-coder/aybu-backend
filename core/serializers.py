from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Event, Announcement, UserProfile


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    User modelinin yalnızca temel alanlarını döndüren hafif serializer.
    İç içe (nested) kullanım için tasarlandı; tam User endpoint'i değildir.
    """
    class Meta:
        model  = User
        fields = ("id", "username", "first_name", "last_name")
        read_only_fields = fields  # Bu serializer sadece okuma amaçlıdır


class EventSerializer(serializers.ModelSerializer):
    """
    Event modeli için tam CRUD serializer.
    - organizer alanı okunurken genişletilmiş (nested) kullanıcı bilgisi döner.
    - Yazma işlemlerinde organizer_id ile sadece ID kabul edilir.
    """
    # Okuma: organizer nesnesini genişletilmiş göster
    organizer = UserMinimalSerializer(read_only=True)
    # Yazma: sadece organizer ID'si kabul et
    organizer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="organizer",
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model  = Event
        fields = (
            "id", "title", "slug", "description",
            "location", "start_date", "end_date",
            "status", "organizer", "organizer_id",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")


class AnnouncementSerializer(serializers.ModelSerializer):
    """
    Announcement modeli için serializer.
    is_active alanı varsayılan olarak True gelir; admin dışında
    değiştirilemez hale getirmek için view katmanında izin kontrolü yapılabilir.
    """
    author = UserMinimalSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="author",
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model  = Announcement
        fields = (
            "id", "title", "slug", "content",
            "priority", "is_active",
            "author", "author_id",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")


class UserProfileSerializer(serializers.ModelSerializer):
    """
    UserProfile modeli için serializer.
    Kullanıcı bilgileri okunurken UserMinimalSerializer ile gösterilir.
    profile_image alanı isteğe bağlı dosya yüklemesini destekler.
    """
    user = UserMinimalSerializer(read_only=True)

    # Tam adı kolayca almak için salt-okunur alan
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