# AfriData — Complete AWS Deployment Assessment Report
**Date:** 2026-06-09 | **Analyst:** Senior Cloud / MLOps / Django / AWS Architect  
**Codebase Root:** `c:\Users\josep\afridata` | **Evidence-based — no assumptions made**

---

## SECTION 1 — PROJECT ARCHITECTURE ANALYSIS

### 1.1 Project Identity

| Attribute | Value |
|---|---|
| **Project name** | AfriData Commons |
| **Purpose** | African open-data repository — Kaggle-style platform for uploading, discovering, downloading, and analysing African datasets, with a token-based economy, AI-powered metadata inference, a data-standardisation pipeline, and a content + collaborative recommendation engine |
| **Architecture** | Monolithic Django app (single process, no microservices, no message queue in production today) |
| **Django version** | **3.2.25** (LTS, EOL April 2024 — upgrade blocker) |
| **Python version** | **3.11** (confirmed by `FROM python:3.11-slim` in Dockerfile) |

### 1.2 Django Apps Installed

```
home            – Landing page, trending datasets, statistics
dataset         – Core upload / download / preview / token economy
accounts        – CustomUser, UserProfile, token management, referrals
community       – Forum (Topic → Thread → Post → PostVote)
api             – DRF REST API
admin_dashboard – Custom admin views
mpesa           – M-Pesa mobile payment integration (callback URLs, STK push)
metadata        – AI metadata inference pipeline (LLM + ML semantic classifier)
recommendations – Hybrid recommendation engine (TF-IDF + ALS/SVD)
standardiser    – 8-stage data-standardisation pipeline (schema matching + Gemini)
schema_graph    – ER diagram viewer
```

### 1.3 Frontend Technologies

- **Django templates** (server-rendered HTML, Jinja2-like syntax)
- **Tailwind CSS** (via `tailwind.config.js` + `package.json`)
- **Chart.js** (dataset previews / visualisations rendered in-browser)
- **FontAwesome icons**
- No React/Vue/Next.js — fully server-side rendered

### 1.4 API Architecture

- **Django REST Framework** with `SessionAuthentication`
- `IsAuthenticatedOrReadOnly` permissions
- `PageNumberPagination` (PAGE_SIZE=20)
- JWT was removed (commented out in settings line 228)
- API prefixes: `/api/`, `/api/metadata/`, `/api/recommendations/`
- CORS headers enabled via `django-cors-headers`

### 1.5 Authentication

- Custom `CustomUser` model extending `AbstractUser`
- Email used as `USERNAME_FIELD`
- Session-based auth (not JWT)
- Login tracking via `LoginAttempt` model
- Referral code system built in

### 1.6 Architecture Diagram (Text)

```
Internet
    │
    ▼
[Nginx / ALB]          (reverse proxy / SSL termination)
    │
    ▼
[Gunicorn (WSGI)]      (manages Django worker processes)
    │
    ▼
[Django Application]
├── home/              (landing, trending, stats)
├── dataset/           (upload, download, preview, token economy)
│   └── views.py       → starts metadata pipeline in background thread
├── accounts/          (CustomUser, UserProfile, token wallet)
├── community/         (forum, threads, posts, voting)
├── api/               (DRF endpoints)
├── admin_dashboard/   (custom admin)
├── mpesa/             (M-Pesa STK push, callback)
├── metadata/          ← AI PIPELINE
│   ├── core/profiler.py         (column statistics)
│   ├── core/extractors/         (CSV/Excel + SQL extractors)
│   ├── core/enhancement/semantic_classifier.py  (scikit-learn SGDClassifier)
│   ├── core/enhancement/llm_generator.py        (Gemini/OpenAI/Anthropic/Ollama)
│   └── core/schema_builder.py   (JSON Schema draft-07 output)
├── recommendations/  ← RECOMMENDATION ENGINE
│   ├── domain/engines/content_based.py  (TF-IDF + cosine similarity)
│   ├── domain/engines/collaborative.py  (ALS or SVD matrix factorisation)
│   └── domain/engines/hybrid.py         (weighted fusion)
└── standardiser/     ← DATA STANDARDISATION PIPELINE
    └── pipeline_lib/ (8-stage: load → schema match → AI → clean → validate → export)
    │
    ▼
[SQLite / MySQL / RDS]   (primary database)
    │
    ▼
[Local filesystem]       (datasets/, profile_pics/, processed/, exports/)
```

---

## SECTION 2 — DJANGO ANALYSIS

### 2.1 settings.py Key Configuration

| Setting | Value | Deployment Note |
|---|---|---|
| `SECRET_KEY` | From env `SECRET_KEY` | ✅ Good — env-driven |
| `DEBUG` | From env `DEBUG` (default `True`) | ⚠️ Must set `False` in prod |
| `ALLOWED_HOSTS` | From env list | ✅ Good — set EC2 public DNS + domain |
| Database | **SQLite** locally; `dj_database_url` when `RENDER=true` | ⚠️ SQLite in prod = BLOCKER |
| `STATIC_ROOT` | `BASE_DIR/staticfiles` | ✅ collectstatic ready |
| `STATIC_URL` | `/static/` | ✅ |
| `STATICFILES_STORAGE` | `whitenoise.CompressedManifestStaticFilesStorage` | ✅ whitenoise configured |
| `MEDIA_ROOT` | **Not explicitly set** | 🚨 BLOCKER — files go to relative paths |
| `MEDIA_URL` | **Not set** | 🚨 BLOCKER |
| `GEMINI_API_KEY` | From env | ✅ env-driven |
| `LLM_BACKEND` | From env, default `gemini` | ✅ |
| `LLM_MODEL` | `gemini-2.5-flash` | ✅ |
| CORS | `corsheaders` middleware installed | ✅ |
| REST_FRAMEWORK | Session auth, `IsAuthenticatedOrReadOnly` | ✅ |

