# Deploy Lexora on AWS EC2 with Docker

This guide deploys the full stack on **one EC2 instance** using Docker Compose:

| Container | Role |
|-----------|------|
| `nginx` | Public HTTP on port 80 (static, media, Django, `/ai` → FastAPI) |
| `web` | Django + Gunicorn |
| `chatbot` | FastAPI (search + AI chat) |
| `worker` | Celery worker (emails, embeddings, deletes) |
| `beat` | Celery beat (daily analytics digest) |
| `redis` | Celery broker |
| `db` | Postgres |

---

## Part A — On your laptop (once)

### 1. Push the project to GitHub

```powershell
git add Dockerfile docker-compose.yml docker nginx .env.example DEPLOY_AWS.md
git add Enterprise_Legal_AI_Case_Management_Platform/settings.py ...
# commit when ready, then:
git push -u origin main
```

Do **not** commit `.env` (real secrets).

### 2. Know your API keys

You will paste these into `.env` on the server:

- `GROQ_API_KEY`
- `COHERE_API_KEY`
- `pinecone_Api_key` (+ index name / region)
- Gmail SMTP app password (if you want OTP / digest emails)

---

## Part B — Create the EC2 instance

### 1. Launch instance

1. AWS Console → **EC2** → **Launch instance**
2. Name: `lexora`
3. AMI: **Ubuntu Server 22.04 or 24.04 LTS**
4. Instance type: **`t3.small`** (minimum) or **`t3.medium`** (better for AI + Celery)
5. Key pair: create/download a `.pem` (needed for SSH)
6. Storage: **20 GB** gp3 is fine

### 2. Security group (firewall)

Inbound rules:

| Type | Port | Source | Why |
|------|------|--------|-----|
| SSH | 22 | My IP | Admin access |
| HTTP | 80 | 0.0.0.0/0 | Website |
| HTTPS | 443 | 0.0.0.0/0 | Optional later (SSL) |

Do **not** open 8000 or 8001 to the world.

### 3. Elastic IP (recommended)

EC2 → Elastic IPs → Allocate → Associate to your instance.  
Use that IP in `DJANGO_ALLOWED_HOSTS` and browser URL.

---

## Part C — Install Docker on EC2

SSH in (replace path and IP):

```bash
chmod 400 ~/Downloads/your-key.pem
ssh -i ~/Downloads/your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

Then on the server:

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker ubuntu
```

Log out and SSH back in so the `docker` group applies:

```bash
exit
ssh -i ~/Downloads/your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
docker --version
docker compose version
```

---

## Part D — Clone and configure

```bash
cd ~
git clone https://github.com/YOUR_USER/YOUR_REPO.git lexora
cd lexora
# If the repo root already IS the Django project, stay here.
# If there is a nested folder, cd into it until you see manage.py + docker-compose.yml

cp .env.example .env
nano .env
```

### Fill `.env` (important values)

```env
DJANGO_SECRET_KEY=paste-a-long-random-string-here
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=YOUR_EC2_PUBLIC_IP
CSRF_TRUSTED_ORIGINS=http://YOUR_EC2_PUBLIC_IP
CORS_ALLOWED_ORIGINS=http://YOUR_EC2_PUBLIC_IP

POSTGRES_DB=lexora
POSTGRES_USER=lexora
POSTGRES_PASSWORD=strong-password-here

# Docker/nginx serves chat+search under /ai (do not use localhost:8001 on AWS)
CHATBOT_API_BASE_URL=/ai

GROQ_API_KEY=...
COHERE_API_KEY=...
pinecone_Api_key=...
PINECONE_INDEX_NAME=documents
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
DEFAULT_FROM_EMAIL=...
ANALYTICS_DIGEST_ENABLED=true
ANALYTICS_DIGEST_EMAIL=...
```

Notes:

- You can leave `REDIS_URL` as localhost in `.env`; **docker-compose overrides it** to `redis://redis:6379/0`.
- `POSTGRES_HOST` is set by compose to `db` — you do not need to set it in `.env`.

Generate a secret key if you want:

```bash
openssl rand -hex 32
```

---

## Part E — Build and start

```bash
cd ~/lexora   # folder that contains docker-compose.yml
docker compose up -d --build
```

First build takes several minutes (Python deps + LangChain/etc.).

Check status:

```bash
docker compose ps
docker compose logs -f web
# Ctrl+C to stop following logs
```

Healthy look: `web`, `chatbot`, `worker`, `beat`, `nginx`, `db`, `redis` all **Up**.

Create an admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

---

## Part F — Open the site

Browser:

```
http://YOUR_EC2_PUBLIC_IP/
```

Quick checks:

| Check | URL / action |
|-------|----------------|
| Landing | `http://IP/` |
| Register / login | `/register/` `/login/` |
| Chatbot health via nginx | `http://IP/ai/health` → `{"status":"ok"}` |
| Upload a PDF on a case | Wait for worker to embed |
| Search / AI chat | Should work after indexing |

---

## Useful commands

```bash
# Restart everything
docker compose restart

# Stop
docker compose down

# Stop and wipe DB/media volumes (destructive)
docker compose down -v

# Rebuild after code pull
git pull
docker compose up -d --build

# Logs
docker compose logs -f worker
docker compose logs -f chatbot

# Shell inside web container
docker compose exec web bash
```

---

## Optional: HTTPS with a domain

1. Point a domain A-record to your Elastic IP.
2. Update `.env`:

   ```env
   DJANGO_ALLOWED_HOSTS=your.domain.com,YOUR_EC2_PUBLIC_IP
   CSRF_TRUSTED_ORIGINS=https://your.domain.com
   CORS_ALLOWED_ORIGINS=https://your.domain.com
   ```

3. Install Certbot on the host **or** add an nginx SSL container later.
4. Restart: `docker compose up -d`

(You can also put CloudFront / an ALB in front later; not required for a portfolio demo.)

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `csrf` / 403 on login | Set `CSRF_TRUSTED_ORIGINS=http://YOUR_IP` exactly (with `http://`) |
| DisallowedHost | Add IP/domain to `DJANGO_ALLOWED_HOSTS`, recreate web: `docker compose up -d web` |
| Chat/search fail | Open `http://IP/ai/health`; check `CHATBOT_API_BASE_URL=/ai` |
| Upload never searchable | `docker compose logs worker` — need Cohere/Pinecone keys |
| Out of memory | Use `t3.medium`; reduce gunicorn/celery workers |
| Port 80 refused | Security group missing HTTP; or nginx not up (`docker compose ps`) |
| entrypoint `/bin/sh^M` | Line endings — ensure `docker/entrypoint.sh` is LF (repo has `.gitattributes`) |

---

## Cost tip

Stop the instance when not demoing:

EC2 → Instance → **Stop** (not Terminate).  
Start again when needed; Elastic IP stays associated if allocated.
