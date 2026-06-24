# AfriData Programmatic Access Module (API & CLI)

## 1. Overview

### Purpose

The AfriData Programmatic Access Module provides secure, authenticated, and controlled access to datasets through APIs and command-line tools without exposing internal infrastructure, databases, storage systems, or other users' resources.

The objective is to enable researchers, developers, data scientists, organizations, and institutions to interact with AfriData directly from scripts, terminals, notebooks, and applications while maintaining the same security guarantees provided by the web platform.

This module replaces the current mock API documentation and introduces a fully functional implementation.

---

# 2. Business Objectives

The module shall allow users to:

* Search datasets programmatically
* Retrieve dataset metadata
* Preview datasets
* Download authorized datasets
* Upload datasets
* Manage their own datasets
* Integrate AfriData into applications
* Access datasets from Python, R, Bash, Power BI, Tableau, and Jupyter notebooks

The module shall not:

* Expose server terminals
* Expose database access
* Expose storage systems
* Allow access to unauthorized datasets
* Allow execution of arbitrary commands

---

# 3. Core Principle

Users interact with AfriData resources.

Users do not interact with AfriData infrastructure.

The API acts as a controlled gateway between users and platform resources.

All requests must pass through:

Authentication → Authorization → Validation → Service Layer → Storage

---

# 4. High-Level Architecture

```
                Web Application
                       |
                       |
                REST API Layer
                       |
                Permission Layer
                       |
                Dataset Service
                       |
            Object Storage (S3/MinIO)
                       |
                 Metadata Database

                       ^
                       |
                AfriData CLI
                       |
                Python SDK
                       |
                 External Apps
```

All external clients use the same API.

No client receives privileged access.

---

# 5. Dataset Visibility Model

Each dataset shall have a visibility level.

## Public

Visible to everyone.

Examples:

* Government datasets
* Open data initiatives
* Public research datasets

Permissions:

* View metadata
* Preview
* Download

Authentication may be optional.

---

## Private

Visible only to owner.

Permissions:

* Owner only
* Platform administrators

---

## Organization

Accessible only to organization members.

Permissions:

* Organization members
* Dataset owner
* Platform administrators

---

# 6. Dataset Ownership Model

Every dataset must have:

* Dataset UUID
* Owner
* Visibility
* Created Date
* Updated Date

Example:

Dataset:
UUID: 9d7bc4cf-e3f9-4f55-b6fb
Owner: user_123
Visibility: Private

The owner becomes the primary authority.

---

# 7. Authentication

## Requirement

All non-public operations require authentication.

Supported methods:

### Browser Authentication

Used by website users.

### API Authentication

Used by applications and CLI users.

---

## API Keys

Users generate API keys from their profile.

Example:

afr_live_xxxxxxxxxxxxxxxxxxx

Each key belongs to a specific user.

The platform must never create anonymous keys.

---

## API Key Storage

Only hashed values are stored.

Never store raw keys.

Similar to password storage.

Example:

stored_value = SHA256(api_key)

---

# 8. Authorization

Authentication identifies the user.

Authorization determines what they may access.

Example:

User A requests Dataset B.

System checks:

1. Dataset visibility
2. Dataset owner
3. Organization membership
4. User permissions

If validation fails:

403 Forbidden

---

# 9. Dataset Security Rules

Every download request must pass permission checks.

Example:

GET /datasets/{uuid}/download

Process:

Step 1:
Validate API key

Step 2:
Validate dataset existence

Step 3:
Validate access permissions

Step 4:
Generate temporary download URL

Step 5:
Return download URL

Direct storage access is never exposed.

---

# 10. Signed Download URLs

Permanent URLs are prohibited.

Bad:

https://afridata.jhubafrica.com/download/123

Reason:

* Can be shared indefinitely
* Hard to revoke

Required:

Temporary signed URLs

Example:

https://storage.afridata.jhubafrica.com/...
?signature=xxxxx
&expires=300

Expiration:

5 minutes

Benefits:

* Time-limited
* Revocable
* Auditable

---

# 11. API Rate Limiting

Rate limiting prevents abuse.

Recommended defaults:

