# Deployment auf AWS

Dieser Leitfaden beschreibt, wie der Heizungscheck auf der **AWS**-Infrastruktur
bereitgestellt wird. Er übernimmt den bestehenden Docker-Stack (Backend +
Nginx) unverändert und ersetzt nur die Datenbank sowie den Bildspeicher durch
verwaltete AWS-Dienste. **Es ist keine Serverless-Umschreibung nötig.**

> Zielarchitektur: **ein EC2-Instance** für Backend + Nginx, **Amazon RDS
> PostgreSQL** für die Datenbank, **Amazon S3** für hochgeladene Bilder. Optional
> **Application Load Balancer** + **ACM-Zertifikat** für HTTPS.

---

## Architektur

```
Browser
  │ (https)
  ▼
Application Load Balancer / Nginx (HTTPS, ACM-Zertifikat)
  ▼
EC2 (EBS)  ──  Docker: Backend (uvicorn)  ──  Nginx (Reverse Proxy)
  │                                          │
  ▼                                          ▼
RDS PostgreSQL 16 (Multi-AZ optional)     Amazon S3 (Nameplate-Bilder)
```

---

## Voraussetzungen

- AWS-Konto mit ausreichenden Berechtigungen (EC2, RDS, S3, IAM, optional
  ALB/ACM/Route 53).
- Docker-Image des Backends (siehe `docker/docker-compose.yml` bzw.
  `backend/Dockerfile`) und das statische Frontend (Netlify oder S3 Static Hosting).

---

## Schritt 1 — VPC & Subnetze

Üblicherweise genügt das **Standard-VPC** für den Einstieg:

- **Public Subnet:** EC2 + ALB.
- **Private Subnet (empfohlen):** RDS (nicht aus dem Internet erreichbar).
- Falls sofort produktiv: RDS in einem privaten Subnetz anlegen und nur den
  EC2-Sicherheitsgruppen-Zugriff auf Port 5432 erlauben.

---

## Schritt 2 — S3 Bucket (Bilder & Frontend-Option)

1. Bucket anlegen, z. B. `heizungscheck-images`.
2. **Bucket-Policy:** Nur die Backend-Rolle (EC2) darf Objekte in
   `uploads/` lesen/schreiben.
3. Enabling **Versionierung** empfiehlt sich für Prüfnachweise.
4. Optional: Das **statische Frontend** über S3 + CloudFront ausliefern
   (alternativ Netlify wie aktuell).

---

## Schritt 3 — RDS PostgreSQL erstellen

1. **Amazon RDS → Create database → PostgreSQL 16**.
2. DB-Kennung, Master-User (`evh`) und Master-Passwort setzen.
3. Public access = `Nein` (nur über EC2 bzw. VPC zugänglich).
4. Sicherheitsgruppe: eingehenden Port **5432** nur von der EC2-SG erlauben.
5. **Multi-AZ** und **Automatische Backups** aktivieren (Produktion).

Notieren Sie den **Endpoint** (z. B. `heizungscheck.cluster-xxxxx.eu-central-1.rds.amazonaws.com`).

---

## Schritt 4 — EC2-Instance (Backend + Nginx)

1. **EC2 → Launch instance** (z. B. `t4g.medium` oder `t3.small` je nach
   OCR-Last; OCR braucht CPU — größere Instance für parallele Scans).
2. AMI: **Amazon Linux 2023** (oder Ubuntu 22.04).
3. **Sicherheitsgruppe:** Port 80/443 eingehend (bzw. nur vom ALB), SSH (22)
   nur für Ihre IP.
4. **IAM-Rolle** an die Instance anhängen mit Mindestberechtigungen:
   - `s3:GetObject`/`s3:PutObject` auf den Bilder-Bucket,
   - `ssm:GetParameters` (vorzugsweise AWS Secrets Manager für Credentials).

### Setup auf der Instance

```bash
# Docker installieren (Amazon Linux 2023)
sudo dnf install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user

# Repo klonen
git clone https://github.com/abhinay-sambherao/HeatScanAI.git
cd HeatScanAI/docker
```

---

## Schritt 5 — Umgebungsvariablen (Secrets verwenden)

Umgebungsvariablen **nicht** im Compose-File fest verdrahten. Laden Sie sie zur
Laufzeit, z. B. über **AWS Secrets Manager**:

```bash
export POSTGRES_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id heizungscheck/db --query SecretString --output text ...)
export JWT_SECRET_KEY=$(openssl rand -hex 32)
```

