# Django-приложение для работы с музыкальными альбомами (Docker + PostgreSQL)

## Стек технологий
- Python 3.11, Django
- PostgreSQL 16
- Docker, Docker Compose

## Запуск для разработки
1. Скопируйте переменные окружения: `cp .env.example .env` (заполните пароль).
2. Запустите контейнеры: `docker compose up --build`.
3. Приложение доступно по адресу: http://localhost:8000.

## Запуск для Production
`docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`

## Миграция данных из SQLite
1. Поместите файл `db.sqlite3` в корень проекта.
2. Запустите базу: `docker compose up -d`.
3. Выполните скрипт: `docker compose exec web python scripts/migrate_sqlite_to_pg.py`.
4. Остановите контейнеры: `docker compose down`.

## Переменные окружения
Настройки хранятся в `.env` (не коммитится в Git). Шаблон: `.env.example`.

## Структура проекта

- `myproject/` — настройки и основные URL-адреса проекта Django.
- `myapp/` — приложение для работы с музыкальными альбомами.
- `myapp/templates/` — HTML-шаблоны страниц.
- `myapp/data/` — папка для хранения файлов с данными.
- `manage.py` — файл для управления проектом.
- `requirements.txt` — список необходимых библиотек.