# Render.com Deployment Checklist — aybu-backend

> Hazırlanma tarihi: 2026-10-06
> Kapsam: `aybu-backend` deposu (commit `452f5fe`)

## 0. Proje Özeti (koddan tespit edilen)

| Bileşen | Değer | Kaynak |
|---|---|---|
| Dil / Framework | Python 3.12 + **Django 6.0.5** + Django REST Framework 3.17.1 | `requirements.txt`, `__pycache__/*.cpython-312.pyc` |
| Veritabanı | **PostgreSQL** (`psycopg2-binary`) — `DATABASE_URL` üzerinden `dj-database-url` ile | `config/settings.py:94-100` |
| Dosya depolama | **Cloudflare R2** (S3 uyumlu, `django-storages` + `boto3`) | `config/settings.py:204-221` |
| Kimlik doğrulama | DRF **Session + Basic Auth** (JWT **yok**, sadece yorum satırında önerilmiş) | `config/settings.py:162-166` |
| WSGI giriş noktası | `config.wsgi:application` | `config/wsgi.py` |
| API kökü | `/api/` (9 ViewSet), `/admin/`, `/api-auth/` | `config/urls.py`, `core/urls.py` |

> ⚠️ Not: Proje açıklamasında "JWT auth" geçebilir, ancak kodda JWT paketi (`djangorestframework-simplejwt`) **kurulu değil**. Mevcut auth Session + Basic Auth'tur.

> ⚠️ Repoda **`.env` dosyası yok** (`.gitignore` ile hariç tutulmuş). Aşağıdaki gerçek değerler ekip üyelerinin yerel `.env` dosyalarından / Cloudflare & Render panellerinden alınmalıdır.

---

## 1. Ortam Değişkenleri Envanteri

### 1.1 Kodun şu an `os.getenv` ile okuduğu değişkenler

| # | Değişken | Kategori | Kullanıldığı yer | Ne için | Durum |
|---|---|---|---|---|---|
| 1 | `DATABASE_URL` | Veritabanı | `config/settings.py:96` | PostgreSQL bağlantı string'i (`dj_database_url.config`) | ❗ **Zorunlu** — tanımsızsa Django `ImproperlyConfigured` hatası verir |
| 2 | `R2_ACCESS_KEY_ID` | 3rd party (Cloudflare R2) | `config/settings.py:205` → `AWS_ACCESS_KEY_ID` | R2 API token Access Key | ❗ Zorunlu (medya yükleme) |
| 3 | `R2_SECRET_ACCESS_KEY` | 3rd party (Cloudflare R2) — **secret** | `config/settings.py:206` → `AWS_SECRET_ACCESS_KEY` | R2 API token Secret | ❗ Zorunlu |
| 4 | `R2_BUCKET_NAME` | 3rd party (Cloudflare R2) | `config/settings.py:207` → `AWS_STORAGE_BUCKET_NAME` | Medya dosyalarının yazılacağı bucket | ❗ Zorunlu |
| 5 | `R2_ACCOUNT_ID` | 3rd party (Cloudflare R2) | `config/settings.py:208` → `AWS_S3_ENDPOINT_URL` | Endpoint: `https://<ACCOUNT_ID>.eu.r2.cloudflarestorage.com` | ❗ Zorunlu — tanımsızsa endpoint `https://None.eu...` olur |

### 1.2 Hardcoded olan ve env'e taşınması GEREKEN değerler

