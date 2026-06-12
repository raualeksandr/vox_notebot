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

## Настройка пакетов и локальная проверка

Для ручных платежей заполните в `.env` параметры СБП, а также цены платных
пакетов:

```text
FRIENDS_PACKAGE_PRICE=0
POWER_PACKAGE_PRICE=0
```

Замените `0` на актуальные суммы. Пока цена равна нулю, бот не создаёт заявку
на платный пакет, чтобы случайно не показать пользователю неверную стоимость.

Перед проверкой примените миграции и запустите бота:

```bash
alembic upgrade head
python -m app.main
```

В Telegram проверьте сценарии по порядку:

1. Отправьте `/start`, затем `/balance`.
2. Откройте `/buy` и один раз выберите Free.
3. После настройки цен и реквизитов выберите Friends или Power и нажмите
   `Я оплатил`.
4. С аккаунта, чей ID указан в `ADMIN_TELEGRAM_IDS`, вызовите `/admin`, откройте
   `Pending payments` и подтвердите или отклоните заявку.
5. В админском меню проверьте ручное начисление и списание по `telegram_id` или
   `@username`.
6. Отправьте voice-сообщение. При положительном балансе бот вернёт заглушку и
   не спишет минуты.

Пользователь должен хотя бы один раз открыть чат с ботом и отправить `/start`,
иначе Telegram не позволит боту отправить ему уведомление первым.
