# Render.com Deployment Checklist — aybu-backend

> Hazırlanma tarihi: 2026-10-06
> Son güncelleme: 2026-10-06 — `busra` dalı, Render hazırlığı (`b2e7d02`) + `origin/busra` merge'ü (`9e7e4b0`) sonrası
> Satır numaraları güncel `config/settings.py`'ye göredir.

## 0. Proje Özeti (koddan tespit edilen)

| Bileşen | Değer | Kaynak |
|---|---|---|
| Dil / Framework | Python 3.12 + **Django 6.0.5** + Django REST Framework 3.17.1 | `requirements.txt`, `__pycache__/*.cpython-312.pyc` |
| Veritabanı | **PostgreSQL** (`psycopg2-binary`) — `DATABASE_URL` üzerinden `dj-database-url` ile | `config/settings.py:121-127` |
| Dosya depolama | **Cloudflare R2** (S3 uyumlu, `django-storages` + `boto3`) | `config/settings.py:225-247` |
| Kimlik doğrulama | DRF **Session + Basic Auth** (JWT **yok**, sadece yorum satırında önerilmiş) | `config/settings.py:183-188` |
| WSGI giriş noktası | `config.wsgi:application` | `config/wsgi.py` |
| API kökü | `/api/` (9 ViewSet), `/admin/`, `/api-auth/` | `config/urls.py`, `core/urls.py` |

> ⚠️ Not: Proje açıklamasında "JWT auth" geçebilir, ancak kodda JWT paketi (`djangorestframework-simplejwt`) **kurulu değil**. Mevcut auth Session + Basic Auth'tur.

> ⚠️ Repoda **`.env` dosyası yok** (`.gitignore` ile hariç tutulmuş). Aşağıdaki gerçek değerler ekip üyelerinin yerel `.env` dosyalarından / Cloudflare & Render panellerinden alınmalıdır.

---

## 1. Ortam Değişkenleri Envanteri

### 1.1 Başlangıçta `os.getenv` ile okunan değişkenler (R2 + DB)

| # | Değişken | Kategori | Kullanıldığı yer | Ne için | Durum |
|---|---|---|---|---|---|
| 1 | `DATABASE_URL` | Veritabanı | `config/settings.py:123` | PostgreSQL bağlantı string'i (`dj_database_url.config`) | ❗ **Zorunlu** — tanımsızsa ilk DB işleminde `ImproperlyConfigured` hatası verir |
| 2 | `R2_ACCESS_KEY_ID` | 3rd party (Cloudflare R2) | `config/settings.py:226` → `AWS_ACCESS_KEY_ID` | R2 API token Access Key | ❗ Zorunlu (medya yükleme) |
| 3 | `R2_SECRET_ACCESS_KEY` | 3rd party (Cloudflare R2) — **secret** | `config/settings.py:227` → `AWS_SECRET_ACCESS_KEY` | R2 API token Secret | ❗ Zorunlu |
| 4 | `R2_BUCKET_NAME` | 3rd party (Cloudflare R2) | `config/settings.py:228` → `AWS_STORAGE_BUCKET_NAME` | Medya dosyalarının yazılacağı bucket | ❗ Zorunlu |
| 5 | `R2_ACCOUNT_ID` | 3rd party (Cloudflare R2) | `config/settings.py:229` → `AWS_S3_ENDPOINT_URL` | Endpoint: `https://<ACCOUNT_ID>.eu.r2.cloudflarestorage.com` | ❗ Zorunlu — tanımsızsa endpoint `https://None.eu...` olur |

### 1.2 Başlangıçta hardcoded olan değerler — ✅ hepsi env'e taşındı

> Bu tablo **ilk incelemedeki (eski) durumu** gösterir; "Eski değer" sütunu artık kodda yok. Güncel karşılıkları "Şimdi" sütunundadır. Tüm değişkenlerin ayrıntısı: [DEPLOYMENT_CONFIG_REFERENCE.md](DEPLOYMENT_CONFIG_REFERENCE.md).

