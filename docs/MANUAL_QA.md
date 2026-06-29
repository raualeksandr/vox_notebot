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
- Confirm `/start` says users can send voice notes or audio files.
- Confirm `/start` shows support contact `@raugestalt` or the configured `SUPPORT_CONTACT_USERNAME`.
- Confirm `/start` shows the user's Telegram ID.
- Run `/help` and confirm it lists supported audio formats: mp3, m4a, wav, ogg.
- Run `/setup` and confirm it says setup is no longer required.
- Confirm `/setup` points users to `/buy` and the support contact.
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

## C2. External audio files

- Send a small `.mp3` as Telegram audio and confirm transcription works.
- Send a small `.m4a` as Telegram audio and confirm transcription works.
- Send a small `.wav` as Telegram audio and confirm transcription works.
- Send a small `.ogg` as Telegram audio and confirm transcription works.
- Send an audio file as Telegram document. If Telegram provides no duration, confirm the bot refuses safely with a clear message and does not call OpenAI.
- Send a non-audio document and confirm the bot says only mp3, m4a, wav, and ogg are supported.
- Send an audio file larger than `MAX_AUDIO_FILE_SIZE_MB` and confirm the bot refuses before OpenAI is called.
- Confirm successful external audio uses the same balance deduction, transcript saving, and action keyboard as voice notes.

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
- If testing direct HR callbacks manually without Premium, confirm the user receives `HR-функции доступны на тарифе Premium HR. Откройте /buy или напишите @raugestalt, чтобы получить доступ.` and no OpenAI processing result is returned.
- If testing Personal callbacks manually without Personal/Premium, confirm the user receives `Эта функция доступна на тарифе Personal. Откройте /buy или напишите @raugestalt, чтобы получить доступ.`

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

- Before testing subscriptions on a fresh environment, apply migrations with `alembic upgrade head`.
- Send `/buy`.
- Confirm `/buy` starts with `💳 Тарифы VoxNoteBot`.
- Confirm `/buy` shows Free, Personal, and Premium HR as public tariffs.
- Confirm Professional is not shown as a primary public tariff.
- Confirm `/buy` shows the user's Telegram ID.
- Confirm `/buy` shows the payment instruction steps.
- Confirm `/buy` shows configured SBP/payment details, or tells the user to contact `@raugestalt` / `SUPPORT_CONTACT_USERNAME` when details are not configured.
- Confirm `/buy` tells the user to send the selected tariff, payment confirmation, and Telegram ID to the administrator.
- Confirm paywall/upgrade messages direct the user to `/buy`.
- Start a manual payment.
- Click `Я оплатил`.
- As admin, approve the payment.
- As admin, reject another payment.
- As admin, open `/admin`, click `💳 Сменить тариф`, enter a user's Telegram ID, and switch plans.
- Confirm plan assignment reports old/new plan and old/new balance.
- Confirm Free sets balance to 30 minutes and creates `personal_notes` only when no profile exists.
- Confirm Personal sets balance to 300 minutes, `profile_type="personal_notes"`, and `plan_expires_at` about 60 days ahead.
- Confirm Premium HR sets balance to 1000 minutes, `profile_type="hr_assessor"`, and `plan_expires_at` about 60 days ahead.
- Confirm Professional sets balance to 600 minutes, sets `plan_expires_at` about 60 days ahead, and does not overwrite an existing legacy profile.
- Confirm Free has no expiration.
- Confirm existing paid users with `plan_expires_at = NULL` are treated as active for backward compatibility.
- As admin, open `/admin`, click `🎁 Выдать Premium HR Trial`, enter a user's Telegram ID, and confirm it grants 1000 minutes, stores `current_plan="premium"`, sets `profile_type="hr_assessor"`, and sets `plan_expires_at` about 7 days ahead.
- Confirm `/balance` for that user shows `current_plan: premium`, `plan_expires_at`, and no expired warning.
- Confirm Premium HR Trial users see all 7 HR buttons while the trial is active.
- Manually set a paid user's `plan_expires_at` to a past datetime in the test database, then confirm `/balance` shows `effective_plan: free` and `Тариф истёк. Сейчас доступен Free-режим.`
- Confirm the expired user sees only Free/basic buttons after transcription and in `/history`.
- Confirm direct HR callbacks for an expired Premium HR user return the Premium HR upgrade message and do not call OpenAI.
- Confirm an old paid user with `plan_expires_at = NULL` remains active for backward compatibility.
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
