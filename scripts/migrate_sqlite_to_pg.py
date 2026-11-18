import os, sys, sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django.setup()

from django.apps import apps
from django.db import connection as pg
from django.db import models

SQLITE_PATH = os.environ.get("SQLITE_PATH", "db.sqlite3")
sqlite_conn = sqlite3.connect(SQLITE_PATH)
sqlite_conn.row_factory = sqlite3.Row

all_models = [m for m in apps.get_models() if not m._meta.auto_created]
all_models.sort(key=lambda m: (m._meta.app_label, m._meta.model_name))


def convert_value(field, value):
    """Приводит значение из SQLite к типу, который ждёт Postgres."""
    if value is None:
        return None

    # Булевы поля: SQLite хранит 0/1, Postgres ждёт bool
    if isinstance(field, models.BooleanField):
        return bool(value)

    # Иногда SQLite хранит числа как строки — приводим обратно
    if isinstance(field, (models.IntegerField, models.AutoField, models.BigAutoField)):
        return int(value) if not isinstance(value, int) else value

    if isinstance(field, models.FloatField):
        return float(value)

    return value


with pg.cursor() as cursor:
    for model in all_models:
        table = model._meta.db_table
        try:
            rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
        except sqlite3.OperationalError:
            print(f"skip {table} (нет в SQLite)")
            continue

        if not rows:
            continue

        # Поля модели по именам колонок
        fields_by_column = {f.column: f for f in model._meta.concrete_fields}

        cols = list(rows[0].keys())
        placeholders = ",".join(["%s"] * len(cols))
        col_list = ",".join(f'"{c}"' for c in cols)
        sql = f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'

        inserted = 0
        for row in rows:
            values = []
            for col in cols:
                field = fields_by_column.get(col)
                v = row[col]
                values.append(convert_value(field, v) if field else v)
            cursor.execute(sql, tuple(values))
            inserted += 1

        print(f"{table}: {inserted} строк")


# Сброс sequence для автоинкрементных PK
with pg.cursor() as cursor:
    for model in all_models:
        pk = model._meta.pk
        if pk.get_internal_type() in ("AutoField", "BigAutoField"):
            seq = f"{model._meta.db_table}_{pk.column}_seq"
            cursor.execute(
                f'SELECT setval(\'{seq}\', COALESCE((SELECT MAX("{pk.column}") FROM "{model._meta.db_table}"), 1), true)'
            )

print("Готово.")