| # | Ayar | Eski satır | Eski değer | Sorun (çözüldü) | Şimdi |
|---|---|---|---|---|---|
| 6 | `SECRET_KEY` | `:29` |`'django-insecure-…'` (açık metin) | 🔴 **Güvenlik:** Git geçmişinde ve GitHub'da (`aybuteknofest-coder/aybu-backend`) duruyor → **ele geçirilmiş kabul edilmeli**. Session/CSRF imzaları bununla yapılır. | ✅ `SECRET_KEY` env (`:38`) — eski anahtarı **kullanmayın** |
| 7 | `DEBUG` | `:32` |`True` | 🔴 Production'da stack trace sızdırır; ayrıca CORS'u herkese açar (bkz. #9) | ✅ `DEBUG` env, varsayılan `False` (`:32`) |
| 8 | `ALLOWED_HOSTS` | `:34` |`[]` | 🔴 `DEBUG=False` iken boş liste → **her istek 400 Bad Request** | ✅ `ALLOWED_HOSTS` env + `RENDER_EXTERNAL_HOSTNAME` (`:45-50`) |
| 9 | `CORS_ALLOW_ALL_ORIGINS` / `CORS_ALLOWED_ORIGINS` | `:144-151` |`= DEBUG`; allow-list yorum satırında | 🟠 `DEBUG=False` olunca frontend'in hiçbir origin'i izinli olmaz → tarayıcıda CORS hatası | ✅ `CORS_ALLOWED_ORIGINS` env (`:172`) |
| 10 | `CSRF_TRUSTED_ORIGINS` | — |— | 🟠 HTTPS üzerinden admin paneli / session-auth POST'ları için gerekli | ✅ `CSRF_TRUSTED_ORIGINS` env (`:60`) |
| 11 | R2 bölge (jurisdiction) | `:208` |`.eu.` sabit | 🟡 Bucket EU jurisdiction'da değilse bağlantı başarısız olur. Commit `c40655c` EU için düzeltilmiş — doğrulanmalı | ⚠️ Değişmedi (`:229`) — bucket'ın EU'da olduğu doğrulanmalı |
| 12 | R2 public domain | — |— | 🟠 `AWS_QUERYSTRING_AUTH=False` + `AWS_S3_CUSTOM_DOMAIN` yok → dosya URL'leri `https://<acc>.eu.r2.cloudflarestorage.com/<bucket>/...` olur; bu S3 API endpoint'i **herkese açık okunamaz**, frontend'de görseller açılmaz | ✅ `R2_CUSTOM_DOMAIN` env (`:236`) — bucket public erişimi **manuel** açılmalı |

### 1.3 Diğer sabit değerler (env gerektirmez, bilgi amaçlı)

| Ayar | Satır | Değer | Not |
|---|---|---|---|
| `AWS_S3_REGION_NAME` | 230 | `'auto'` | R2 için doğru |
| `AWS_S3_SIGNATURE_VERSION` | 231 | `'s3v4'` | R2 için gerekli |
| `AWS_QUERYSTRING_AUTH` | 232 | `False` | İmzasız URL → bucket public olmalı ve `R2_CUSTOM_DOMAIN` tanımlı olmalı (bkz. #12) |
| `STATIC_URL` / `STATIC_ROOT` | 164-165 | `'/static/'`, `BASE_DIR/staticfiles` | WhiteNoise sunar; build'de `collectstatic` çalışmalı |
| `MEDIA_URL` / `MEDIA_ROOT` | 219-220 | `/media/`, `BASE_DIR/media` | Medya R2'de olduğu için Render'da kullanılmaz |
| `TIME_ZONE` | 154 | `'UTC'` | İsteğe göre `Europe/Istanbul` |
| `REST_FRAMEWORK.DEFAULT_RENDERER_CLASSES` | 195-199 | Browsable API açık | Production'da kapatılması önerilir |

### 1.4 Bulunmayanlar (tarama sonucu)

- E-posta / SMTP ayarı: **yok**
- JWT / OAuth / 3rd party auth anahtarı: **yok**
- Harici API çağrısı (`requests`, `httpx`, sabit base URL): **yok** (`core/` içinde)
- Redis / Celery / cache backend: **yok**

---

## 2. Veritabanı Bağlantı Bilgileri

**Konum:** `config/settings.py:121-127`

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
| `DATABASE_URL` | PostgreSQL bağlantı string'i | ✅ `settings.py:123` | ⬜ Render DB oluşturulunca | **Evet** |
| `R2_ACCOUNT_ID` | R2 endpoint'i için Cloudflare hesap ID | ✅ `settings.py:229` | ⬜ Yerel `.env`'den alınmalı | Hayır (ama gizli tutun) |
| `R2_ACCESS_KEY_ID` | R2 API token access key | ✅ `settings.py:226` | ⬜ Yerel `.env`'den alınmalı | **Evet** |
| `R2_SECRET_ACCESS_KEY` | R2 API token secret | ✅ `settings.py:227` | ⬜ Yerel `.env`'den alınmalı | **Evet** |
| `R2_BUCKET_NAME` | Medya bucket adı | ✅ `settings.py:228` | ⬜ Yerel `.env`'den alınmalı | Hayır |
| `R2_CUSTOM_DOMAIN` | Görsellerin public URL domain'i | ✅ settings.py | ⬜ MISSING — R2'de public erişim açılmalı | Hayır |
| `WEB_CONCURRENCY` | Gunicorn worker sayısı | Gunicorn okur | ⬜ Opsiyonel | Hayır |
| `RENDER_EXTERNAL_HOSTNAME` | **Render otomatik ekler**, elle eklemeyin | ✅ `ALLOWED_HOSTS`a otomatik eklenir | — | Hayır |

**Lejant:** ✅ mevcut · ❌ eksik · ⬜ doldurulmadı / doğrulanmadı · ❓ bilinmiyor

### 3.2 Deploy öncesi kod değişiklikleri — ✅ uygulandı

Render hazırlığı commit `b2e7d02`'de; merge düzeltmeleri `busra` dalındaki merge commit'inde.

- [x] 🔴 **Migration çakışması giderildi:** merge ile iki ayrı `0003` geldi (`0003_iletisimmesaji_uyebasvurusu` ve `0003_iletisimmesaji_uyebasvurusu_announcement_event_date_and_more`) → `migrate` *"Conflicting migrations detected"* ile duruyordu ve Render build'i kırılırdı. Aynı tabloları oluşturan kopya silindi; yalnızca yeni alanları (`Announcement.location`, `Announcement.event_date`) ekleyen `0004_announcement_location_event_date` oluşturuldu.
  - Kopya `0003`'ü yerel DB'sine **uygulamış** ekip üyeleri bir kez `python manage.py migrate core 0004 --fake` çalıştırmalı (tablolar ve alanlar zaten var).
- [x] Admin: `AnnouncementAdmin`'e "Etkinlik Bilgisi" bölümü (`location`, `event_date`) eklendi
- [x] Merge kalıntıları temizlendi (`models.py` sonundaki fazla import, tekrarlanan yorum başlıkları)

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

### 3.4 Deploy öncesi / sonrası doğrulama

Push öncesi (yerelde):
- [ ] `python manage.py makemigrations --check --dry-run` → `No changes detected`
- [ ] `python manage.py migrate` boş bir DB'de hatasız tamamlanıyor
- [ ] `python manage.py check` → `no issues`

Deploy sonrası:

- [ ] `https://<servis>.onrender.com/api/` → 200 ve JSON döner
- [ ] `https://<servis>.onrender.com/admin/` → CSS ile yüklenir
- [ ] `python manage.py createsuperuser` (Render Shell) ile admin oluşturuldu
- [ ] Admin'den bir görsel yüklendi → R2 bucket'ında göründü
- [ ] Görselin API'deki URL'si tarayıcıda açılıyor (public domain doğru)
- [ ] Frontend'den `GET /api/events/` CORS hatası olmadan çalışıyor
- [ ] `GET /api/announcements/` yanıtında `location` ve `event_date` alanları var
- [ ] Frontend'den `POST /api/uye-basvurulari/` ve `POST /api/iletisim-mesajlari/` (AllowAny) çalışıyor
- [ ] Hata sayfasında stack trace **görünmüyor** (`DEBUG=False` doğrulaması)

### 3.5 Güvenlik aksiyonları

- [ ] 🔴 GitHub'daki eski `SECRET_KEY` geçersiz sayıldı, yenisi yalnızca Render'da
- [ ] R2 API token'ı yalnızca ilgili bucket'a "Object Read & Write" yetkisiyle sınırlandırıldı
- [ ] `.env` dosyasının hiçbir commit'te bulunmadığı doğrulandı (`git log --all -- .env` → boş ✅)
