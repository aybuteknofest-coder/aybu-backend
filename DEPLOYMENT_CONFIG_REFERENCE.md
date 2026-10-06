# Deployment Configuration Reference

> Kaynak: `config/settings.py` (2026-10-06 itibarıyla, Render hazırlık değişiklikleri dahil — henüz push edilmedi).
> Satır numaraları bu sürüme göredir. Bu belge değişkenlerin **adını, türünü ve formatını** tanımlar; gerçek değerler içermez.
> Deploy adımları için bkz. [RENDER_DEPLOYMENT_CHECKLIST.md](RENDER_DEPLOYMENT_CHECKLIST.md).

`.env` dosyası `config/settings.py:24` içinde `load_dotenv(BASE_DIR / '.env')` ile yüklenir (yalnızca yerelde; Render değişkenleri doğrudan ortamdan verir). Gerçek ortam değişkenleri `.env`'deki değerlerden önceliklidir.

---

## Environment Variables Needed

### 1. Tüm ortam değişkenleri

| Değişken Adı | Varsayılan Değer | Türü | Kullanım Yeri | Tanımsızsa ne olur? |
|---|---|---|---|---|
| `SECRET_KEY` | — (yalnızca `DEBUG=True` iken rastgele üretilir) | **Critical** · string | `settings.py:38` | `DEBUG=False` → uygulama açılışta `ImproperlyConfigured` ile durur |
| `DEBUG` | `False` | Boolean (yalnızca tam olarak `True` → açık) | `settings.py:32` | `False` — production modu |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Liste (virgülle ayrılmış host) | `settings.py:45` | Yalnızca localhost kabul edilir; Render'da `RENDER_EXTERNAL_HOSTNAME` yine eklenir |
| `RENDER_EXTERNAL_HOSTNAME` | — | string (host) — **Render otomatik verir** | `settings.py:48-50` | Eklenmez |
| `CSRF_TRUSTED_ORIGINS` | `""` (boş liste) | Liste (virgülle ayrılmış, **şemalı** origin) | `settings.py:60` | HTTPS'te admin/oturum POST'ları farklı origin'den gelirse 403 |
| `CORS_ALLOWED_ORIGINS` | `""` (boş liste) | Liste (virgülle ayrılmış, **şemalı** origin) | `settings.py:172` | Hiçbir frontend origin'ine izin verilmez → tarayıcıda CORS hatası |
| `DATABASE_URL` | — | **Critical** · URL | `settings.py:123` | Açılış başarılı ama ilk DB işleminde `ImproperlyConfigured: ... supply the ENGINE value` |
| `R2_ACCOUNT_ID` | — | **Critical** · string | `settings.py:229` | Endpoint `https://None.eu.r2.cloudflarestorage.com` olur → yükleme hatası |
| `R2_ACCESS_KEY_ID` | — | **Critical** · secret | `settings.py:226` | Yükleme hatası |
| `R2_SECRET_ACCESS_KEY` | — | **Critical** · secret | `settings.py:227` | Yükleme hatası |
| `R2_BUCKET_NAME` | — | **Critical** · string | `settings.py:228` | Yükleme hatası |
| `R2_CUSTOM_DOMAIN` | `None` | string (host, **şemasız**) | `settings.py:236` | Görsel URL'leri public olmayan S3 endpoint'ine gider → frontend'de görseller açılmaz |

**Liste türü kuralları** (`ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`): virgülle ayrılır, baştaki/sondaki boşluklar kırpılır, boş öğeler atlanır.

| Değişken | Doğru | Yanlış |
|---|---|---|
| `ALLOWED_HOSTS` | `api.ornek.com,aybu.onrender.com` | `https://aybu.onrender.com` (şema olmamalı) |
| `CORS_ALLOWED_ORIGINS` | `https://ornek.com,http://localhost:5173` | `ornek.com` (şema zorunlu), `https://ornek.com/` (sonda `/` olmamalı) |
| `CSRF_TRUSTED_ORIGINS` | `https://aybu.onrender.com` | `aybu.onrender.com` (şema zorunlu) |
| `R2_CUSTOM_DOMAIN` | `pub-abc123.r2.dev` | `https://pub-abc123.r2.dev` (şema eklenirse URL `https://https://...` olur) |
| `DEBUG` | `True` / `False` | `true`, `1`, `yes` (hepsi **False** sayılır) |

### 2. Ortam değişkeni olmayan, sabit yapılandırma