| # | Ayar | Dosya:Satır | Mevcut değer | Sorun | Önerilen env değişkeni |
|---|---|---|---|---|---|
| 6 | `SECRET_KEY` | `config/settings.py:29` | `'django-insecure-…'` (açık metin) | 🔴 **Güvenlik:** Git geçmişinde ve GitHub'da (`aybuteknofest-coder/aybu-backend`) duruyor → **ele geçirilmiş kabul edilmeli**. Session/CSRF imzaları bununla yapılır. | `SECRET_KEY` (yeni, rastgele üretilmiş) |
| 7 | `DEBUG` | `config/settings.py:32` | `True` | 🔴 Production'da stack trace sızdırır; ayrıca CORS'u herkese açar (bkz. #9) | `DEBUG=False` |
| 8 | `ALLOWED_HOSTS` | `config/settings.py:34` | `[]` | 🔴 `DEBUG=False` iken boş liste → **her istek 400 Bad Request** | `ALLOWED_HOSTS` (+ Render'ın otomatik verdiği `RENDER_EXTERNAL_HOSTNAME`) |
| 9 | `CORS_ALLOW_ALL_ORIGINS` / `CORS_ALLOWED_ORIGINS` | `config/settings.py:144-151` | `= DEBUG`; allow-list yorum satırında | 🟠 `DEBUG=False` olunca frontend'in hiçbir origin'i izinli olmaz → tarayıcıda CORS hatası | `CORS_ALLOWED_ORIGINS` (virgülle ayrılmış) |
| 10 | `CSRF_TRUSTED_ORIGINS` | *(tanımlı değil)* | — | 🟠 HTTPS üzerinden admin paneli / session-auth POST'ları için gerekli | `CSRF_TRUSTED_ORIGINS` |
| 11 | R2 bölge (jurisdiction) | `config/settings.py:208` | `.eu.` sabit | 🟡 Bucket EU jurisdiction'da değilse bağlantı başarısız olur. Commit `c40655c` EU için düzeltilmiş — doğrulanmalı | (opsiyonel) `R2_ENDPOINT_URL` |
| 12 | R2 public domain | *(tanımlı değil)* | — | 🟠 `AWS_QUERYSTRING_AUTH=False` + `AWS_S3_CUSTOM_DOMAIN` yok → dosya URL'leri `https://<acc>.eu.r2.cloudflarestorage.com/<bucket>/...` olur; bu S3 API endpoint'i **herkese açık okunamaz**, frontend'de görseller açılmaz | `R2_CUSTOM_DOMAIN` (ör. `pub-xxxx.r2.dev` veya özel domain) → `AWS_S3_CUSTOM_DOMAIN` |

### 1.3 Diğer sabit değerler (env gerektirmez, bilgi amaçlı)

| Ayar | Satır | Değer | Not |
|---|---|---|---|
| `AWS_S3_REGION_NAME` | 209 | `'auto'` | R2 için doğru |
| `AWS_S3_SIGNATURE_VERSION` | 210 | `'s3v4'` | R2 için gerekli |
| `AWS_QUERYSTRING_AUTH` | 211 | `False` | İmzasız URL → bucket public olmalı (bkz. #12) |
| `STATIC_URL` | 137 | `'static/'` | `STATIC_ROOT` **tanımlı değil** → `collectstatic` başarısız olur (bkz. §3.2) |
| `MEDIA_URL` / `MEDIA_ROOT` | 198-199 | `/media/`, `BASE_DIR/media` | Medya R2'de olduğu için Render'da kullanılmaz |
| `TIME_ZONE` | 127 | `'UTC'` | İsteğe göre `Europe/Istanbul` |
| `REST_FRAMEWORK.DEFAULT_RENDERER_CLASSES` | 174-178 | Browsable API açık | Production'da kapatılması önerilir |

### 1.4 Bulunmayanlar (tarama sonucu)

- E-posta / SMTP ayarı: **yok**
- JWT / OAuth / 3rd party auth anahtarı: **yok**
- Harici API çağrısı (`requests`, `httpx`, sabit base URL): **yok** (`core/` içinde)
- Redis / Celery / cache backend: **yok**

---

## 2. Veritabanı Bağlantı Bilgileri

**Konum:** `config/settings.py:94-100`

```python
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}
```

| Alan | Değer | Durum |
|---|---|---|
| Motor | PostgreSQL (`psycopg2-binary==2.9.9`) | ✅ |
| Host | `DATABASE_URL` içinden | ❓ Doğrulanmadı — repoda değer yok |
| Port | `DATABASE_URL` içinden (Postgres varsayılanı `5432`) | ❓ Doğrulanmadı |
| Database Name | `DATABASE_URL` içinden | ❓ Doğrulanmadı |
| Username / Auth | `DATABASE_URL` içinde kullanıcı adı + parola (password auth) | ❓ Doğrulanmadı |
| SSL/TLS | **Kodda ayarlanmamış** (`ssl_require` yok) | 🟡 Aşağıya bakın |
| Bağlantı süresi | `conn_max_age=600` → kalıcı bağlantı, 10 dk yeniden kullanım | ✅ |
| Sağlık kontrolü | `conn_health_checks=True` → yeniden kullanmadan önce bağlantı test edilir | ✅ |
| Pool | Harici pool (PgBouncer / psycopg pool) **yok**; her Gunicorn worker kendi kalıcı bağlantısını tutar | ℹ️ |

**Format:**
```
postgresql://<USER>:<PASSWORD>@<HOST>:<PORT>/<DB_NAME>
```

**SSL notları:**
- Render Postgres **Internal Database URL** (aynı bölgedeki web servisinden) kullanılırsa SSL zorunlu değildir — **önerilen budur**.
- **External Database URL** veya harici bir sağlayıcı (Neon, Supabase vb.) kullanılırsa URL sonuna `?sslmode=require` ekleyin ya da koda `ssl_require=True` ekleyin.

**Pool / bağlantı limiti notu:** Bağlantı sayısı ≈ `WEB_CONCURRENCY` (Gunicorn worker sayısı) × instance sayısı. Render'ın ücretsiz/başlangıç Postgres planlarının bağlantı limitini aşmamaya dikkat edin.

**Yerel geliştirme:** Repoda `db.sqlite3` var, ancak `settings.py` SQLite'a fallback yapmıyor; yerelde `DATABASE_URL=sqlite:///db.sqlite3` veya bir Postgres URL'si kullanılıyor olmalı. **SQLite'taki veriler Render Postgres'e otomatik taşınmaz** — gerekiyorsa `dumpdata`/`loaddata` ile aktarın.

---

## 3. Render.com Deployment Checklist

### 3.1 Render Dashboard → Environment Variables

Render'da **Environment → Add from .env** ile aşağıdaki bloğu yapıştırıp değerleri doldurabilirsiniz.

```env
# --- Python ---
PYTHON_VERSION=3.12.5

# --- Django çekirdek ---
SECRET_KEY=<YENİ-RASTGELE-50+-KARAKTER>
DEBUG=False
ALLOWED_HOSTS=<servis-adi>.onrender.com
CORS_ALLOWED_ORIGINS=https://<frontend-domain>
CSRF_TRUSTED_ORIGINS=https://<servis-adi>.onrender.com,https://<frontend-domain>

# --- Veritabanı ---
DATABASE_URL=<Render Postgres → Internal Database URL>

# --- Cloudflare R2 ---
R2_ACCOUNT_ID=<cloudflare-account-id>
R2_ACCESS_KEY_ID=<r2-api-token-access-key>
R2_SECRET_ACCESS_KEY=<r2-api-token-secret>
R2_BUCKET_NAME=<bucket-adi>
R2_CUSTOM_DOMAIN=<pub-xxxx.r2.dev veya cdn.ornek.com>

# --- Opsiyonel ---
WEB_CONCURRENCY=2
```

| Değişken | Açıklama | Kod okuyor mu? | Değer doğrulandı mı? | Secret? |
|---|---|---|---|---|
| `PYTHON_VERSION` | Render'ın kullanacağı Python sürümü; Django 6.0 ≥ 3.12 ister | Render okur | ⬜ | Hayır |
| `SECRET_KEY` | Django imzalama anahtarı — **yenisini üretin**, eskisi ifşa | ✅ settings.py | ⬜ MISSING | **Evet** |
| `DEBUG` | Production'da `False` | ✅ settings.py | ⬜ MISSING | Hayır |
| `ALLOWED_HOSTS` | Servise erişilecek host adları | ✅ settings.py | ⬜ MISSING | Hayır |
| `CORS_ALLOWED_ORIGINS` | Frontend origin(ler)i | ✅ settings.py | ⬜ MISSING — frontend domain bilinmiyor | Hayır |
| `CSRF_TRUSTED_ORIGINS` | HTTPS POST için güvenilir origin'ler | ✅ settings.py | ⬜ MISSING | Hayır |
| `DATABASE_URL` | PostgreSQL bağlantı string'i | ✅ `settings.py:96` | ⬜ Render DB oluşturulunca | **Evet** |
| `R2_ACCOUNT_ID` | R2 endpoint'i için Cloudflare hesap ID | ✅ `settings.py:208` | ⬜ Yerel `.env`'den alınmalı | Hayır (ama gizli tutun) |
| `R2_ACCESS_KEY_ID` | R2 API token access key | ✅ `settings.py:205` | ⬜ Yerel `.env`'den alınmalı | **Evet** |
| `R2_SECRET_ACCESS_KEY` | R2 API token secret | ✅ `settings.py:206` | ⬜ Yerel `.env`'den alınmalı | **Evet** |
| `R2_BUCKET_NAME` | Medya bucket adı | ✅ `settings.py:207` | ⬜ Yerel `.env`'den alınmalı | Hayır |
| `R2_CUSTOM_DOMAIN` | Görsellerin public URL domain'i | ✅ settings.py | ⬜ MISSING — R2'de public erişim açılmalı | Hayır |
| `WEB_CONCURRENCY` | Gunicorn worker sayısı | Gunicorn okur | ⬜ Opsiyonel | Hayır |
| `RENDER_EXTERNAL_HOSTNAME` | **Render otomatik ekler**, elle eklemeyin | ✅ `ALLOWED_HOSTS`a otomatik eklenir | — | Hayır |

**Lejant:** ✅ mevcut · ❌ eksik · ⬜ doldurulmadı / doğrulanmadı · ❓ bilinmiyor

### 3.2 Deploy öncesi kod değişiklikleri — ✅ uygulandı (2026-10-06, henüz push edilmedi)

- [x] `SECRET_KEY` env'den okunuyor; `DEBUG=False` iken tanımsızsa uygulama **başlamaz** (`ImproperlyConfigured`). Rastgele yedek anahtar yalnızca `DEBUG=True`'da kullanılır.
- [x] `DEBUG = os.environ.get('DEBUG', 'False') == 'True'`
- [x] `ALLOWED_HOSTS` env'den (varsayılan `localhost,127.0.0.1`) + `RENDER_EXTERNAL_HOSTNAME` otomatik ekleniyor
- [x] `CORS_ALLOWED_ORIGINS` env'den (artık `DEBUG`'a bağlı değil — yerelde de `.env`'e frontend origin'i yazılmalı)
- [x] `CSRF_TRUSTED_ORIGINS` env'den
- [x] `SECURE_PROXY_SSL_HEADER`, `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE = not DEBUG`
- [x] `STATIC_URL = '/static/'`, `STATIC_ROOT = BASE_DIR / 'staticfiles'`
- [x] WhiteNoise middleware (2. sıra) + `CompressedManifestStaticFilesStorage`
- [x] `requirements.txt`: `whitenoise==6.12.0`, `gunicorn==23.0.0`
- [x] `AWS_S3_CUSTOM_DOMAIN = R2_CUSTOM_DOMAIN` (şemasız host, ör. `pub-xxxx.r2.dev`)
- [x] `.gitignore`: `staticfiles/` eklendi (`.env` zaten vardı)
- [ ] 🔴 Cloudflare'da bucket için public erişim (r2.dev veya custom domain) açılmalı — **manuel**
- [ ] (Önerilen) Production'da `BrowsableAPIRenderer` kapatılmalı
- [ ] (Önerilen) `BasicAuthentication` production'da kaldırılmalı
- [ ] (Önerilen) HSTS (`SECURE_HSTS_SECONDS`) — custom domain netleşince

**Yerel `.env` örneği** (değişikliklerden sonra yerelde çalışmak için gerekli):
```env
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=...
R2_CUSTOM_DOMAIN=pub-xxxx.r2.dev
```

### 3.3 Render servis ayarları

| Alan | Değer |
|---|---|
| Service type | Web Service |
| Root directory | *(repo kökü — `manage.py` burada)* |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate` |
| Start Command | `gunicorn config.wsgi:application` |
| Health check path | `/api/` |
| Region | Postgres ile **aynı bölge** (Internal URL için şart) — R2 EU olduğundan **Frankfurt** önerilir |

### 3.4 Deploy sonrası doğrulama

- [ ] `https://<servis>.onrender.com/api/` → 200 ve JSON döner
- [ ] `https://<servis>.onrender.com/admin/` → CSS ile yüklenir
- [ ] `python manage.py createsuperuser` (Render Shell) ile admin oluşturuldu
- [ ] Admin'den bir görsel yüklendi → R2 bucket'ında göründü
- [ ] Görselin API'deki URL'si tarayıcıda açılıyor (public domain doğru)
- [ ] Frontend'den `GET /api/events/` CORS hatası olmadan çalışıyor
- [ ] Frontend'den `POST /api/uye-basvurulari/` ve `POST /api/iletisim-mesajlari/` (AllowAny) çalışıyor
- [ ] Hata sayfasında stack trace **görünmüyor** (`DEBUG=False` doğrulaması)

### 3.5 Güvenlik aksiyonları

- [ ] 🔴 GitHub'daki eski `SECRET_KEY` geçersiz sayıldı, yenisi yalnızca Render'da
- [ ] R2 API token'ı yalnızca ilgili bucket'a "Object Read & Write" yetkisiyle sınırlandırıldı
- [ ] `.env` dosyasının hiçbir commit'te bulunmadığı doğrulandı (`git log --all -- .env` → boş ✅)
