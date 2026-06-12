# voice-notes-bot

Telegram-бот принимает голосовые сообщения, транскрибирует их через OpenAI,
ведёт баланс минут и поддерживает ручные платежи и администрирование.

## Требования

- Python 3.11+
- PostgreSQL

## Установка

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

## Конфигурация

Заполните локальный `.env`:

- `BOT_TOKEN` - токен Telegram-бота.
- `DATABASE_URL` - URL PostgreSQL с драйвером `asyncpg`.
- `ADMIN_TELEGRAM_IDS` - Telegram ID администраторов через запятую.
- `OPENAI_API_KEY` - API key для транскрибации.
- `TRANSCRIPTION_MODEL` - модель транскрибации, по умолчанию
  `gpt-4o-mini-transcribe`.
- Параметры `SBP_*` и цены пакетов - настройки ручной оплаты.

Пример URL базы данных:

```text
postgresql+asyncpg://postgres:password@localhost:5432/voice_notes_bot
```

`.env` содержит секреты и не должен коммититься в GitHub. Он добавлен в
`.gitignore`. В `.env.example` должны оставаться только безопасные пустые или
демонстрационные значения.

Бот запускается без `OPENAI_API_KEY`. В этом случае команды и админка доступны,
а при отправке voice-сообщения бот сообщает, что транскрибация не настроена.

## Миграции

Применить миграции:

```bash
alembic upgrade head
```

Создать миграцию после изменения моделей:

```bash
alembic revision --autogenerate -m "describe change"
```

## Запуск

```bash
python -m app.main
```

## Ручная проверка

1. Выполните `/start`, затем `/balance`.
2. В `/buy` получите Free-пакет либо создайте заявку на Friends/Power.
3. Проверьте заявку через `/admin` с аккаунта администратора.
4. Отправьте voice-сообщение при положительном балансе.
5. При настроенном `OPENAI_API_KEY` бот должен показать статус обработки,
   вернуть транскрипцию и списать округлённое вверх количество минут.
6. Удалите `OPENAI_API_KEY`, перезапустите бота и повторите отправку. Бот должен
   сообщить, что ключ не настроен, не списывая минуты.

Clean/Summary/Tasks, Bear export и Telegram Stars пока не подключены.
