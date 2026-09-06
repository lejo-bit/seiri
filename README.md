# seiri

Eine Flask-Anwendung **SEIRI – Praktikum** zum Verwalten von Praktikumsbewerbungen (Fachinformatiker – Daten und Prozessanalyse). Der gesamte Ablauf einer Bewerbung wird unterstützt:

- jede Firma hat einen **Status** (verwaltbar im „Status“-Bereich),
- ein **„Sucht?“**-Feld (sucht / sucht nicht / unbekannt),
- eine **Website** und ein gespeichertes **Anschreiben** (Text in der Datenbank),
- eine **„Mein Profil“**-Seite mit deinen persönlichen Daten,
- eine sortierbare Liste (nach Name / Status / letzter Änderung),
- eine Schaltfläche **„PDF generieren“** — ein sauberes A4-Anschreiben mit den Firmendaten, deinen Daten und dem aktuellen Datum,
- **mehrere Stellenangebot-Links** pro Firma (exportierbar),
- eine **Teilen**-Funktion: eine nur-lesbare Firmenliste über einen geheimen Link.

Die Oberfläche nutzt das CSS-Framework **Bulma** (dunkles Design). Die Bedienoberfläche ist auf Deutsch.

## Installation

Im Projektverzeichnis mit einer virtuellen Umgebung:

```bash
# virtuelle Umgebung anlegen
python -m venv .venv

# Umgebung aktivieren
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt
```

## Starten (lokal)

```bash
# (optional) Datenbankschema anlegen / aktualisieren
.venv/bin/python startdb.py

# Entwicklungsserver starten
.venv/bin/python run.py
```

Beim Start prüft `run.py` die Datenbank und aktualisiert das Schema (fehlende Tabellen und Spalten werden angelegt — ohne Daten zu löschen).

Die Anwendung ist dann erreichbar unter: **http://127.0.0.1:5001**

> Hinweis: Der Standard-Port ist **5001**, weil auf macOS der Port 5000 vom Systemprozess ControlCenter (AirPlay) belegt ist. Port und Host lassen sich über Umgebungsvariablen ändern:
>
> ```bash
> PORT=8080 HOST=127.0.0.1 .venv/bin/python run.py
> ```

## Struktur

- `models.py` — Datenbankmodelle (`Status`, `Company`, `Profile`, `Settings`, `JobLink`) — siehe `docs/db_structure.md`
- `routes.py` — Anwendungsrouten
- `run.py` — Application-Factory + Serverstart
- `startdb.py` — Datenbank-Erstellung / automatische Schema-Aktualisierung
- `templates/` — HTML-Templates (Bulma)
- `static/css/app.css` — Design (dunkel, professionell)
- `static/fonts/` — Schriftarten für die PDF-Erzeugung
- `docs/db_structure.md` — Dokumentation der Datenbankstruktur

## Teilen & Export

Im Admin-Bereich erstellt der Tab **„Teilen“** einen geheimen, nicht erratbaren Link (`/share/<token>`), der eine nur-lesbare Liste aller Firmen zeigt (Name, Adresse, Status, „Sucht?“) — inklusive Schaltfläche zum CSV-Export. Der Link ist **nicht passwortgeschützt** — jeder, der den Link hat, sieht die Liste. Erstelle daher einen neuen Link, wenn du den Zugriff widerrufen möchtest.

Der CSV-Export (immer die gesamte Liste auf einmal) enthält: Name, Adresse, Adresse 2, Stadt, E-Mail, Telefon, Website, Stellenangebote, Status, Sucht?.

## Auf einem eigenen VPS-Server installieren

Eine Schritt-für-Schritt-Anleitung für einen eigenen Server (getestet mit Ubuntu 22.04 / Debian 12).

### 1. Server vorbereiten

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git nginx
```

### 2. Projekt hochladen

```bash
# Variante A: per Git
git clone <dein-repo-url> /opt/seiri

# Variante B: per rsync von deinem Rechner
rsync -avz /pfad/zu/seiri/ benutzer@dein-server:/opt/seiri/
```

### 3. Virtuelle Umgebung & Abhängigkeiten

```bash
cd /opt/seiri
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 4. Secret-Key setzen (empfohlen)

```bash
sudo bash -c 'echo "SECRET_KEY=$(openssl rand -hex 32)" > /etc/seiri.env'
```

> Ohne gesetzten `SECRET_KEY` erzeugt die Anwendung beim ersten Start automatisch einen zufälligen Schlüssel und speichert ihn in `instance/secret_key`.

### 5. Systemd-Dienst

Erstelle `/etc/systemd/system/seiri.service`:

```ini
[Unit]
Description=SEIRI – Praktikum
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/seiri
EnvironmentFile=/etc/seiri.env
ExecStart=/opt/seiri/.venv/bin/waitress-serve --host 127.0.0.1 --port 5001 --call run:create_app
Restart=always

[Install]
WantedBy=multi-user.target
```

Anschließend aktivieren und starten:

```bash
sudo chown -R www-data:www-data /opt/seiri
sudo systemctl daemon-reload
sudo systemctl enable --now seiri
sudo systemctl status seiri
```

### 6. Nginx als Reverse-Proxy

Erstelle `/etc/nginx/sites-available/seiri`:

```nginx
server {
    listen 80;
    server_name deine-domain.de;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Aktivieren und neu laden:

```bash
sudo ln -s /etc/nginx/sites-available/seiri /etc/nginx/sites-enabled/seiri
sudo nginx -t
sudo systemctl reload nginx
```

### 7. HTTPS mit Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d deine-domain.de
```

### 8. Firewall (optional)

Die App läuft intern nur auf `127.0.0.1`, nach außen werden nur HTTP/HTTPS freigegeben:

```bash
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

Danach ist die Anwendung unter **https://deine-domain.de** erreichbar. Den Teilen-Link findest du im Admin-Bereich unter **„Teilen“**.