### 2.2 Missing Production Settings (Deployment Blockers)

The following settings are **absent from settings.py** and **must be added** before deployment:

```python
# MUST ADD for production
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # or S3
MEDIA_URL = '/media/'

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Logging to CloudWatch or file
# File upload size limit
DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000  # 500MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 524288000
```

### 2.3 Database Configuration

```python
# CURRENT (Local) — SQLite only
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}

# PRODUCTION PATH (already stubbed but commented out):
# uses dj_database_url.parse(os.environ.get('DATABASE_URL'))  # triggered by RENDER env var
```

**Evidence:** settings.py lines 111–138. MySQL credentials are in `.env.example` (lines 15–19). The `mysqlclient==2.1.1` package is in requirements.txt (line 16), confirming MySQL is the intended production database.

---

## SECTION 3 — DATABASE ANALYSIS

### 3.1 Database Engine

| Environment | Engine | Version |
|---|---|---|
| Current local | SQLite 3 | Any |
| Intended production | MySQL 5.7 / 8.0 | Confirmed by docker-compose.yml and mysqlclient dependency |

### 3.2 Models Inventory (All Tables)

**accounts app:**
- `CustomUser` — 20+ fields, custom user table
- `UserProfile` — token wallet, subscription status, monthly limits
- `LoginAttempt` — security audit log
- `TokenPurchase` — payment records

**dataset app:**
- `Dataset` (`dataset_files` table) — core dataset record, file references, token cost, quality tier, metadata
- `Comment` — dataset comments, upvote counts
- `TokenTransaction` — full token ledger
- `PremiumPurchase` — premium dataset payment records (Stripe integration referenced)
- `Download` — download tracking, one record per user/dataset pair
- `Referral` — referral bonus tracking

**recommendations app:**
- `UserInteraction` — every user action (view/download/bookmark/rating/search_click)
- `DatasetProxy` — denormalised copy of dataset metadata for fast scoring
- `RecommendationResult` — persisted Top-N results per user (JSON arrays)

**metadata app:**
- `PipelineRun` (UUID PK) — one record per AI pipeline execution
- `MetadataResult` — JSON Schema output per run
- `ColumnProfile` — per-column semantic profile records

**standardiser app:**
- `StandardisationJob` — 8-stage pipeline job tracking
- `JobResult` — cached pipeline outputs (column mappings, quality reports, file paths)
- `SchemaMappingEdit` — user edits to AI-generated column mappings
- `DatasetVersion` — version history with schema snapshots
- `ProcessingLog` — detailed per-step pipeline logs

**community app:**
- `Topic`, `Thread`, `Post`, `PostVote`, `UserActivity`

**Total tables: ~25**

### 3.3 Database Recommendations for AWS

| Aspect | Recommendation |
|---|---|
| **Service** | **Amazon RDS for MySQL 8.0** (db.t3.micro for demo, db.t3.small for prod) |
| **Storage** | 20 GB gp3 SSD, auto-scaling enabled |
| **Multi-AZ** | Not required for demo; enable for production |
| **Backups** | 7-day retention window |
| **Current DB size** | `db.sqlite3` = **1.03 MB** — virtually empty, easy to migrate |
| **Estimated Year 1** | 5–20 GB (depends on dataset metadata JSON blob growth) |

> **Evidence:** `db.sqlite3` file size measured at 1,056,768 bytes (1.03 MB). Database is in early-stage with minimal data.

---

## SECTION 4 — AI / MACHINE LEARNING ANALYSIS

### 4.1 Complete ML/AI Inventory

#### Model 1: SemanticClassifier (scikit-learn SGDClassifier)

| Attribute | Value |
|---|---|
| **Location** | `metadata/core/enhancement/semantic_classifier.py` |
| **Purpose** | Assigns semantic type labels (email, phone, currency, id, age…) to dataset columns from 23-feature vector |
| **Algorithm** | SGDClassifier (log_loss = logistic regression) with StandardScaler, trained on **synthetic data at runtime** |
| **Model file** | `metadata/core/enhancement/artifacts/semantic_classifier.joblib` — **does not exist yet** (model is trained in memory on every startup if file is missing) |
| **Size on disk** | ~100 KB when serialised (tiny sklearn Pipeline) |
| **RAM usage** | ~5 MB (23 features × synthetic dataset of ~200 samples) |
| **CPU** | Negligible — classification is instant |
| **GPU** | Not required |
| **Loading** | On import/first use; trains synthetically if no `.joblib` found |

**Evidence:** `semantic_classifier.py` lines 372–391, 602–637 — `_load()` tries to load from `artifacts/`, falls back to `_train()` which calls `_build_training_data()`.

---