Ergänzen Sie in `docker-compose.yml`:

```yaml
backend:
  environment:
    DATABASE_URL: postgresql+asyncpg://evh:${POSTGRES_PASSWORD}@heizungscheck.cluster-xxxxx.eu-central-1.rds.amazonaws.com:5432/evh_heatscan
    DATABASE_URL_SYNC: postgresql://evh:${POSTGRES_PASSWORD}@heizungscheck.cluster-xxxxx.eu-central-1.rds.amazonaws.com:5432/evh_heatscan
    ALLOWED_ORIGINS: https://heizungscheck.example.com
    S3_BUCKET: heizungscheck-images
    OCR_TIMEOUT_SECONDS: 30
```

> **Hinweis:** In AWS starten Sie **nur** Backend + Nginx; die Datenbank ist die
> verwaltete RDS-Instanz, **nicht** der `db`-Dienst des Compose-Stacks. (Die
> lokale Compose-Datei enthält einen `db`-Service; für AWS entweder ausblenden
> oder per Profil trennen.)

---

## Schritt 6 — Starten & Migration

```bash
# Migration ausführen (gegen RDS)
docker compose run --rm backend alembic upgrade head

# EPREL-Daten (optional, sonst on-demand)
docker compose run --rm backend python -m scripts.seed_db

# Dienste starten
docker compose --profile prod up -d --build
```

---

## Schritt 7 — HTTPS

**Variante A — ALB + ACM (empfohlen):**

1. Zertifikat in **ACM** für `heizungscheck.example.com` anfordern.
2. **ALB** erstellen, Target-Group → EC2-Port 80.
3. HTTPS-Listener (443) mit dem ACM-Zertifikat → Target-Group.
4. DNS-A-Record (Route 53) auf den ALB zeigen.

**Variante B — Nginx + Let's Encrypt (einfach, ohne ALB):**

```bash
sudo dnf install -y certbot python3-certbot-nginx
sudo certbot --nginx -d heizungscheck.example.com
```

---

## Schritt 8 — S3-Anbindung im Backend

Falls Sie hochgeladene Bilder dauerhaft in S3 archivieren möchten (statt nur
flüchtig auf EBS):

- Backend-URL-Format: `https://heizungscheck-images.s3.<region>.amazonaws.com/uploads/<uuid>.jpg`.
- Die Backend-Rolle (mind. `s3:PutObject`/`s3:GetObject`) über die IAM-Rolle der
  EC2-Instance bereitstellen.
- Für http(s) Nutzung über das Frontend: Bucket als **Static Website** oder über
  **CloudFront** freigeben.

---

## Backups & Wiederherstellung

| Datum | Art | Ziel |
|---|---|---|
| RDS | Automatische Backups (PITR) | RDS selbst |
| EBS-Volume der EC2 | AMI-/Snapshot (optional) | EC2 |
| Manuell | `scripts/backup_db.sh` (Datenbank-Dump) | S3 |

---

## Monitoring & Alarmierung

- **CloudWatch:** EC2-CPU, RDS-Connections, S3-Anfragen.
- **Health-Check:** `GET /health` — von einem Alarms anrufen lassen.
- **Logs:** Backend-logs via CloudWatch-Agent nach `/aws/backend` streamen.

---

## Kostenabschätzung (Richtwerte, Region eu-central-1)

| Ressource | Beispielgröße | ≈ / Monat |
|---|---|---|
| EC2 t4g.medium (2 vCPU, 4 GB) | on-demand, keine Reserved | ~26 $ |
| RDS db.t4g.small Single-AZ | 20 GB gp3 | ~15 $ |
| S3 | wenige GB | < 1 $ |
| ALB (optional) | 1 Node | ~18 $ |
| **Summe** | | **~60 $** (ohne ALB ~40 $) |

> Werte können abweichen; nutzen Sie den AWS-Pricing-Calculator für Ihre Region.

---

## Vorteile gegenüber aktueller Bereitstellung

| Bereich | Raspberry Pi + Tunnel | AWS (dieser Leitfaden) |
|---|---|---|
| Verfügbarkeit | Einzelgerät | RDS Multi-AZ + ALB |
| Skalierung | Fixe Hardware | Größere EC2 / mehrere Instanzen |
| Verwaltung | Manuell | Verwaltete Dienste, Backups, PITR |
| Sicherheit | Cloudflare-Tunnel | SG, IAM-Rollen, Secrets Manager |
