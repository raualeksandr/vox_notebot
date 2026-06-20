# Manual QA checklist

Use this checklist before a release or Railway redeploy. Run it against a test bot/account when possible.

## A. Smoke test

- Send `/start`.
- Send `/help`.
- Send `/setup`.
- Send `/balance`.
- Send `/history`.

Expected result: commands respond without errors. `/start` shows the product description and tariffs. `/setup` does not start the old questionnaire.

## B. Start / Setup / Menu

- Run `/start` and confirm it explains VoxNoteBot, Personal Notes, Premium HR, and tariffs.
- Confirm `/start` shows the user's Telegram ID.
- Run `/setup` and confirm it says setup is no longer required.
- Confirm `/setup` does not show questionnaire buttons.
- Confirm the reply menu does not contain `⚙️ Настройка`.
- Confirm the reply menu contains `🛒 Тарифы`.
- Click `🛒 Тарифы` and confirm it opens the `/buy` tariff/package flow.

## C. Voice

- Send a short voice message.
- Confirm the bot transcribes it.
- Confirm minutes are deducted only after successful transcription.
- Confirm failed transcription does not deduct minutes.
- Confirm the transcript is saved with `status="completed"` after success.

## D. Universal actions

For a Free user, confirm only these actions are visible after transcription:

- `🧹 Очистить`
- `📝 Саммари`

For a Personal user with `profile_type="personal_notes"`, confirm these actions are visible:

- `🧹 Очистить`
- `📝 Саммари`
- `✅ Задачи`
- `🧠 Рефлексия`
- `📅 План`

Expected result: each action returns a structured artifact and does not deduct extra minutes.
After each result, a new `Что сделать с этой транскрипцией дальше?` action panel appears below the result.

## E. Role-specific actions

For each eligible paid profile, run at least one role-specific action:

- Premium HR: confirm all 7 HR buttons are visible: `📋 HR-саммари`, `⚖️ Факты / интерпретации`, `👥 Люди`, `🧠 Компетенции`, `💪 Сильные стороны / зоны роста`, `📈 Рекомендации`, `🧾 HR-отчёт`.
- Professional/Premium PM/BA: click one of `📌 Протокол`, `🧩 User Story`, `☑️ Критерии`, `⚠️ Риски`.
- Professional/Premium Founder: click one of `🚀 Идея`, `🧪 Гипотезы`, `🧱 MVP`, `🎤 Pitch`.
- Professional/Premium Student/Researcher: click one of `🎓 Конспект`, `🔍 Исследование`, `🧠 Объяснить проще`, `🗂️ Карточки`.
- Personal/Premium Personal Notes: click one of `🧠 Рефлексия`, `📅 План`.

Expected result: each action returns a role-specific artifact and does not deduct extra minutes.

## F. Gating

- Set profile to HR / Assessor with Free or Personal plan and confirm HR buttons are not shown.
- Set profile to HR / Assessor with Premium plan and confirm all 7 HR buttons are shown.
- Set profile to Personal Notes with Free plan and confirm only basic actions are shown.
- Set profile to Personal Notes with Personal plan and confirm personal buttons are shown.
- Set legacy profile PM/BA, Founder, or Student/Researcher with Free plan and confirm only basic actions are shown.
- Set legacy profile PM/BA, Founder, or Student/Researcher with Professional/Premium plan and confirm matching legacy role buttons are shown.
- Confirm users do not see buttons for other profiles.
- If testing callbacks manually, confirm a mismatched profile receives `Эта функция недоступна для вашего профиля.`
- If testing direct HR callbacks manually without Premium, confirm the user receives `HR-функции доступны на тарифе Premium HR.` and no OpenAI processing result is returned.
- If testing Personal callbacks manually without Personal/Premium, confirm the user receives `Эта функция доступна на тарифе Personal.`

## G. History

- Send `/history`.
- Confirm latest successful transcriptions are listed.
- Click `📄 Текст` and confirm full text opens.
- Run one universal action from history.
- Confirm a fresh action panel appears below the result from history.
- Confirm Free users see only basic actions in history.
- Confirm all 7 HR buttons in history are visible only for Premium + `hr_assessor`.
- Confirm Personal buttons in history are visible only for Personal/Premium + `personal_notes`.
- Confirm legacy buttons in history are visible only for Professional/Premium legacy profiles.

## H. Payments/admin

- Send `/buy`.
- Confirm `/buy` shows the user's Telegram ID.
- Confirm `/buy` tells the user to send the selected tariff, payment confirmation, and Telegram ID to the administrator.
- Start a manual payment.
- Click `Я оплатил`.
- As admin, approve the payment.
- As admin, reject another payment.
- As admin, open `/admin`, click `💳 Сменить тариф`, enter a user's Telegram ID, and switch plans.
- Confirm plan assignment reports old/new plan and old/new balance.
- Confirm Free sets balance to 30 minutes and creates `personal_notes` only when no profile exists.
- Confirm Personal sets balance to 300 minutes and `profile_type="personal_notes"`.
- Confirm Premium HR sets balance to 1000 minutes and `profile_type="hr_assessor"`.
- Confirm Professional sets balance to 600 minutes and does not overwrite an existing legacy profile.
- As admin, add minutes manually and confirm this still works as a secondary operation.
- As admin, remove minutes manually and confirm this still works as a secondary operation.
- Confirm Free/Personal + HR profile does not see HR buttons.
- Confirm Premium + HR profile sees all 7 HR buttons.
- Confirm Free + Personal Notes profile sees only basic actions.
- Confirm Personal + Personal Notes profile sees personal buttons.
- As admin, check stats.

Expected result: balances and payment statuses update correctly.

## I. Telegram ID

- Confirm `/start` shows `Ваш Telegram ID: ...`.
- Confirm `/buy` shows `Ваш Telegram ID: ...`.
- Confirm `/balance` shows `Ваш Telegram ID: ...`.
- Confirm no external Telegram ID bot is needed for the payment/admin flow.

## J. Railway

- Deploy the latest branch.
- Confirm deploy logs are clean.
- Confirm migrations have been applied with `alembic upgrade head`.
- Confirm the bot responds after redeploy.
- Send one smoke-test command in Telegram.
