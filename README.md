# voice-notes-bot

Telegram-бот принимает голосовые сообщения, транскрибирует их через OpenAI,
ведёт баланс минут и поддерживает ручные платежи и администрирование. После
транскрибации пользователь может очистить текст, получить краткое резюме или
выделить список задач. Команда `/history` позволяет вернуться к последним десяти
успешным транскрипциям и повторно открыть или обработать их.

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
- `OPENAI_API_KEY` - API key для транскрибации и обработки текста.
- `TRANSCRIPTION_MODEL` - модель транскрибации, по умолчанию
  `gpt-4o-mini-transcribe`.
- `TEXT_MODEL` - модель для Clean/Summary/Tasks, по умолчанию
  `gpt-5.4-nano`.
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

Основные пользовательские команды:

- `/start` - регистрация и начало работы.
- `/balance` - баланс минут и последние операции.
- `/buy` - пакеты минут.
- `/history` - последние 10 успешных транскрипций.
- `/admin` - меню администратора.

## Ручная проверка

1. Выполните `/start`, затем `/balance`.
2. В `/buy` получите Free-пакет либо создайте заявку на Friends/Power.
3. Проверьте заявку через `/admin` с аккаунта администратора.
4. Отправьте voice-сообщение при положительном балансе.
5. При настроенном `OPENAI_API_KEY` бот должен показать статус обработки,
   вернуть транскрипцию, списать округлённое вверх количество минут и показать
   кнопки `🧹 Очистить`, `📝 Summary`, `✅ Задачи`.
6. Нажмите каждую кнопку и убедитесь, что бот обрабатывает именно выбранную
   транскрипцию. За эти операции дополнительные минуты не списываются.
7. Выполните `/history`, откройте полный текст кнопкой `📄 Текст` и повторно
   проверьте Clean/Summary/Tasks для одной из прошлых транскрипций.
8. Удалите `OPENAI_API_KEY`, перезапустите бота и повторите отправку. Бот должен
   сообщить, что ключ не настроен, не списывая минуты.

Bear export и Telegram Stars пока не подключены.

## Deploy to Railway

1. Загрузите проект в GitHub, не добавляя локальный файл `.env`.
2. В Railway создайте новый Service из GitHub-репозитория проекта.
3. Railway использует команду запуска из `railway.toml`:

```bash
python -m app.main
```

4. Добавьте в Railway Variables необходимые переменные окружения:

```text
BOT_TOKEN
OPENAI_API_KEY
DATABASE_URL
ADMIN_TELEGRAM_IDS
SBP_PHONE
SBP_BANK_NAME
SBP_RECIPIENT_NAME
SBP_PAYMENT_COMMENT
DEFAULT_FREE_MINUTES
FRIENDS_PACKAGE_MINUTES
POWER_PACKAGE_MINUTES
FRIENDS_PACKAGE_PRICE
POWER_PACKAGE_PRICE
TRANSCRIPTION_MODEL
TEXT_MODEL
```

5. Перед запуском сервиса примените Alembic-миграции к Railway PostgreSQL:

```bash
alembic upgrade head
```

Файл `.env` нельзя коммитить в GitHub. Токены, ключи, URL базы данных и другие
секреты добавляйте только через раздел Railway Variables.