#### Model 2: LLMGenerator (External LLM API)

| Attribute | Value |
|---|---|
| **Location** | `metadata/core/enhancement/llm_generator.py` |
| **Purpose** | Enriches column profiles with description, tags, business_name, notes via LLM |
| **Backend (current)** | **Google Gemini 2.5 Flash** (configured via `LLM_BACKEND=gemini` + `GEMINI_API_KEY`) |
| **Other backends** | OpenAI, Anthropic Claude, Ollama (local) — all supported, plug-and-play |
| **Model size** | Zero — runs in Google Cloud; no local model weights |
| **RAM usage** | Zero local RAM for model (only JSON payload in memory) |
| **CPU** | Minimal — HTTP request/response only |
| **GPU** | **Not required** — inference happens remotely |
| **Loading** | Instantiated per request; API key read from Django settings |
| **Batching** | 10 columns per batch (configurable via `LLM_BATCH_SIZE`) |
| **Timeout** | 30s per request; 3 retries with exponential backoff |

**Evidence:** `llm_generator.py` lines 387–431, `settings.py` lines 240–243.

---

#### Model 3: ContentBasedEngine (TF-IDF + Cosine Similarity)

| Attribute | Value |
|---|---|
| **Location** | `recommendations/domain/engines/content_based.py` |
| **Purpose** | Scores datasets by cosine similarity of TF-IDF bag-of-words profile to user's weighted interaction history |
| **Algorithm** | `sklearn.TfidfVectorizer` + sparse matrix cosine similarity |
| **Model file** | `models/tfidf/item_matrix` (`.npz` sparse matrix + `.npy` item_id index) — loaded via `vector_store.py` |
| **Size on disk** | ~1–50 MB depending on dataset count and vocabulary size |
| **RAM usage** | ~10–200 MB (sparse matrix: n_datasets × n_vocab_terms) |
| **CPU** | Low — sparse dot products |
| **GPU** | Not required |
| **Loading** | `engine.load()` called in `dataset_detail` view on every request (⚠️ inefficient — should be loaded once at startup) |
| **Cold-start** | Falls back to popularity ranking when user has no interactions |

**Evidence:** `content_based.py` lines 170–240; `dataset/views.py` lines 232–246 — `ContentBasedEngine()` instantiated per request.

---

#### Model 4: CollaborativeEngine (ALS / SVD Matrix Factorisation)

| Attribute | Value |
|---|---|
| **Location** | `recommendations/domain/engines/collaborative.py` |
| **Purpose** | User-item collaborative filtering via latent factor models |
| **Algorithm** | ALS (`implicit` library) or Truncated SVD (sklearn), selected by `CF_MODEL_TYPE` setting |
| **Model file** | `models/collaborative/cf_model.joblib` |
| **Size on disk** | ~1–50 MB (depends on n_users × n_factors) |
| **RAM usage** | ~50–500 MB for mid-scale deployment |
| **CPU** | Low at inference (dot products); high during training |
| **GPU** | Not required for inference; optional for ALS training |
| **Loading** | `model_store.load_model()` — supports local or S3 backend |
| **Cold-start** | Returns 0.0 scores; hybrid engine falls back to content-based |

**Evidence:** `collaborative.py` lines 36–41, `model_store.py` lines 117–204.

---

#### Model 5: DataStandardisation AI Schema Generator (Gemini)