| Ayar | Değer | Satır | Not |
|---|---|---|---|
| `SECURE_PROXY_SSL_HEADER` | `('HTTP_X_FORWARDED_PROTO', 'https')` | 53 | Bkz. §4 |
| `SESSION_COOKIE_SECURE` | `not DEBUG` | 56 | Production'da çerez yalnızca HTTPS ile gider |
| `CSRF_COOKIE_SECURE` | `not DEBUG` | 57 | Aynı |
| `CORS_ALLOW_CREDENTIALS` | `True` | 175 | Frontend `credentials: 'include'` kullanabilir |
| `STATIC_URL` / `STATIC_ROOT` | `/static/` / `BASE_DIR/staticfiles` | 164-165 | WhiteNoise (`settings.py:88`) sunar |
| `STORAGES["staticfiles"]` | `whitenoise.storage.CompressedManifestStaticFilesStorage` | 245 | Build'de `collectstatic` zorunlu |
| `STORAGES["default"]` | `storages.backends.s3boto3.S3Boto3Storage` | 241 | Tüm `ImageField` yüklemeleri R2'ye gider |
| `AWS_S3_REGION_NAME` | `'auto'` | 230 | R2 için doğru |
| `AWS_S3_SIGNATURE_VERSION` | `'s3v4'` | 231 | R2 için gerekli |
| `AWS_QUERYSTRING_AUTH` | `False` | 232 | İmzasız URL → bucket public olmalı |
| `TIME_ZONE` | `'UTC'` | 154 | |

---

## Database Connection Details

- **Type:** PostgreSQL (`django.db.backends.postgresql`, sürücü `psycopg2-binary==2.9.9`)
- **Format:** `postgresql://user:password@host:port/dbname` (`postgres://` öneki de kabul edilir)
- **Current settings** (`config/settings.py:121-127`):

```python
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}
```

### `DATABASE_URL` nasıl parse ediliyor?

`dj_database_url.config()` URL'yi Django'nun `DATABASES['default']` sözlüğüne çevirir. Kodda host, port, kullanıcı vb. için **ayrı bir değer yok**; hepsi bu tek URL'den gelir.

| URL parçası | Django anahtarı | Ayrıştırılabilir mi? | Not |
|---|---|---|---|
| Şema (`postgresql://`) | `ENGINE` | ✅ | `django.db.backends.postgresql` olur |
| Kullanıcı adı | `USER` | ✅ | |
| Parola | `PASSWORD` | ✅ | Özel karakterler **percent-encode** edilmeli (`@` → `%40`, `:` → `%3A`, `/` → `%2F`) |
| Host | `HOST` | ✅ | Kodda sabit değer yok |
| Port | `PORT` | ✅ | URL'de yoksa boş kalır → PostgreSQL varsayılanı **5432** kullanılır |
| `/dbname` | `NAME` | ✅ | |
| `?sslmode=require` | `OPTIONS['sslmode']` | ✅ | Query parametreleri `OPTIONS`'a aktarılır |
| — | `CONN_MAX_AGE` | Koddan | `600` sn — bağlantı 10 dk yeniden kullanılır |
| — | `CONN_HEALTH_CHECKS` | Koddan | `True` — yeniden kullanmadan önce bağlantı test edilir |

**SSL/TLS:** Kodda zorlanmıyor (`ssl_require` yok). Render **Internal** URL'si için gerekmez; **External** URL veya harici sağlayıcıda URL sonuna `?sslmode=require` ekleyin.

**Pool:** Ayrı bir bağlantı havuzu yok. Toplam bağlantı ≈ Gunicorn worker sayısı × instance sayısı.

## How to Extract DATABASE_URL

If `DATABASE_URL` is set, parse it:

```
postgres://user:pass@db.onrender.com:5432/dbname
```

Extract (doğrulandı — `dj_database_url.parse` çıktısı):

- **Host:** `db.onrender.com`
- **Port:** `5432`
- **Database:** `dbname`
- **User:** `user`
- **Password:** `pass`

Render URL örnekleri:

| Tür | Örnek | Parse sonucu |
|---|---|---|
| Internal (önerilen) | `postgresql://aybu:****@dpg-xxxxx-a/aybu_db` | Host `dpg-xxxxx-a`, Port boş (→ 5432), DB `aybu_db`, User `aybu` |
| External | `postgresql://aybu:****@dpg-xxxxx-a.frankfurt-postgres.render.com/aybu_db?sslmode=require` | Yukarıdakine ek olarak `OPTIONS = {'sslmode': 'require'}` |

Elle parse etmek için:

```bash
python -c "import dj_database_url, os; print(dj_database_url.parse(os.environ['DATABASE_URL']))"
```

> ⚠️ Bu komut parolayı ekrana yazar; çıktıyı paylaşmayın.

---

## Cloudflare R2

| Değişken | Kullanım | Ayarlandığı Django ayarı | Required |
|---|---|---|---|
| `R2_ACCOUNT_ID` | Yükleme endpoint'ini oluşturur: `https://<R2_ACCOUNT_ID>.eu.r2.cloudflarestorage.com` | `AWS_S3_ENDPOINT_URL` (`:229`) | Yes |
| `R2_ACCESS_KEY_ID` | R2 API token'ının Access Key ID'si | `AWS_ACCESS_KEY_ID` (`:226`) | Yes |
| `R2_SECRET_ACCESS_KEY` | R2 API token'ının Secret Access Key'i | `AWS_SECRET_ACCESS_KEY` (`:227`) | Yes |
| `R2_BUCKET_NAME` | Medya dosyalarının (`profiles/`, `board/`, `departments/`, `sponsors/`, `event_covers/`, `event_photos/`) yazıldığı bucket | `AWS_STORAGE_BUCKET_NAME` (`:228`) | Yes |
| `R2_CUSTOM_DOMAIN` | Görseller için public URL: `https://<R2_CUSTOM_DOMAIN>/<dosya-yolu>` | `AWS_S3_CUSTOM_DOMAIN` (`:236`) | Yes* |

