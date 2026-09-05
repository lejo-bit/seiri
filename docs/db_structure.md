# Struktura bazy danych

## Przegląd

Aplikacja **SEIRI – Praktikum** korzysta z **SQLite** (domyślnie plik
`instance/seiri.db`) obsługiwanego przez **Flask-SQLAlchemy** (wersja 3.1.1).

Definicja modeli znajduje się w pliku `models.py`, w którym współdzielona
instancja `db = SQLAlchemy()` jest inicjalizowana w fabryce aplikacji
(`create_app()` w `app.py`).

> Tabele tworzone są poleceniem:
> ```
> flask --app app init-db
> ```
> (wewnętrznie wykonuje `db.create_all()`).

## Model: `Company`

Reprezentuje **firmę oferującą miejsca praktyk**. Mapa na tabelę o nazwie
`company`.

### Kolumny

| Kolumna       | Typ          | Ograniczenia             | Opis                                |
|---------------|--------------|--------------------------|-------------------------------------|
| `id`          | `Integer`    | `PRIMARY KEY`, AUTOINC   | Identyfikator firmy                 |
| `name`        | `String(120)`| `NOT NULL`               | Nazwa firmy (wymagana)              |
| `address`     | `String(200)`| –                        | Adres firmy                         |
| `email`       | `String(120)`| –                        | Adres e-mail firmy                  |
| `phone`       | `String(40)` | –                        | Numer telefonu                      |
| `description` | `Text`       | –                        | Opis działalności / oferty praktyk  |

### Uwagi

- Kolumny `address`, `email`, `phone`, `description` nie mają wartości
  domyślnych — po utworzeniu rekordu bez podania tych pól przyjmą `NULL`.
- Kolumna `name` jest obowiązkowa (`NOT NULL`); jej walidacja odbywa się
  w warstwie aplikacji (`app.py`, trasa `new_company`), a nie na poziomie
  bazy danych.

### Odpowiednik SQL (SQLite)

```sql
CREATE TABLE company (
    id          INTEGER NOT NULL,
    name        VARCHAR(120) NOT NULL,
    address     VARCHAR(200),
    email       VARCHAR(120),
    phone       VARCHAR(40),
    description TEXT,
    PRIMARY KEY (id)
);
```

### Powiązania / relacje

Brak relacji — model `Company` jest obecnie samodzielny (nie ma tabel
powiązanych kluczami obcymi). Struktura jest gotowa do rozbudowy o kolejne
modele (np. oferty praktyk powiązane z firmą).

## Odwzorowanie ORM

| Warstwa Python (Flask-SQLAlchemy)  | Warstwa SQL / baza          |
|------------------------------------|-----------------------------|
| `Company`                          | tabela `company`            |
| `Company.id`                       | kolumna `id`                |
| `Company.name`                     | kolumna `name`              |
| `Company.address`                  | kolumna `address`           |
| `Company.email`                    | kolumna `email`             |
| `Company.phone`                    | kolumna `phone`             |
| `Company.description`              | kolumna `description`       |

## Konfiguracja połączenia

URI bazy danych jest pobierane kolejno z:

1. zmiennej środowiskowej `DATABASE_URL`,
2. wartości domyślnej `sqlite:///instance/seiri.db` (względem katalogu
   projektu).

W testach używany jest adres in-memory: `sqlite://`.