| Attribute | Value |
|---|---|
| **Location** | `pipeline_lib/schema.py` (via `pipeline.py`'s `generate_schema_with_ai`) |
| **Purpose** | Generates column mapping instructions and domain-specific schema for uploaded datasets |
| **Backend** | Google Gemini (same API key as LLMGenerator) |
| **RAM / CPU / GPU** | Same as LLMGenerator — remote API, no local resources |
| **Schema caching** | `schema_registry.json` (10 KB currently, grows with usage) |

**Evidence:** `pipeline.py` lines 131–133; `schema_registry.json` exists at root.

---

### 4.2 AI/ML Resource Summary

| Component | RAM | CPU | GPU | External API Cost |
|---|---|---|---|---|
| SemanticClassifier | ~5 MB | Negligible | None | None |
| LLM Generator (Gemini) | ~2 MB | Negligible | None | ~$0.0004/call (Gemini Flash) |
| ContentBasedEngine | ~10–200 MB | Low | None | None |
| CollaborativeEngine | ~50–500 MB | Low | None | None |
| Standardisation Pipeline | ~100 MB (Polars df) | Medium during processing | None | Gemini API calls |

**Total estimated RAM for AI stack at idle:** ~200–800 MB  
**GPU requirement:** ❌ Not required for any component  
**External dependencies:** Google Gemini API (GEMINI_API_KEY must be set and valid)

---

## SECTION 5 — STORAGE ANALYSIS

### 5.1 Current Storage Locations

| Path | Type | Current Size | Files | Notes |
|---|---|---|---|---|
| `datasets/` | Dataset uploads (FileField) | **21.01 MB** | 26 files | Primary user content — grows unbounded |
| `static/` | CSS/JS/images | **33.91 MB** | 14 files | Collected by whitenoise |
| `profile_pics/` | User profile images | **0.22 MB** | 1 file | |
| `processed/` | Standardiser output data | **0.27 MB** | 8 files | Temp CSV/parquet after pipeline |
| `exports/` | User export downloads | **0.65 MB** | 11 files | |
| `db.sqlite3` | Database (SQLite) | **1.03 MB** | — | Replace with RDS |
| `schema_registry.json` | AI schema cache | **10.6 KB** | — | Grows slowly |
| `models/` | ML model weights | **0 MB** | 0 files | Not yet trained — will grow to 50–200 MB |

> **Evidence:** All sizes measured via PowerShell `Get-ChildItem -Recurse -File | Measure-Object -Property Length -Sum`.

### 5.2 MEDIA_ROOT / MEDIA_URL — Critical Gap

`settings.py` does **not** define `MEDIA_ROOT` or `MEDIA_URL`. Dataset files uploaded via `FileField(upload_to='datasets/')` are currently stored relative to the working directory. This is a **deployment blocker** that must be fixed before going live.

### 5.3 Storage Architecture Recommendation

```
┌─────────────────────────────────────────────────────────────┐
│                   RECOMMENDED ARCHITECTURE                    │
│                                                             │
│  EC2 Instance (app server)                                  │
│  ├── /app/staticfiles/     → served by whitenoise (EBS)    │
│  └── (no media files here)                                  │
│                                                             │
│  Amazon S3 Bucket (afridata-media)                          │
│  ├── datasets/             → all uploaded dataset files     │
│  ├── profile_pics/         → user avatars                   │
│  ├── processed/            → standardiser outputs           │
│  ├── exports/              → user downloads                 │
│  └── models/               → ML model weights (.joblib)     │
└─────────────────────────────────────────────────────────────┘
```

**Why S3:**
- `model_store.py` already has a complete S3 backend implemented (lines 117–204) — just needs `MODEL_STORE_BACKEND=s3` setting
- Dataset files can be 1.5 GB+ per file (token cost table goes to 1.5 GB)
- S3 provides unlimited scale, 99.999999999% durability, and direct download URLs

**For tomorrow's demo:** Use local EBS storage initially (fastest to deploy). S3 migration = ~2 hours of additional work.

---

## SECTION 6 — DATASET STORAGE ANALYSIS

### 6.1 Upload Mechanism

**Evidence:** `dataset/views.py` lines 497–575 — `upload_dataset()` view:
- `DatasetUploadForm` with `request.FILES`
- Standard Django `FileField` with `upload_to='datasets/'`
- No chunked upload / resumable upload (limitation for very large files)
- File size tracked in `Dataset.file_size_mb`
- Token cost automatically calculated from file size at save

### 6.2 Download Mechanism

**Evidence:** `dataset/views.py` lines 482–493 — `serve_file()`:
```python
def serve_file(dataset):
    dataset.file.seek(0)
    response = HttpResponse(dataset.file.read(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{dataset.file.name}"'
    return response
```
> ⚠️ **CRITICAL ISSUE:** The entire file is read into memory and served through Django/Gunicorn. For large files (100 MB+) this will exhaust RAM and timeout. **Must use X-Accel-Redirect (Nginx) or S3 pre-signed URLs for production.**

### 6.3 Supported File Formats

Evidence from `Dataset.DATASET_TYPES` (models.py lines 11–21):
`csv`, `excel`, `pdf`, `txt`, `json`, `xml`, `zip`, `yaml`, `parquet`

### 6.4 File Size Limits

From token cost table (models.py lines 79–94): System references files up to **1.5 GB** (1536 MB tier). Django's default `DATA_UPLOAD_MAX_MEMORY_SIZE` is 2.5 MB — **this must be raised** for dataset uploads to work.

### 6.5 Growth Projections

| Scenario | Year 1 Storage |
|---|---|
| Demo (10–50 datasets) | 1–5 GB |
| Small production (100–500 datasets) | 10–50 GB |
| Growth (1,000+ datasets) | 100+ GB |

**Recommendation:** S3 for all user-uploaded content. EBS only for OS + app code.

---

## SECTION 7 — DEPENDENCY ANALYSIS

### 7.1 Complete Python Package Inventory

```
# Core Django Stack
Django==3.2.25              # ⚠️ EOL — upgrade to 4.2 LTS post-launch
asgiref==3.7.2
djangorestframework==3.15.1
django-cors-headers==4.1.0
django-environ==0.11.2
django-extensions==3.2.3
django-filter==23.5
django-schema-graph==2.2.1
dj-database-url==0.5.0
whitenoise==6.5.0
gunicorn                    # ✅ production WSGI server

# Database
mysqlclient==2.1.1          # ✅ C extension for MySQL — needs libmysqlclient
PyMySQL==1.1.1              # Pure Python fallback

# Data Processing
pandas==3.0.1               # ✅
numpy>=2.4.3                # ✅
polars==1.7.1               # ✅ used in pipeline.py
scipy>=1.11.0               # ✅ used in content-based engine
pyarrow>=15.0.0             # ✅ parquet support

# AI / ML
google-generativeai==0.8.6  # ✅ Gemini API
google-api-core==2.15.0
tenacity==9.1.4             # retry logic
# scikit-learn — NOT IN requirements.txt! Used in semantic_classifier.py 🚨
# joblib — NOT IN requirements.txt! Used in model_store.py 🚨
# implicit — NOT IN requirements.txt! Used for ALS collaborative filtering 🚨

# File Format Handling
openpyxl==3.1.5             # Excel .xlsx
lxml==6.0.3                 # XML parsing
pyyaml==6.0.3               # YAML
Pillow==9.5.0               # Image handling (profile pics)

# Utilities
python-dotenv==1.2.2
python-dateutil>=2.8.2
requests==2.31.0
certifi==2025.7.14
urllib3==2.0.7
pytz==2025.2
six==1.17.0
```

### 7.2 🚨 Missing Dependencies from requirements.txt

The following packages are **imported in the codebase but absent from requirements.txt**:

| Package | Used In | Severity |
|---|---|---|
| `scikit-learn` | `semantic_classifier.py` lines 615–630 | 🔴 **CRITICAL** — will crash |
| `joblib` | `model_store.py` lines 24, 101–113 | 🔴 **CRITICAL** — will crash |
| `implicit` | `collaborative.py` line 36 (ALS support) | 🟡 Medium — ALS training only |
| `boto3` | `model_store.py` line 132 (S3 backend) | 🟡 Medium — only for S3 backend |
| `httpx` | `llm_generator.py` line 542 (Ollama backend) | 🟢 Low — only for Ollama |

**These MUST be added to requirements.txt before Docker build.**

### 7.3 System / Linux Packages

From Dockerfile (lines 8–13):
```bash
apt-get install -y gcc g++ default-libmysqlclient-dev build-essential
```
This is sufficient for `mysqlclient` compilation. No additional system packages needed.

### 7.4 External Services Required

| Service | Required For | Required at Runtime? |
|---|---|---|
| Google Gemini API | Metadata inference, schema generation | ✅ Yes |
| MySQL / RDS | Primary database | ✅ Yes |
| M-Pesa API (Safaricom) | Mobile payments | Optional for demo |
| Stripe | Premium dataset payments | Optional for demo |
| S3 | ML model storage, media files | Optional (EBS works for demo) |

---

## SECTION 8 — PERFORMANCE ANALYSIS

### 8.1 Background Processing Architecture

**Evidence:** `dataset/views.py` lines 521–531:
```python
threading.Thread(
    target=_run_pipeline_task_with_db_cleanup,
    kwargs={...},
    daemon=True
).start()
```

The metadata AI pipeline runs in a **raw Python daemon thread** (not Celery, not RQ, not background worker). This means:
- Pipeline runs **in the same process as the web server**
- If Gunicorn restarts, the thread dies mid-pipeline
- No retry logic, no queue, no monitoring
- Acceptable for demo; **must be replaced with Celery for production**

### 8.2 Sizing Estimates

#### A. Demo Deployment (Tomorrow's Presentation)

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 2 vCPU | 2 vCPU |
| RAM | 2 GB | **4 GB** |
| Storage (EBS) | 20 GB | 30 GB |
| Bandwidth | 1 Gbps | 1 Gbps |
| EC2 type | t3.small | **t3.medium** |
| Cost/month | ~$16 | ~$33 |

RAM breakdown for demo: Django+Gunicorn (~300 MB) + ContentBasedEngine (~100 MB) + CollaborativeEngine (~100 MB) + SemanticClassifier (~5 MB) + OS (~500 MB) + Buffer = **~1.1 GB minimum**, 4 GB for safety.

#### B. Small Production Deployment (50–500 users/day)

| Resource | Recommended |
|---|---|
| EC2 | t3.large (2 vCPU, 8 GB RAM) |
| RDS | db.t3.small MySQL 8.0 |
| Storage | S3 (unlimited) + 50 GB EBS |
| Load balancer | Application Load Balancer |
| Cost/month | ~$100–150 |

#### C. Large-Scale Deployment (5,000+ users/day)

| Resource | Recommended |
|---|---|
| EC2 (app) | 3× c5.xlarge (4 vCPU, 8 GB RAM) |
| RDS | db.r5.large Multi-AZ MySQL 8.0 |
| Storage | S3 + CloudFront CDN |
| Background | Celery workers on separate EC2 |
| Cache | ElastiCache Redis |
| Cost/month | ~$500–800 |

---

## SECTION 9 — AWS DEPLOYMENT OPTIONS COMPARISON

### Option A: Single EC2 Deployment

```
EC2 (t3.medium) ← code + sqlite → local filesystem
```

| Attribute | Value |
|---|---|
| Complexity | ⭐ Very Low |
| Cost | ~$33/month |
| Deployment Speed | ⚡ Fastest (30–60 min) |
| Scalability | ❌ Single point of failure |
| Suitability for tomorrow | ✅✅ **Best for demo** |
| Database | SQLite (OK for demo, bad for prod) |

---

### Option B: EC2 + RDS + S3 ⭐ RECOMMENDED FOR TOMORROW

```
EC2 (t3.medium) → RDS MySQL 8.0 (db.t3.micro)
                → S3 bucket (media files)
```

| Attribute | Value |
|---|---|
| Complexity | ⭐⭐ Low-Medium |
| Cost | ~$50–60/month |
| Deployment Speed | ⚡⚡ 60–90 minutes |
| Scalability | ✅ Good |
| Suitability for tomorrow | ✅✅✅ **Best balance** |
| Notes | Proper database, real storage, future-ready |

---

### Option C: Docker on EC2

```
EC2 (t3.medium) → Docker container → SQLite or external DB
```

| Attribute | Value |
|---|---|
| Complexity | ⭐⭐ Low-Medium |
| Cost | ~$33/month |
| Deployment Speed | ⚡⚡ 45–75 minutes |
| Scalability | ⭐⭐⭐ Good (Dockerfile exists) |
| Suitability for tomorrow | ✅✅ Good — Dockerfile already written |
| Notes | `docker-compose.yml` uses MySQL 5.7, needs env var wiring |

---

### Option D: ECS (Elastic Container Service)

```
ECS Fargate → RDS → S3
```

| Attribute | Value |
|---|---|
| Complexity | ⭐⭐⭐⭐ High |
| Cost | ~$80–120/month |
| Deployment Speed | 🐢 3–6 hours |
| Scalability | ✅✅ Excellent |
| Suitability for tomorrow | ❌ Too slow |

---

### Option E: EKS (Elastic Kubernetes Service)

| Attribute | Value |
|---|---|
| Complexity | ⭐⭐⭐⭐⭐ Very High |
| Cost | ~$200+/month |
| Deployment Speed | 🐢🐢 8–24 hours |
| Scalability | ✅✅✅ Enterprise |
| Suitability for tomorrow | ❌ Absolutely not |

### Ranking for Tomorrow

1. 🥇 **Option B** — EC2 + RDS + S3 (best functionality vs speed)
2. 🥈 **Option C** — Docker on EC2 (if RDS setup takes too long)
3. 🥉 **Option A** — Single EC2 + SQLite (last resort; only if time collapses)
4. ❌ Options D and E — not viable for tomorrow

---

## SECTION 10 — CI/CD ANALYSIS

### 10.1 Existing CI/CD

**Evidence:** `.github/workflows/docker-build.yml`:
- Triggers on push to `main`
- Logs into DockerHub, builds and pushes `afridata:latest`
- Docker Buildx with layer caching enabled

**Gaps:** No deployment step — only builds and pushes the image. Nothing deploys to AWS.

### 10.2 Required Secrets

```
GitHub Secrets needed:
  DOCKERHUB_USERNAME        (already referenced)
  DOCKERHUB_TOKEN           (already referenced)
  AWS_ACCESS_KEY_ID         (new — for EC2/ECS deployment)
  AWS_SECRET_ACCESS_KEY     (new)
  EC2_HOST                  (new — EC2 public IP/DNS)
  EC2_SSH_KEY               (new — private key for SSH)
  DJANGO_SECRET_KEY         (new)
  GEMINI_API_KEY            (new)
  DB_HOST / DB_USER / DB_PASSWORD / DB_NAME (new)
```

### 10.3 Recommended CI/CD Architecture

```yaml
# Recommended GitHub Actions pipeline:
1. Run tests (pytest)             → push to any branch
2. Build Docker image             → push to main
3. Push to DockerHub / ECR        → push to main
4. SSH into EC2, pull new image   → push to main (via appleboy/ssh-action)
5. Run migrations                 → after deploy
6. Restart gunicorn               → after migrations
```

### 10.4 Required Environment Variables for Production

```bash
# Django core
SECRET_KEY=<strong random key>
DEBUG=False
ALLOWED_HOSTS=<EC2-public-dns>,<custom-domain>

# Database (RDS)
DATABASE_URL=mysql://afriuser:<password>@<rds-endpoint>:3306/afridata

# AI Features
GEMINI_API_KEY=<your-gemini-key>
LLM_BACKEND=gemini
LLM_MODEL=gemini-2.5-flash

# Storage (if using S3)
MODEL_STORE_BACKEND=s3
MODEL_STORE_S3_BUCKET=afridata-models
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_S3_REGION_NAME=us-east-1

# M-Pesa (optional for demo)
MPESA_CALLBACK_URL=https://<domain>/mpesa/callback/
```

---

## SECTION 11 — RISK ANALYSIS

### 🔴 CRITICAL Blockers (will prevent deployment)

| # | Risk | Evidence | Fix |
|---|---|---|---|
| 1 | `MEDIA_ROOT` / `MEDIA_URL` not set | settings.py — absent | Add to settings.py + configure upload path |
| 2 | `scikit-learn` missing from requirements.txt | semantic_classifier.py line 615 | Add `scikit-learn>=1.3.0` |
| 3 | `joblib` missing from requirements.txt | model_store.py line 24 | Add `joblib>=1.3.0` |
| 4 | Files read entirely into memory for download | dataset/views.py line 487 `file.read()` | Use X-Accel-Redirect or S3 pre-signed URLs |
| 5 | `DATA_UPLOAD_MAX_MEMORY_SIZE` not set | settings.py — absent | Set to 500 MB+ for large datasets |
| 6 | SQLite in production | settings.py lines 132–138 | Switch to RDS MySQL |

### 🟡 High Severity (degrade functionality)

| # | Risk | Evidence | Fix |
|---|---|---|---|
| 7 | `ContentBasedEngine` loaded on every request | dataset/views.py lines 234–236 | Load once at app startup in `AppConfig.ready()` |
| 8 | Metadata pipeline runs in daemon thread | dataset/views.py line 521 | OK for demo; replace with Celery for production |
| 9 | Django 3.2 EOL (April 2024) | requirements.txt line 7 | Upgrade to Django 4.2 LTS post-launch |
| 10 | M-Pesa callback URL hardcoded to ngrok | .env.example line 34 | Update to real domain before launch |
| 11 | `DEBUG=True` default | settings.py line 29 | Set `DEBUG=False` in production env |
| 12 | `CORS_ALLOWED_ORIGINS` not configured | settings.py — absent | Add `CORS_ALLOWED_ORIGINS` list |

### 🟢 Low Severity (technical debt)

| # | Risk | Evidence |
|---|---|---|
| 13 | No rate limiting on API endpoints | settings.py — absent |
| 14 | No Celery / task queue for async work | threading.Thread used |
| 15 | JWT authentication removed but DRF configured | settings.py line 228 comment |
| 16 | `implicit` package missing (ALS training) | requirements.txt — absent |
| 17 | docker-compose uses `runserver` not gunicorn | docker-compose.yml line 19 |
| 18 | `CORS_ALLOW_ALL_ORIGINS` may be needed | not configured anywhere |

---

## SECTION 12 — FINAL RECOMMENDATION

### Pre-Deployment Fixes (Do These First — ~30 Minutes)

**1. Fix requirements.txt — Add missing packages:**
```txt
scikit-learn>=1.3.0
joblib>=1.3.0
boto3>=1.26.0
implicit>=0.7.0
```

**2. Add production settings to settings.py:**
```python
# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# File upload limits
DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000   # 500 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 524288000   # 500 MB

# Security
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000

# CORS
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
```

**3. Add URL patterns for media files in development (`afridata/urls.py`):**
```python
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## DEPLOYMENT PLAN FOR TOMORROW

### Overview

**Strategy: Option B — EC2 t3.medium + RDS MySQL 8.0 + EBS + Docker**

- **Total estimated time:** 90–120 minutes
- **Estimated monthly cost:** ~$55–65
- **GPU required:** ❌ No
- **All major features:** ✅ Will work (Gemini, metadata inference, recommendations, dataset upload/download, community forum, M-Pesa stub, admin)

---

### PHASE 0: Pre-Flight Code Fixes (30 minutes, do this NOW locally)

**Step 1 — Fix requirements.txt:**
```bash
# Add to requirements.txt:
echo "scikit-learn>=1.3.0" >> requirements.txt
echo "joblib>=1.3.0" >> requirements.txt
echo "boto3>=1.26.0" >> requirements.txt
```

**Step 2 — Fix settings.py (add MEDIA_ROOT, file size limits):**
```python
# In afridata/settings.py, add after STATIC_ROOT:
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000
FILE_UPLOAD_MAX_MEMORY_SIZE = 524288000
```

**Step 3 — Fix afridata/urls.py (serve media in dev/prod):**
```python
from django.conf import settings
from django.conf.urls.static import static
# At end of urlpatterns list:
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Step 4 — Fix entrypoint.sh (use production Gunicorn workers):**
```bash
exec gunicorn afridata.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --timeout 120 \
  --worker-class sync
```

**Step 5 — Test locally:**
```bash
pip install scikit-learn joblib boto3
python manage.py check --deploy
```

**Step 6 — Commit and push:**
```bash
git add requirements.txt afridata/settings.py afridata/urls.py entrypoint.sh
git commit -m "fix: production readiness — MEDIA_ROOT, missing deps, file size limits"
git push origin main
```

---

### PHASE 1: AWS Infrastructure Setup (20 minutes)

**Step 7 — Create EC2 Instance:**
```
Service: EC2
AMI: Ubuntu Server 22.04 LTS (ami-0c55b159cbfafe1f0 or latest)
Instance type: t3.medium (2 vCPU, 4 GB RAM)
Storage: 30 GB gp3 SSD
Security Group rules:
  - SSH (22) — your IP only
  - HTTP (80) — 0.0.0.0/0
  - HTTPS (443) — 0.0.0.0/0
  - Custom TCP (8000) — 0.0.0.0/0 (temporary for testing)
Key pair: Create/download .pem file
```

**Step 8 — Create RDS Instance:**
```
Service: RDS → Create Database
Engine: MySQL 8.0
Template: Free Tier (or Dev/Test)
DB instance: db.t3.micro
Storage: 20 GB gp2
DB name: afridata
Master username: afriuser
Master password: <strong password>
VPC: Same VPC as EC2
Public access: Yes (for now, restrict later)
Security group: Allow port 3306 from EC2 security group
```

**Step 9 — Note the RDS endpoint** (will look like `afridata.xxxxx.us-east-1.rds.amazonaws.com`)

---

### PHASE 2: Server Configuration (20 minutes)

**Step 10 — SSH into EC2 and install Docker:**
```bash
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
newgrp docker

# Verify
docker --version
```

**Step 11 — Create production .env file on server:**
```bash
cat > /home/ubuntu/.env << 'EOF'
SECRET_KEY=<generate-with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DEBUG=False
ALLOWED_HOSTS=<EC2-PUBLIC-IP>,<EC2-PUBLIC-DNS>

# RDS
DATABASE_URL=mysql://afriuser:<password>@<rds-endpoint>:3306/afridata

# AI Features  
GEMINI_API_KEY=<your-gemini-api-key>
LLM_BACKEND=gemini
LLM_MODEL=gemini-2.5-flash
LLM_MAX_TOKENS=4096

# M-Pesa (use public EC2 URL)
MPESA_CALLBACK_URL=http://<EC2-PUBLIC-IP>/mpesa/callback/
EOF
```

---

### PHASE 3: Build and Deploy (20 minutes)

**Step 12 — Pull and run the Docker image:**
```bash
# Either pull from DockerHub (if CI built it):
docker pull <dockerhub-username>/afridata:latest

# OR clone and build directly on EC2:
git clone https://github.com/<your-username>/afridata.git /home/ubuntu/afridata
cd /home/ubuntu/afridata
docker build -t afridata:latest .
```

**Step 13 — Run the container:**
```bash
docker run -d \
  --name afridata \
  --restart always \
  -p 80:8000 \
  --env-file /home/ubuntu/.env \
  -e RENDER=true \
  -v /home/ubuntu/media:/app/media \
  -v /home/ubuntu/staticfiles:/app/staticfiles \
  afridata:latest
```

> Note: `-e RENDER=true` triggers the `dj_database_url.parse(DATABASE_URL)` branch in settings.py. This reuses the existing production DB logic without code changes.

**Step 14 — Run database migrations:**
```bash
docker exec afridata python manage.py migrate
docker exec afridata python manage.py collectstatic --noinput
```

**Step 15 — Create admin user:**
```bash
docker exec -it afridata python create_admin.py
```

---

### PHASE 4: Verification (10 minutes)

**Step 16 — Verify the application:**
```bash
# Check container is running
docker ps

# Check logs
docker logs afridata --tail=50

# Test health
curl http://<EC2-PUBLIC-IP>/home/
curl http://<EC2-PUBLIC-IP>/admin/
curl http://<EC2-PUBLIC-IP>/api/

# Test dataset upload (manual)
# Test metadata pipeline trigger (upload a CSV)
# Test recommendation API
# Test community forum
```

**Step 17 — Test AI features specifically:**
```bash
# Test metadata pipeline (upload a CSV via the UI)
# Verify pipeline runs: check logs
docker logs afridata --tail=100 | grep "LLMGenerator"
docker logs afridata --tail=100 | grep "SemanticClassifier"
```

---

### PHASE 5: CI/CD Setup (20 minutes, do after the presentation)

**Step 18 — Update GitHub Actions to deploy on push:**

Add to `.github/workflows/docker-build.yml`:
```yaml
      - name: Deploy to EC2
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ubuntu
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            docker pull ${{ secrets.DOCKERHUB_USERNAME }}/afridata:latest
            docker stop afridata || true
            docker rm afridata || true
            docker run -d \
              --name afridata \
              --restart always \
              -p 80:8000 \
              --env-file /home/ubuntu/.env \
              -e RENDER=true \
              -v /home/ubuntu/media:/app/media \
              afridata:latest
            docker exec afridata python manage.py migrate --noinput
```

**Add GitHub Secrets:**
```
EC2_HOST = <EC2 public IP>
EC2_SSH_KEY = <contents of .pem file>
DOCKERHUB_USERNAME = <your username>
DOCKERHUB_TOKEN = <your token>
```

---

### Cost Summary

| Service | Type | Monthly Cost |
|---|---|---|
| EC2 t3.medium | ~730 hours | ~$33 |
| RDS db.t3.micro MySQL | ~730 hours | ~$15 |
| EBS 30 GB gp3 | storage | ~$2.40 |
| Data transfer | 10 GB out | ~$0.90 |
| **Total** | | **~$51/month** |

> First 12 months on new AWS account: EC2 t3.micro and RDS db.t3.micro are **free tier eligible** — demo could cost **$0** if within free tier limits.

---

### Deployment Timeline Summary

```
T+0:00  Phase 0 — Fix code (requirements.txt, settings.py, urls.py)
T+0:30  Phase 1 — Launch EC2 + RDS in AWS Console
T+0:50  Phase 2 — SSH, install Docker, create .env
T+1:10  Phase 3 — Build/pull Docker, run container, migrate DB
T+1:30  Phase 4 — Verify all features working
T+1:45  Phase 5 — Set up CI/CD (optional before presentation)
T+2:00  🎉 Application LIVE
```

---

### What Will Work at Launch

| Feature | Status |
|---|---|
| Dataset upload (CSV, Excel, etc.) | ✅ After MEDIA_ROOT fix |
| Dataset download (token economy) | ✅ |
| Dataset preview + Chart.js visualisation | ✅ |
| AI metadata inference (Gemini Flash) | ✅ Requires valid GEMINI_API_KEY |
| Semantic column classification (sklearn) | ✅ After adding scikit-learn to requirements |
| Content-based recommendations (TF-IDF) | ✅ (warm-up on first request) |
| Collaborative filtering recommendations | ⚠️ Needs training run (`python manage.py train_collaborative`) |
| Data standardisation pipeline | ✅ |
| Community forum | ✅ |
| User registration / login | ✅ |
| Admin dashboard | ✅ |
| M-Pesa integration | ⚠️ Needs real MPESA credentials + HTTPS |
| REST API | ✅ |

---

*Report generated by automated codebase analysis. All file paths, line numbers, and measurements are cited from direct inspection of the repository.*
