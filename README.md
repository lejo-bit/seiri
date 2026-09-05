# seiri

Aplikacja Flask **SEIRI – aplikacje Praktikum** — baza firm oferujących miejsca
praktyk. Obsługuje cały workflow wysyłania aplikacji na praktyki:

- każda firma ma **status** (dodajesz/usuwasz je w panelu „Statusy”),
- pole **„szukają kogoś na praktyki?”** (szukają / nie szukają / nie wiem),
- **stronę internetową** oraz zapisany **list motywacyjny** (tekst w bazie),
- **„Mój profil”** z Twoimi danymi,
- sortowalna lista (po nazwie / statusie / dacie ostatniej zmiany),
- przycisk **„Generuj PDF”** — ładny list motywacyjny z danymi firmy,
  Twoimi danymi i datą (A4).

Interfejs korzysta z frameworka CSS **Bulma** (ciemny motyw).


## Uruchomienie

W katalogu projektu, w środowisku wirtualnym `.venv`:

```bash
# (opcjonalnie) przygotuj / zaktualizuj schemat bazy danych
.venv/bin/python startdb.py

# uruchom serwer deweloperski
.venv/bin/python run.py
```

Przy każdym starcie `run.py` sam sprawdza istniejącą bazę danych i aktualizuje
jej schemat (tworzy brakujące tabele i kolumny — bez kasowania danych).

Aplikacja będzie dostępna pod adresem: **http://127.0.0.1:5001**

> Uwaga: domyślnie używany jest port **5001**, ponieważ na macOS port 5000
> jest zajęty przez systemowy proces ControlCenter (AirPlay) i nie da się tam
> uruchomić serwera. Port i host można zmienić zmiennymi środowiskowymi:
>
> ```bash
> PORT=8080 HOST=127.0.0.1 .venv/bin/python run.py
> ```

## Struktura

- `models.py` — modele bazy danych (`Status`, `Company`, `Profile`) — patrz `docs/db_structure.md`
- `routes.py` — trasy aplikacji
- `run.py` — fabryka aplikacji + start serwera
- `startdb.py` — tworzenie / automatyczna aktualizacja bazy danych
- `templates/` — szablony HTML (Bulma)
- `static/css/app.css` — motyw (ciemny, profesjonalny)
- `static/fonts/` — czcionki użyte w generowaniu PDF (Arial + pogrubiona)
- `docs/db_structure.md` — opis struktury bazy danych


