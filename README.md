# voice-notes-bot

## Project overview

`voice-notes-bot` is a Telegram bot for turning voice notes into structured text artifacts. It is designed as an MVP that runs on Railway, uses PostgreSQL for persistence, OpenAI for transcription and text processing, and manual payments for minute balance top-ups.

The current MVP focus is HR assessors and personal voice notes: send a voice note, receive a transcript, then turn it into clean text, summaries, tasks, reflection, plans, or HR assessment materials.

## What the bot does

- Transcribes Telegram voice messages.
- Tracks a minute balance and charges minutes only for successful transcription.
- Provides text actions after transcription.
- Shows actions according to `User.current_plan` and the existing user profile.
- Keeps the last successful transcriptions available through `/history`.
- Supports manual payment claims and admin approval/rejection.
- Uses guardrails so text-processing outputs stay artifact-style.

## Main flows

### Voice transcription

The user sends a Telegram voice message. The bot checks the user's balance, downloads the audio, transcribes it with the transcription model selected for the user's plan, saves the transcript, deducts rounded-up minutes only after success, and shows action buttons for the transcript.

Free and Personal plans use fast transcription. Professional and Premium plans use premium transcription. Unknown plans fall back to the fast transcription model or the legacy `TRANSCRIPTION_MODEL` setting.

### Text processing actions

Visible actions after transcription and in `/history` depend on the current plan and profile:

- Free: basic actions only (`🧹 Очистить`, `📝 Саммари`).
- Personal + `personal_notes`: basic actions, `✅ Задачи`, `🧠 Рефлексия`, and `📅 План`.
- Premium HR + `hr_assessor`: basic actions and HR role-specific actions.
- Professional: internal / legacy plan for legacy profile actions.

These actions do not deduct additional minutes in the current MVP.
After every text-processing result, the bot sends a fresh action panel for the same transcription so users do not need to scroll back to the original buttons.

For the `personal_notes` profile, the post-transcription UI is intentionally smaller:

- `🧹 Очистить`
- `📝 Саммари`
- `✅ Задачи`
- `🧠 Рефлексия`
- `📅 План`

### Start and Plans

`/start` shows the product description, main modes, and public tariffs. Users can send a voice message immediately; no setup questionnaire is required.

Public tariffs shown in `/start` and `/buy`:

- Free: 0 RUB, 30 minutes, fast transcription, clean text and summary.
- Personal: 199 RUB, 300 minutes, Personal Notes actions.
- Premium HR: 1290 RUB, 1000 minutes, premium transcription, stronger HR text model, HR assessor actions.

Professional is an internal / legacy plan and is not presented as a primary public tariff.

Paid plans now have `User.plan_expires_at`:

- Personal: 60 days.
- Premium HR: 60 days.
- Professional: 60 days.
- Premium HR Trial: 7 days, stored as `current_plan="premium"` with `profile_type="hr_assessor"`.

Existing paid users with `plan_expires_at = NULL` remain active for backward compatibility.

### Subscription expiration

Access checks use an effective plan instead of raw `User.current_plan`. When a paid plan has expired, `get_effective_plan(user)` returns `free`, so visible buttons, `/history` actions, role callbacks, and model selection fall back to Free access. The stored `current_plan` is not overwritten automatically; `/balance` and admin summaries show both the current plan and the effective plan when they differ.

Premium HR Trial is a 7-day Premium HR access grant. It stores `current_plan="premium"`, sets `profile_type="hr_assessor"`, grants 1000 minutes, and sets `plan_expires_at` 7 days ahead.

`/setup` is deprecated. It remains as a safe legacy handler, but it no longer starts the questionnaire; access is determined by tariff.

### Profile-specific actions

Role actions are configured in `app/bot/role_actions.py`. The bot shows action rows only when both `UserProfile.profile_type` and `User.current_plan` allow them.

Supported profile-specific actions:

- HR / Assessor
- Personal Notes

Internal / legacy profile-specific actions remain in the code and callback routing:

- PM / BA
- Founder
- Student / Researcher

Profile-specific actions do not deduct additional minutes in the current MVP. HR actions are Premium HR only. Personal Notes actions are available on Personal and Premium. Legacy PM/BA, Founder, and Student/Researcher actions remain available only for legacy users on Professional or Premium.

### History

`/history` shows the latest successful transcriptions. Users can open the full text and run the same actions currently visible for their plan and profile. HR buttons are shown only for Premium HR users, Personal Notes buttons only for Personal/Premium users, and Free users see only basic actions.

### Balance / manual payments

`/balance` shows the user's Telegram ID, remaining minutes, and recent transactions. `/buy` is the manual sales/paywall screen: it shows Free, Personal, and Premium HR, explains what each tariff includes, shows the user's Telegram ID, and provides payment instructions. Professional is internal / legacy and is not a primary public option in `/buy`.

Users should send the selected tariff, payment confirmation, and their Telegram ID to the administrator, then claim payment with the `Я оплатил` button. If payment details are not configured, `/buy` tells the user to уточнить реквизиты у администратора. Admins can approve or reject the claim.

Plan-gated upgrade messages point users to `/buy` so they can see the tariff and manual payment instructions.

Package settings are configured through environment variables. The current MVP does not use Telegram Stars.

### Admin flow

Admins are configured with `ADMIN_TELEGRAM_IDS`. Admin tools include payment review, approve/reject flows, manual minute adjustments, Premium HR Trial grants, and basic stats.
The primary access-management action is assigning a plan. When an admin changes a user's plan, the bot sets `User.current_plan`, sets the remaining balance to the plan package minutes, and applies the default profile where appropriate:

- Free: sets 30 remaining minutes; creates `personal_notes` only if the user has no profile.
- Personal: sets 300 remaining minutes, `profile_type="personal_notes"`, and a 60-day expiration.
- Premium HR: sets 1000 remaining minutes, `profile_type="hr_assessor"`, and a 60-day expiration.
- Premium HR Trial: service helper support for 1000 minutes, `profile_type="hr_assessor"`, and a 7-day expiration.
- Professional: sets 600 remaining minutes, a 60-day expiration, and leaves the existing legacy profile unchanged.

Manual add/remove minutes remains available as an admin-only secondary operation.

## Supported profiles

### HR / Assessor

Profile key: `hr_assessor`

Actions:

- `📋 HR-саммари`
- `⚖️ Факты / интерпретации`
- `👥 Люди`
- `🧠 Компетенции`
- `💪 Сильные стороны / зоны роста`
- `📈 Рекомендации по развитию`
- `🧾 HR-отчёт`

### PM / BA

Internal / experimental / legacy profile. It is not shown in the public UX.

Profile key: `pm_ba`

Actions:

- `📌 Протокол`
- `🧩 User Story`
- `☑️ Критерии`
- `⚠️ Риски`

### Founder

Internal / experimental / legacy profile. It is not shown in the public UX.

Profile key: `founder`

Actions:

- `🚀 Идея`
- `🧪 Гипотезы`
- `🧱 MVP`
- `🎤 Pitch`

### Student / Researcher

Internal / experimental / legacy profile. It is not shown in the public UX.

Profile key: `student_researcher`

Actions:

- `🎓 Конспект`
- `🔍 Исследование`
- `🧠 Объяснить проще`
- `🗂️ Карточки`

### Personal Notes

Profile key: `personal_notes`

Actions:

- `🧠 Рефлексия`
- `🗂️ Категории`
- `🏷️ Теги`
- `📅 План`

## Safety / guardrails

Text-processing prompts include shared guardrails:

- Return only the requested artifact.
- Do not add unsupported facts.
- Do not address the user directly.
- Do not add conversational tails such as "Если хочешь, могу...".
- Keep assumptions separate from facts.
- Stay inside the requested format.

HR actions are designed to structure notes and draft reports, not to make final hiring or employment decisions.

Personal Notes actions structure private notes, but do not diagnose, provide therapy, or make medical/psychological claims. Emotional content is handled neutrally.

## Local development

Requirements:

- Python 3.11+
- PostgreSQL

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

Fill `.env` locally. Do not commit `.env`.

Apply migrations:

```bash
alembic upgrade head
```

Run the bot locally only when you intentionally want to start polling:

```bash
python -m app.main
```

Useful checks:

```bash
python -m compileall app
alembic heads
```

## Railway deployment

The Railway start command is defined in `railway.toml`:

```bash
python -m app.main
```

Deployment checklist:

- Create a Railway service from the GitHub repository.
- Attach or configure PostgreSQL.
- Set all required environment variables in Railway Variables.
- Run `alembic upgrade head` against the Railway database before the service handles users.
- Check deploy logs after redeploy.
- Confirm the bot responds in Telegram.

Secrets must live in Railway Variables, not in Git.

## Environment variables

Actual settings are defined in `app/config.py`. `.env.example` contains placeholder or safe default values only.

Required or commonly used variables:

- `BOT_TOKEN`
- `OPENAI_API_KEY`
- `DATABASE_URL`
- `ADMIN_TELEGRAM_IDS`
- `TEXT_MODEL`
- `TEXT_MODEL_FREE`
- `TEXT_MODEL_PAID`
- `TEXT_MODEL_HR`
- `TEXT_MODEL_LEGACY`
- `TRANSCRIPTION_MODEL`
- `TRANSCRIPTION_MODEL_FAST`
- `TRANSCRIPTION_MODEL_PREMIUM`
- `SBP_PHONE`
- `SBP_BANK_NAME`
- `SBP_RECIPIENT_NAME`
- `SBP_PAYMENT_COMMENT`
- `DEFAULT_FREE_MINUTES`
- `FRIENDS_PACKAGE_MINUTES`
- `POWER_PACKAGE_MINUTES`
- `FRIENDS_PACKAGE_PRICE`
- `POWER_PACKAGE_PRICE`

`TRANSCRIPTION_MODEL` and `TEXT_MODEL` are kept for backward compatibility. If `TRANSCRIPTION_MODEL_FAST` is empty, the app falls back to `TRANSCRIPTION_MODEL` or `gpt-4o-mini-transcribe`. If a plan-specific text model is empty, the app falls back to `TEXT_MODEL`, `TEXT_MODEL_PAID`, or the safe defaults in `app/config.py`.

## Manual QA checklist

See [docs/MANUAL_QA.md](docs/MANUAL_QA.md).

Short release smoke test:

- `/start`
- `/help`
- `/setup`
- `/balance`
- `/history`
- send one short voice note
- run one universal action
- confirm a fresh action panel appears below the processing result
- confirm `/start` shows product description and tariffs
- confirm `/start`, `/buy`, and `/balance` show the user's Telegram ID
- confirm `/setup` says setup is no longer required
- confirm tariff-based action gating after transcription
- create and review one manual payment claim

## Known limitations / Next steps

Current limitations:

- No automated test suite yet.
- No separate dev/prod bot setup documented in code.
- Premium transcription is selected by plan; separate premium rerun UX is planned for later.
- Telegram Stars are planned for later, not implemented.
- Export to Notion, Google Docs, Bear, or similar tools is planned for later, not implemented.

Planned next steps:

- Separate dev and production bots.
- Add automated tests for billing, action gating, and callback processing.
- Add premium transcription rerun when pricing and UX are ready.
- Add exports after core flows stay stable.
- Continue reducing duplication around action routing where it remains safe.

## Release notes

See [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md).
