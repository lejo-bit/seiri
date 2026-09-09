"""Create and automatically update the SEIRI database.

Can also be run as a script:
    python startdb.py
"""
import datetime
import os

from sqlalchemy import inspect, text

from models import db, _utcnow


def ensure_schema(app):
    """Check the existing database and update its schema.

    - creates the instance/ directory (if missing),
    - creates missing tables,
    - adds missing columns to existing tables (ALTER TABLE).
    Existing data is preserved.
    """
    basedir = os.path.abspath(os.path.dirname(__file__))
    os.makedirs(os.path.join(basedir, "instance"), exist_ok=True)

    changed = False
    with app.app_context():
        engine = db.engine

        # 1) missing tables
        inspector = inspect(engine)
        existing = set(inspector.get_table_names())
        for table in db.metadata.sorted_tables:
            if table.name not in existing:
                table.create(engine)
                changed = True
                print(f"Created table: {table.name}")

        # 2) missing columns in existing tables
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
                        if table.name == "settings" and column.name == "google_search_enabled":
                            # Existing installations should keep Google search
                            # enabled until the administrator turns it off.
                            statement = (
                                "ALTER TABLE settings ADD COLUMN "
                                "google_search_enabled BOOLEAN NOT NULL DEFAULT 1"
                            )
                        elif table.name == "settings" and column.name == "design":
                            statement = (
                                "ALTER TABLE settings ADD COLUMN "
                                "design VARCHAR(20) NOT NULL DEFAULT 'dark'"
                            )
                        else:
                            statement = (
                                f"ALTER TABLE {table.name} ADD COLUMN "
                                f"{column.name} {col_type}"
                            )
                        conn.execute(text(statement))
                        changed = True
                        print(f"Added column: {table.name}.{column.name}")

        # 3) backfill: give records without one a "last change" date
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
                        print(f"Set change date for {result.rowcount} companies.")

    return changed


def main():
    from run import create_app

    app = create_app()
    if ensure_schema(app):
        print("Database schema has been updated.")
    else:
        print("Database is up to date.")


if __name__ == "__main__":
    main()