\* Teknik olarak tanımsız da çalışır (yükleme başarılı olur), ancak dönen görsel URL'leri public olmayan S3 endpoint'ini gösterir ve tarayıcıda açılmaz. Pratikte zorunludur.

**Not:** Endpoint'teki `.eu.` kodda sabittir — bucket EU jurisdiction'da oluşturulmuş olmalıdır. Yükleme `AWS_S3_ENDPOINT_URL` üzerinden, okuma `R2_CUSTOM_DOMAIN` üzerinden yapılır.

---

## CORS ve Security

| Soru | Cevap |
|---|---|
| **`ALLOWED_HOSTS` nasıl set ediliyor?** | `settings.py:45`: `ALLOWED_HOSTS` env değişkeni virgülle bölünür (varsayılan `localhost,127.0.0.1`). `settings.py:48-50`: Render'ın otomatik verdiği `RENDER_EXTERNAL_HOSTNAME` varsa listeye eklenir. Listede olmayan `Host` başlığıyla gelen istek **400 Bad Request** alır. |
| **`CORS_ALLOWED_ORIGINS` nereye yazılıyor?** | `settings.py:172`, `django-cors-headers` (`corsheaders` app + `CorsMiddleware`, `settings.py:89`) tarafından okunur. Eskiden `DEBUG=True` iken tüm origin'ler açıktı; artık **yalnızca bu listedeki** origin'ler `Access-Control-Allow-Origin` alır — yerelde de `.env`'e yazılmalı. |
| **`CSRF_TRUSTED_ORIGINS`?** | `settings.py:60`. Django'nun CSRF kontrolü, HTTPS'te gelen POST'un `Origin` başlığını bu listeyle (veya isteğin kendi host'uyla) karşılaştırır. Admin paneli aynı domainden kullanılıyorsa çoğunlukla gerekmez; frontend farklı domainden **session-auth ile** POST/PUT/DELETE yapıyorsa frontend origin'i eklenmelidir. |
| **`SECURE_PROXY_SSL_HEADER` nedir?** | `settings.py:53`. Render HTTPS'i kendi proxy'sinde sonlandırır ve Django'ya isteği **HTTP** olarak iletir; gerçek protokolü `X-Forwarded-Proto: https` başlığında gönderir. Bu ayar Django'ya o başlığa güvenmesini söyler, böylece `request.is_secure()` doğru (`True`) döner. Olmasaydı admin girişi CSRF origin uyuşmazlığı nedeniyle **403** verirdi ve secure çerezler/yönlendirmeler yanlış çalışırdı. ⚠️ Yalnızca bu başlığı her zaman kendisi ayarlayan bir proxy arkasında (Render gibi) güvenlidir. |

---

## Example .env File

### Yerel geliştirme (`aybu-backend/.env` — git'e eklenmez)

```env
# --- Django ---
DEBUG=True
# SECRET_KEY=          # DEBUG=True iken opsiyonel (her açılışta rastgele üretilir)
ALLOWED_HOSTS=localhost,127.0.0.1

# --- CORS / CSRF ---
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
CSRF_TRUSTED_ORIGINS=

# --- Veritabanı ---
DATABASE_URL=sqlite:///db.sqlite3
# veya: DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aybu

# --- Cloudflare R2 ---
R2_ACCOUNT_ID=<cloudflare-account-id>
R2_ACCESS_KEY_ID=<r2-access-key-id>
R2_SECRET_ACCESS_KEY=<r2-secret-access-key>
R2_BUCKET_NAME=<bucket-adi>
R2_CUSTOM_DOMAIN=pub-xxxxxxxx.r2.dev
```

### Production (Render → Environment → "Add from .env")

```env
PYTHON_VERSION=3.12.5

# --- Django ---
SECRET_KEY=<50+ karakter, rastgele — get_random_secret_key() ile üretin>
DEBUG=False
ALLOWED_HOSTS=<servis-adi>.onrender.com

# --- CORS / CSRF ---
CORS_ALLOWED_ORIGINS=https://<frontend-domain>
CSRF_TRUSTED_ORIGINS=https://<servis-adi>.onrender.com,https://<frontend-domain>

# --- Veritabanı ---
DATABASE_URL=postgresql://<user>:<password>@<dpg-xxxxx-a>/<dbname>

# --- Cloudflare R2 ---
R2_ACCOUNT_ID=<cloudflare-account-id>
R2_ACCESS_KEY_ID=<r2-access-key-id>
R2_SECRET_ACCESS_KEY=<r2-secret-access-key>
R2_BUCKET_NAME=<bucket-adi>
R2_CUSTOM_DOMAIN=<pub-xxxxxxxx.r2.dev veya cdn.ornek.com>

# RENDER_EXTERNAL_HOSTNAME → Render otomatik ekler, elle eklemeyin
```
