# voice-notes-bot

Стартовый каркас Telegram-бота для обработки голосовых заметок. На текущем
этапе команды и сервисы работают как заглушки, а вызовы OpenAI и платежная
логика не подключены.

## Требования

- Python 3.11+
- PostgreSQL

## Установка

Создайте виртуальное окружение:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Для macOS/Linux активация выглядит так:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Установите зависимости:

```bash
python -m pip install -r requirements.txt
```

## Конфигурация

Создайте локальный `.env` из примера.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Заполните в `.env` как минимум `BOT_TOKEN` и `DATABASE_URL`. При необходимости
укажите Telegram ID администраторов в `ADMIN_TELEGRAM_IDS` через запятую,
например `123456789,987654321`. Параметры СБП понадобятся на следующем этапе.
`OPENAI_API_KEY` пока можно оставить пустым: приложение не обращается к OpenAI.

Не коммитьте `.env` в GitHub. Файл содержит локальные секреты и уже добавлен в
`.gitignore`. Файл `.env.example` содержит только безопасные пустые значения.

Пример URL PostgreSQL для асинхронного драйвера:

```text
postgresql+asyncpg://postgres:password@localhost:5432/voice_notes_bot
```

## Запуск

Из корня проекта выполните:

```bash
python -m app.main
```

Доступны stub-команды `/start`, `/help`, `/balance`, `/buy` и `/admin`.
Реальная OpenAI-транскрибация будет подключена на следующем этапе.

## Миграции базы данных

После заполнения `DATABASE_URL` примените начальную миграцию:

```bash
alembic upgrade head
```

При изменении SQLAlchemy-моделей новую миграцию можно создать командой:

```bash
alembic revision --autogenerate -m "describe change"
```
