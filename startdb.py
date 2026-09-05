"""Tworzenie i automatyczna aktualizacja bazy danych SEIRI.

Można też uruchomić jako skrypt:
    python startdb.py
"""
import datetime
import os

from sqlalchemy import inspect, text

from models import db, _utcnow


def ensure_schema(app):
    """Sprawdza istniejącą bazę danych i aktualizuje jej schemat.

    - tworzy katalog instance/ (jeśli nie istnieje),
    - tworzy brakujące tabele,
    - dodaje brakujące kolumny do istniejących tabel (ALTER TABLE).
    Istniejące dane zostają zachowane.
    """
    basedir = os.path.abspath(os.path.dirname(__file__))
    os.makedirs(os.path.join(basedir, "instance"), exist_ok=True)

    changed = False
    with app.app_context():
        engine = db.engine

        # 1) brakujące tabele
        inspector = inspect(engine)
        existing = set(inspector.get_table_names())
        for table in db.metadata.sorted_tables:
            if table.name not in existing:
                table.create(engine)
                changed = True
                print(f"Utworzono tabelę: {table.name}")

        # 2) brakujące kolumny w istniejących tabelach
        inspector = inspect(engine)
        existing = set(inspector.get_table_names())
        with engine.begin() as conn:
            for table in db.metadata.sorted_tables:
                if table.name not in existing:
                    continue
                columns = {c["name"] for c in inspector.get_columns(table.name)}
                for column in table.columns:
                    if column.name not in columns:
                        col_type = column.type.compile(engine.dialect)
                        conn.execute(
                            text(f"ALTER TABLE {table.name} ADD COLUMN {column.name} {col_type}")
                        )
                        changed = True
                        print(f"Dodano kolumnę: {table.name}.{column.name}")

        # 3) backfill: nadaj datę „ostatniej zmiany” rekordom bez niej
        inspector = inspect(engine)
        if {"company"} <= set(inspector.get_table_names()):
            cols = {c["name"] for c in inspector.get_columns("company")}
            if "updated_at" in cols:
                with engine.begin() as conn:
                    result = conn.execute(
                        text("UPDATE company SET updated_at = :ts WHERE updated_at IS NULL"),
                        {"ts": _utcnow()},
                    )
                    if result.rowcount:
                        changed = True
                        print(f"Ustawiono datę zmiany dla {result.rowcount} firm.")

    return changed


def main():
    from run import create_app

    app = create_app()
    if ensure_schema(app):
        print("Schemat bazy danych został zaktualizowany.")
    else:
        print("Baza danych jest aktualna.")


if __name__ == "__main__":
    main()
