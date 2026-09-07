# seiri

Eine Flask-Anwendung **SEIRI – Praktikum** zum Verwalten von Praktikumsbewerbungen (Fachinformatiker – Daten und Prozessanalyse). Der gesamte Ablauf einer Bewerbung wird unterstützt:

- jede Firma hat einen **Status** (verwaltbar im „Status“-Bereich),
- ein **„Sucht?“**-Feld (sucht / sucht nicht / unbekannt),
- eine **Website** und ein gespeichertes **Anschreiben** (Text in der Datenbank),
- eine **„Mein Profil“**-Seite mit deinen persönlichen Daten,
- eine sortierbare Liste (nach Name / Status / letzter Änderung),
- eine Schaltfläche **„PDF generieren“** — ein sauberes A4-Anschreiben mit den Firmendaten, deinen Daten und dem aktuellen Datum,
- **mehrere Stellenangebot-Links** pro Firma (exportierbar),
- eine **Praktikumsseiten**-Seite — eine separate Liste mit Job-Portalen (eigene Tabelle),
- eine **Teilen**-Funktion: eine nur-lesbare Firmenliste über einen geheimen Link,
- eine optionale **Google-Firmensuche** beim Hinzufügen einer neuen Firma.

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
# Windows: .venv\Scripts\python.exe run.py
# Linux/macOS: .venv/bin/python run.py
```

Beim Start prüft `run.py` die Datenbank und aktualisiert das Schema (fehlende Tabellen und Spalten werden angelegt — ohne Daten zu löschen).

Die Anwendung ist dann erreichbar unter: **http://127.0.0.1:5001**

> Hinweis: Der Standard-Port ist **5001**, weil auf macOS der Port 5000 vom Systemprozess ControlCenter (AirPlay) belegt ist. Port und Host lassen sich über Umgebungsvariablen ändern:
>
> ```bash
> PORT=8080 HOST=127.0.0.1 .venv/bin/python run.py
> ```

## Struktur

- `models.py` — Datenbankmodelle (`Status`, `Company`, `Profile`, `Settings`, `JobLink`, `JobSite`) — siehe `docs/db_structure.md`
- `routes.py` — Anwendungsrouten
- `google_places.py` — Google-Places-Suche für neue Firmen (serverseitiger API-Key)
- `run.py` — Application-Factory + Serverstart
- `startdb.py` — Datenbank-Erstellung / automatische Schema-Aktualisierung
- `templates/` — HTML-Templates (Bulma)
- `static/css/app.css` — Design (dunkel, professionell)
- `static/fonts/` — Schriftarten für die PDF-Erzeugung
- `docs/db_structure.md` — Dokumentation der Datenbankstruktur

## Teilen & Export

Im Admin-Bereich erstellt der Tab **„Teilen“** einen geheimen, nicht erratbaren Link (`/share/<token>`), der eine nur-lesbare Liste aller Firmen zeigt (Name, Adresse, Stadt, E-Mail, Telefon, Website, Stellenangebote und „Sucht?“) — inklusive Schaltfläche zum CSV-Export. Der Link ist **nicht passwortgeschützt** — jeder, der den Link hat, sieht die Liste. Erstelle daher einen neuen Link, wenn du den Zugriff widerrufen möchtest.

Auf der geteilten Seite können die Firmen nach **Name**, **Stadt** und **Stellenangebote** sortiert werden. Außerdem gibt es eine Suche nach dem Firmennamen. Stellenangebote werden als kompakte Schaltflächen („Link 1“, „Link 2“ usw.) angezeigt.

Der CSV-Export (immer die gesamte Liste auf einmal) enthält: Name, Adresse, PLZ, Stadt, E-Mail, Telefon, Website, Stellenangebote, Status, Sucht?.

## Google-Firmensuche

Beim Anlegen einer neuen Firma kann über **„Firma suchen“** die Google Places API nach passenden Unternehmen durchsucht werden. Die gefundenen Daten können anschließend über **„Übernehmen“** in das Formular übernommen und vor dem Speichern geprüft werden.

Wenn die Suche ohne Stadt Treffer aus mehreren Städten liefert, muss zuerst eine Stadt ausgewählt werden. Danach wird die Suche auf diese Stadt eingeschränkt. Die Suche wird nur nach einem Klick auf **„Firma suchen“** ausgeführt — nicht automatisch beim Tippen.

Die Google-Suche kann im Admin-Bereich unter **Admin → Teilen → Google-Firmensuche aktivieren** ein- oder ausgeschaltet werden. Ist sie ausgeschaltet, wird die Schaltfläche beim Hinzufügen einer Firma ausgeblendet und der Such-Endpunkt blockiert.

Die Suche kann folgende Daten übernehmen, sofern Google sie liefert:

- Firmenname
- vollständige Adresse
- Straße und Hausnummer
- PLZ und Stadt
- Telefonnummer
- Website

E-Mail-Adressen werden von der verwendeten Google-Places-Suche normalerweise nicht geliefert und bleiben daher meist leer. Die Google Places API kann außerdem eine aktivierte Abrechnung im Google-Cloud-Projekt voraussetzen. Beschränke den API-Key in Google Cloud auf die benötigte Places API und verwende ihn ausschließlich serverseitig.

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

### 4. Secret-Key & Sicherheitsoptionen setzen (empfohlen)

```bash
sudo bash -c 'echo "SECRET_KEY=$(openssl rand -hex 32)" > /etc/seiri.env'
sudo bash -c 'echo "SEIRI_SECURE_COOKIES=1" >> /etc/seiri.env'
sudo bash -c 'echo "BEHIND_PROXY=1" >> /etc/seiri.env'
# Google Places API key — replace the placeholder with your real key
sudo bash -c 'echo "GOOGLE_PLACES_API_KEY=DEIN_GOOGLE_API_KEY" >> /etc/seiri.env'
sudo chmod 600 /etc/seiri.env
```

- `SEIRI_SECURE_COOKIES=1` — Sitzungscookies nur über HTTPS senden (aktivieren, sobald HTTPS läuft, siehe Schritt 7).
- `BEHIND_PROXY=1` — nginx als Reverse-Proxy berücksichtigen (echte Client-IP und `https`-Schema für den Teilen-Link).
- `GOOGLE_PLACES_API_KEY` — serverseitiger Schlüssel für die Firmensuche auf der Seite „Firma hinzufügen“. Der Schlüssel wird nicht im Quellcode gespeichert.
- Ohne gesetzten `SECRET_KEY` erzeugt die Anwendung beim ersten Start automatisch einen zufälligen Schlüssel und speichert ihn in `instance/secret_key`.

Nach dem Eintragen des Schlüssels die Datei absichern und prüfen, ohne den Schlüssel auszugeben:

```bash
sudo chmod 600 /etc/seiri.env
sudo grep -q '^GOOGLE_PLACES_API_KEY=.' /etc/seiri.env && echo 'Google Places API key: SET' || echo 'Google Places API key: MISSING'
```

Das Google-Cloud-Projekt muss die Places API (New) aktiviert haben. Je nach Google-Cloud-Konto ist außerdem ein Billing-Konto erforderlich. API-Keys niemals in Git, Templates oder JavaScript speichern.

Datenbank- und Schlüsseldatei absichern (enthalten persönliche Daten):

```bash
sudo chmod 700 /opt/seiri/instance
sudo chmod 600 /opt/seiri/instance/seiri.db /opt/seiri/instance/secret_key
```

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

Nach Änderungen an `/etc/seiri.env` den Dienst neu starten:

```bash
sudo systemctl daemon-reload
sudo systemctl restart seiri
sudo systemctl status seiri --no-pager
```

### 6. Nginx als Reverse-Proxy

Erstelle `/etc/nginx/sites-available/seiri`:

```nginx
server {
    listen 80;
    server_name deine-domain.de;

    # Teilen-Links nicht loggen (geheimes Token steht in der URL)
    location /share/ {
        access_log off;
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

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

Danach HSTS aktivieren (im `server { … }`-Block für Port 443 der nginx-Konfiguration):

```nginx
add_header Strict-Transport-Security "max-age=31536000" always;
```

> Debug-Modus niemals aktivieren: Der Produktivbetrieb läuft über `waitress-serve`
> (siehe Schritt 5). `FLASK_DEBUG=1` bzw. `python run.py` ist nur für die lokale
> Entwicklung gedacht — der Werkzeug-Debugger darf nie öffentlich erreichbar sein.

### 8. Firewall (optional)

Die App läuft intern nur auf `127.0.0.1`, nach außen werden nur HTTP/HTTPS freigegeben:

```bash
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

Danach ist die Anwendung unter **https://deine-domain.de** erreichbar. Den Teilen-Link findest du im Admin-Bereich unter **„Teilen“**.