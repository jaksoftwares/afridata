# AfriData Containerization & Hosting Guide

This document outlines the containerization strategy and CI/CD pipeline set up for the AfriData application. It serves as a comprehensive guide for the hosting and DevOps teams to seamlessly deploy and maintain the platform.

## Application Architecture

AfriData is a robust Django web application, designed for containerized deployment using standard Docker best practices.

- **Web Server:** Gunicorn (serving the Django WSGI application)
- **Static File Serving:** WhiteNoise
- **Database:** 
  - **Production:** MySQL 5.7+ (connected via `DATABASE_URL`)
  - **Development:** SQLite (default fallback)

## Docker Configuration

The application is fully containerized with a production-ready `Dockerfile`.

### Exposed Ports
- **`8000` (TCP)**: The primary port exposed by the Django/Gunicorn container. Your load balancer or reverse proxy (e.g., NGINX, AWS ALB) should route HTTP traffic to this port.

### Health & Start-Up
The container uses an `entrypoint.sh` script to ensure clean startups:
1. **Database Wait:** Uses `nc` to wait for the database host/port to become available before starting.
2. **Migrations:** Automatically runs `python manage.py migrate` to apply any pending database changes.
3. **Static Assets:** Automatically runs `python manage.py collectstatic --noinput` to prepare static assets.
4. *(Optional)* **Superuser Creation:** Automatically provisions a superuser if `DJANGO_SUPERUSER_USERNAME` and related variables are provided.
5. **Server Launch:** Starts the application using Gunicorn.

---

## Environment Variables

The application relies on several critical environment variables. An exhaustive list of supported variables can be found in `.env.example`.

### Required for Production Deployment

| Variable | Description | Example |
| :--- | :--- | :--- |
| `SECRET_KEY` | Cryptographic key for Django. Must be kept secret. | `your_long_random_string` |
| `DEBUG` | Should be explicitly set to `False` in production. | `False` |
| `ALLOWED_HOSTS` | Comma-separated list of hostnames. | `yourdomain.com,www.yourdomain.com` |
| `DATABASE_URL` | The connection string to your MySQL database. | `mysql://user:password@db:3306/afridata` |

*Note: For the `entrypoint.sh` script to properly wait for the database, ensure `DB_HOST` and `DB_PORT` are also set to match the host and port in the `DATABASE_URL`.*

---

## Running the Application

### 1. Local Development / Staging via Docker Compose

A `docker-compose.yml` file is provided for isolated local development and testing. It spins up both the Django web application and an isolated MySQL container.

```bash
# Build the containers and start the application in detached mode
docker-compose up --build -d

# View logs
docker-compose logs -f web

# Bring down the application
docker-compose down
```
Access the application at `http://localhost:8000`.

### 2. Production Deployment

In a cloud environment (e.g., AWS ECS, DigitalOcean App Platform, Render), configure your service to pull the Docker image and inject the required environment variables.

1. **Pull Image:** The CI/CD pipeline pushes the latest image to your registry.
2. **Environment Configuration:** Inject `DATABASE_URL`, `SECRET_KEY`, `ALLOWED_HOSTS`, etc.
3. **Networking:** Map container port `8000` to your platform's public-facing port (usually 80/443).

---

## CI/CD Pipeline Setup

The project includes an automated GitHub Actions pipeline located at `.github/workflows/docker-build.yml`.

### Workflow Logic
1. **Trigger:** Fires on any `push` to the `main` branch.
2. **Build:** Uses Docker Buildx with layer caching for significantly faster subsequent builds.
3. **Registry Authentication:** Authenticates against Docker Hub.
4. **Push:** Pushes the built image tagged as `latest` directly to your container registry.

### Required GitHub Secrets
To ensure the pipeline operates successfully, the repository administrator must configure the following standard GitHub Repository Secrets:

- `DOCKERHUB_USERNAME`: The username for the target Docker Hub account.
- `DOCKERHUB_TOKEN`: An access token (with push rights) for the target Docker Hub account.

*(If you choose to use an alternative registry like AWS ECR or GitHub Container Registry, the `login-action` and image tagging steps in `.github/workflows/docker-build.yml` should be modified accordingly).*