Anonymous:
100 requests/hour

Authenticated:
1,000 requests/hour

Premium:
10,000 requests/hour

Downloads:
50 downloads/hour

Limits configurable by account tier.

---

# 12. Audit Logging

Every critical operation must be logged.

Track:

* Searches
* Uploads
* Downloads
* API key usage
* Authentication events

Example:

timestamp
user_id
dataset_uuid
action
ip_address

Logs support:

* Security reviews
* Abuse detection
* Usage analytics

---

# 13. Dataset Identifiers

Sequential IDs are prohibited.

Bad:

1
2
3
4

Reason:

Enumeration attacks.

Required:

UUIDs

Example:

9d7bc4cf-e3f9-4f55-b6fb-6e2f1f9f0d7e

---

# 14. API Endpoints

## Dataset Search

GET /api/v1/datasets

Supports:

* Search
* Category
* Tags
* Country
* Visibility
* Pagination

---

## Dataset Details

GET /api/v1/datasets/{uuid}

Returns:

* Metadata
* Owner
* Tags
* Statistics

---

## Dataset Preview

GET /api/v1/datasets/{uuid}/preview

Returns limited rows.

Maximum:

100 rows

---

## Dataset Download

POST /api/v1/datasets/{uuid}/download

Returns signed URL.

---

## Dataset Upload

POST /api/v1/datasets/upload

Authentication required.

---

## User Datasets

GET /api/v1/me/datasets

Returns datasets owned by authenticated user.

---

## API Key Management

POST /api/v1/api-keys/create

DELETE /api/v1/api-keys/{id}

GET /api/v1/api-keys

---

# 15. AfriData CLI

## Purpose

Provide terminal access without exposing infrastructure.

CLI acts as a client.

CLI never bypasses API permissions.

---

## Installation

pip install afridata-cli

---

## Authentication

afridata login

Workflow:

1. User authenticates
2. API token generated
3. Token stored locally

Storage location:

Windows:
%USERPROFILE%.afridata

Linux:
~/.afridata

---

## Search

afridata search kenya

---

## Dataset Information

afridata info dataset-uuid

---

## Preview

afridata preview dataset-uuid

---

## Download

afridata pull dataset-uuid

Process:

CLI
→ API
→ Permission Check
→ Signed URL
→ Download

---

## Upload

afridata push dataset.csv

---

## My Datasets

afridata my-datasets

---

# 16. Python SDK

Future enhancement.

Example:

from afridata import Client

client = Client(api_key="xxx")

datasets = client.search("kenya")

dataset = client.get_dataset(uuid)

dataset.download()

SDK internally uses REST APIs.

---

# 17. Storage Architecture

Datasets should reside in:

* Amazon S3
* MinIO
* Azure Blob Storage
* Google Cloud Storage

Not in application servers.

Benefits:

* Scalability
* Reliability
* Signed URL support
* Reduced server load

---

# 18. Security Requirements

Mandatory:

✓ HTTPS only

✓ API key hashing

✓ Rate limiting

✓ Audit logs

✓ UUID identifiers

✓ Signed download URLs

✓ Permission checks

✓ Ownership validation

✓ Storage isolation

✓ Input validation

✓ Malware scanning during uploads

Recommended:

✓ Organization workspaces

✓ API scopes

✓ Download quotas

✓ Geographic restrictions

---

# 19. Development Phases

Phase 1

* API authentication
* Dataset search
* Dataset details
* Dataset previews
* Downloads

Phase 2

* Upload APIs
* API key management
* Usage analytics

Phase 3

* AfriData CLI
* SDK

Phase 4

* Organizations
* Dataset sharing
* Advanced permissions

---

# 20. Success Criteria

The module is considered complete when:

1. Users can access datasets securely through APIs.
2. Permissions mirror website permissions.
3. Downloads use signed URLs.
4. Dataset ownership is enforced.
5. No direct infrastructure access is possible.
6. CLI users can interact entirely through terminal commands.
7. All actions are auditable.
8. Public and private datasets remain isolated.
9. API abuse is rate-limited.
10. The system supports future SDK and enterprise integrations.
