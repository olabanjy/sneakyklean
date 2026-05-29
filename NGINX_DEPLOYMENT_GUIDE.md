# Nginx Deployment Guide

This guide shows how to run **Nginx directly on the server** as the public entrypoint for Sneaky Klean, while the Django app runs in Docker on the same machine.

The setup looks like this:

- Internet traffic hits Nginx on ports `80` and `443`
- Nginx reverse proxies requests to Docker on `127.0.0.1:${HOST_WEB_PORT}`
- Django serves the app through Gunicorn
- Postgres and Redis stay internal to Docker

## 1. Prerequisites

Before you start, make sure you have:

- A Linux server, ideally Ubuntu 22.04 or 24.04
- A domain name pointed to the server IP
- Docker and Docker Compose installed
- Root or `sudo` access on the server

## 2. Update the App Environment

Create your production env file on the server:

```bash
cp .env.production.example .env.production
```

Set these values carefully:

- `ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com,www.your-domain.com`
- `CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com`
- `SECRET_KEY` to a long random value
- Database password to a strong password
- Real email and ZeptoMail credentials
- `DEFAULT_FROM_EMAIL=Sneaky Klean <noreply@arroweye.pro>` or another verified sender address

If you are using HTTPS, you should also make sure your domain is correct everywhere you expose public URLs.
If you browse the site by IP address, add that IP to `ALLOWED_HOSTS` too or Django will return `400 Bad Request`.

## 3. Start the App Stack

Build and start the deployment compose file:

```bash
docker compose --env-file .env.production -f docker-compose.deploy.yml up -d --build
```

This will start:

- `web` inside Docker on port `8000`, exposed to the host on `HOST_WEB_PORT`
- `celery` for background jobs
- `db` for Postgres
- `redis` for the Celery broker and result backend

Check that the app is reachable locally on the server:

```bash
curl http://127.0.0.1:8000/
```

If `8000` is already in use on the server, set `HOST_WEB_PORT` in `.env.production` to another free port and point Nginx to that port instead.

## 4. Install Nginx

On Ubuntu/Debian:

```bash
sudo apt update
sudo apt install nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

Open the firewall if needed:

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

## 5. Create the Nginx Site Config

Create a new site file:

```bash
sudo nano /etc/nginx/sites-available/sneakyklean
```

Use this configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable the site and reload Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/sneakyklean /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Now your app should be reachable at `http://your-domain.com`.

## 6. Add HTTPS with Let’s Encrypt

Install Certbot:

```bash
sudo apt install certbot python3-certbot-nginx
```

Request and install a certificate:

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Certbot will update the Nginx config and set up automatic renewal.

Test renewal:

```bash
sudo certbot renew --dry-run
```

## 7. Optional: Add Security Headers

After HTTPS is working, you can add headers to the Nginx server block:

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

If you add these, reload Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 8. Media Files Note

Sneaky Klean uses WhiteNoise for static files, so static assets are handled by Django in production.

If the app starts storing uploaded media files, Nginx should serve `/media/` directly. For that, you will need:

- A shared volume or host directory mounted into the Django container
- An Nginx `location /media/` block pointing to that directory

Example:

```nginx
location /media/ {
    alias /srv/sneakyklean/media/;
}
```

If you do not store user uploads, you can skip this.

## 9. Common Operations

Restart the app stack:

```bash
docker compose --env-file .env.production -f docker-compose.deploy.yml restart
```

View logs:

```bash
docker compose --env-file .env.production -f docker-compose.deploy.yml logs -f web
docker compose --env-file .env.production -f docker-compose.deploy.yml logs -f celery
```

Reload Nginx after config changes:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 10. Troubleshooting

### 502 Bad Gateway

This usually means Nginx cannot reach the Docker app.

Check:

- `web` container is running
- `127.0.0.1:8000` is listening on the server
- Nginx `proxy_pass` points to `http://127.0.0.1:8000`

### Static files not loading

Confirm the app ran `collectstatic` and that WhiteNoise is enabled in Django.

### HTTPS redirect loop

Make sure Nginx forwards `X-Forwarded-Proto` and that the certificate is valid.

### Large uploads fail

Increase `client_max_body_size` in the Nginx server block.

## 11. Recommended Deployment Flow

1. Update `.env.production`
2. Start Docker services
3. Install and configure Nginx
4. Enable HTTPS with Certbot
5. Smoke test the site
6. Monitor logs after launch
