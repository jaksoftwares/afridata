# 🌍 Afridata – African Dataset Hub

**Afridata** is a Django-based web application designed to serve as a centralized repository for datasets across Africa. It aims to promote open data access, enable collaboration, and empower individuals and institutions to share, explore, and utilize datasets across multiple domains such as education, health, governance, agriculture, environment, and development.

> **Owned and managed by JHUB Africa**

---

## 📌 Project Overview

Afridata is not just a data repository — it's a community platform that supports dataset discovery, dataset contributions, API access, and data-driven discussions. It provides a unified, structured interface for managing and accessing datasets relevant to the African continent.

### Key Objectives:
- Centralize African datasets across disciplines and sectors.
- Provide authenticated access to upload, download, and manage datasets.
- Enable open collaboration through community forums.
- Offer programmatic dataset access via a RESTful API.

---

## ⚙️ Core Features

- **Dataset Upload & Download**: Authenticated users can upload and download datasets in formats like CSV, Excel, JSON, ZIP, etc.
- **User Authentication**: Secure account registration, login, and profile management.
- **Dataset Metadata**: Datasets include structured metadata (title, description, tags, category, license).
- **Community Forum**: Engage in discussions, data requests, and feedback sharing.
- **REST API Access**: Programmatic access to public datasets.
- **Search & Filtering**: Discover datasets using keywords, categories, and tags.
- **Role Management**: Role-based permissions for Users, Moderators, and Admins.

---

## 🧱 Tech Stack

- **Backend**: Django, Django REST Framework
- **Database**: PostgreSQL (production), SQLite (development)
- **Frontend**: Django Templates (Bootstrap or Tailwind CSS)
- **Authentication**: JWT and/or Session-based login
- **Deployment Ready**: Configurable for Docker, Gunicorn + Nginx, or cloud platforms

---

## 🌍 Target Users

Afridata is built for:

- **Researchers & Academics** – Access datasets for studies or academic projects.
- **Developers & Data Scientists** – Pull and integrate clean structured data.
- **Governments & NGOs** – Publish and share public data responsibly.
- **Students & Enthusiasts** – Learn and practice using real-world African datasets.
- **Open Data Communities** – Contribute to open knowledge and collaboration.

---

## 🌐 API Overview (High-Level)

Afridata exposes a RESTful API to enable programmatic access to datasets:

| Method | Endpoint               | Description                          |
|--------|------------------------|--------------------------------------|
| GET    | `/api/datasets/`       | List all datasets                    |
| GET    | `/api/datasets/<id>/`  | Retrieve specific dataset details    |
| POST   | `/api/datasets/`       | Upload a new dataset (auth required) |
| POST   | `/api/token/`          | Obtain JWT authentication token      |
| GET    | `/api/categories/`     | List available dataset categories    |

Supports filtering, pagination, and secured access via JSON Web Tokens (JWT).

---

## ✅ Project Status

Afridata is under **active development**. Core features are complete, and the platform is open for dataset contributions and community engagement.

### Planned Enhancements:
- Dataset ratings and user reviews
- Dataset versioning and history tracking
- Notification system for dataset updates
- Webhooks and API integrations

---

## 📄 License

This project is licensed under the **MIT License**. See the `LICENSE` file for full terms.

---

## ✉️ Maintainer

**Managed by:** JHUB Africa  
**Technical Support:** Afridata Team JHUB Africa 
📍 Nairobi, Kenya  
📧 info@afridata.jhubafrica.com  
