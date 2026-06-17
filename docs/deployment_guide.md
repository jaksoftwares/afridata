# AfriData Deployment Guide

This document outlines the standard operating procedures for deploying and maintaining the AfriData application in a production or staging environment using Docker. It is intended for DevOps engineers and system administrators.

## 1. Prerequisites
- **Docker Engine** and **Docker Compose** installed on the host machine.
- Access to the application source code.
- A properly populated `.env` file provided securely.

## 2. Environment Variables (`.env`)
The application relies heavily on the environment variables to function securely. Ensure the following critical variables are set in the `.env` file at the root of the project:

- **Database Credentials**: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` (should match the db service name, e.g., `db`), `DB_PORT` (e.g., `3306`).
- **Django Core**: `SECRET_KEY`, `DEBUG` (Must be set to `False` in production), `ALLOWED_HOSTS` (Comma-separated list of your production domains/IPs).
- **Email/SMTP settings**: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`, `CONTACT_EMAIL_RECIPIENT` (e.g., `info.jhub@jkuat.ac.ke`).

> [!WARNING]  
> Never commit the `.env` file to version control. Handle it securely via a secrets manager or secure file transfer.

## 3. Deployment Steps

### Step 1: Setup Environment
Clone or transfer the repository to the host server and place the `.env` file in the root directory.
```bash
cd /path/to/afridata
# Ensure .env is present
```

### Step 2: Line Endings Verification
If the code was developed or transferred from a Windows machine, the `entrypoint.sh` script might have CRLF line endings. This will cause the container to fail with an `exec format error` or `\r command not found` in Linux.
```bash
# Convert line endings to LF to ensure Linux compatibility
dos2unix entrypoint.sh
chmod +x entrypoint.sh
```

### Step 3: Build and Run
Use Docker Compose to build the images and start the containers in detached mode.
```bash
docker-compose build
docker-compose up -d
```

### Step 4: Verify Application State
Ensure both the `web` and `db` containers are running healthily.
```bash
docker-compose ps
docker-compose logs -f web
```
*Expected Behavior:* The `entrypoint.sh` script will automatically:
1. Wait for the MySQL database to become ready using `nc`.
2. Apply all Django database migrations (`python manage.py migrate`).
3. Collect static files for WhiteNoise (`python manage.py collectstatic`).
4. Start the Gunicorn server on port `8000`.

## 4. Data Management & Persistent Volumes

> [!CAUTION]  
> By default, user-uploaded datasets and cover photos are stored inside the container at `/app/media/`. In a true production environment, you **must** map this directory to a persistent Docker volume, or ideally, configure Django (via `django-storages`) to use an external object store like AWS S3 or DigitalOcean Spaces to prevent data loss during container restarts.

Database data is automatically persisted using a Docker named volume (`mysql_data`).

## 5. Reverse Proxy & SSL Setup
The Docker container exposes the application on port `8000`. Do not expose this port directly to the public web. 

You should place a reverse proxy (such as **Nginx** or **Traefik**) in front of the application to:
1. Handle SSL/TLS termination (e.g., via Let's Encrypt).
2. Proxy web traffic from ports `80` and `443` to `http://localhost:8000`.
3. Optionally, serve large static and media files directly to reduce the load on the Python Gunicorn workers.

## 6. Common Troubleshooting

- **Database Connection Refused:** Ensure the `DB_HOST` in your `.env` matches the exact name of the database service defined in `docker-compose.yml`.
- **Request Header Fields Too Large:** If Gunicorn throws this error (often caused by large cookies or proxy headers), the `entrypoint.sh` script has already been patched to increase the limit (`--limit-request-line 8190 --limit-request-field_size 8190`).
- **Verification Emails Going to Spam:** Ensure your SMTP provider (e.g., SendGrid, Mailgun) has properly configured SPF, DKIM, and DMARC records on your domain's DNS.
