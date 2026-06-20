# voice-notes-bot

## Project overview

`voice-notes-bot` is a Telegram bot for turning voice notes into structured text artifacts. It is designed as an MVP that runs on Railway, uses PostgreSQL for persistence, OpenAI for transcription and text processing, and manual payments for minute balance top-ups.

The current MVP focus is HR assessors and personal voice notes: send a voice note, receive a transcript, then turn it into clean text, summaries, tasks, reflection, plans, or HR assessment materials.

## What the bot does

- Transcribes Telegram voice messages.
- Tracks a minute balance and charges minutes only for successful transcription.
- Provides text actions after transcription.
- Runs a 5-step onboarding flow with two public profiles and stores `UserProfile.profile_type`.
- Shows profile-specific actions only for the active profile.
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

For the `personal_notes` profile, the post-transcription UI is intentionally smaller:

- `🧹 Очистить`
- `📝 Саммари`
- `✅ Задачи`
- `🧠 Рефлексия`
- `📅 План`

### Onboarding

New users can complete a 5-step setup flow through `/start` or `/setup`. The public profile choice is limited to:

- `📋 HR / оценка персонала`
- `🧠 Личные заметки`

The flow then asks about preferred output, audio source, quality preference, and usage frequency.

The service layer calculates:

- profile type
- recommended plan
- recommended transcription quality
- onboarding summary

The Telegram flow saves this data in `UserProfile` and marks onboarding as completed. It does not change billing rules.

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

`/balance` shows remaining minutes and recent transactions. `/buy` starts the manual payment flow. Users can claim payment with the `Я оплатил` button, and admins can approve or reject the claim.

Package settings are configured through environment variables. The current MVP does not use Telegram Stars.

### Admin flow

Admins are configured with `ADMIN_TELEGRAM_IDS`. Admin tools include payment review, approve/reject flows, manual minute adjustments, and basic stats.

## Supported profiles

### HR / Assessor

Profile key: `hr_assessor`

Actions:

- `📋 HR-саммари`
- `🧠 Компетенции`
- `⚖️ Факты / интерпретации`
- `🧾 HR-отчёт`

### PM / BA

Internal / experimental / legacy profile. It is not shown in the public onboarding flow.

Profile key: `pm_ba`

Actions:

- `📌 Протокол`
- `🧩 User Story`
- `☑️ Критерии`
- `⚠️ Риски`

### Founder

Internal / experimental / legacy profile. It is not shown in the public onboarding flow.

Profile key: `founder`

Actions:

- `🚀 Идея`
- `🧪 Гипотезы`
- `🧱 MVP`
- `🎤 Pitch`

### Student / Researcher

Internal / experimental / legacy profile. It is not shown in the public onboarding flow.

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
- confirm onboarding shows only HR / assessment and personal notes
- confirm personal notes shows only clean, summary, tasks, reflection, and plan actions after transcription
- confirm HR profile still shows the existing HR buttons
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
- Add automated tests for onboarding, billing, action gating, and callback processing.
- Add premium transcription rerun when pricing and UX are ready.
- Add exports after core flows stay stable.
- Continue reducing duplication around action routing where it remains safe.

## Release notes

See [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md).
