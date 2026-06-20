# Manual QA checklist

Use this checklist before a release or Railway redeploy. Run it against a test bot/account when possible.

## A. Smoke test

- Send `/start`.
- Send `/help`.
- Send `/setup`.
- Send `/balance`.
- Send `/history`.

Expected result: commands respond without errors, and existing users are not forced through onboarding by `/start` if onboarding is already completed.

## B. Onboarding

- Run `/setup`.
- Complete onboarding as HR / Assessor.
- Complete onboarding as PM / BA.
- Complete onboarding as Founder.
- Complete onboarding as Student / Researcher.
- Complete onboarding as Personal Notes.
- Check that each completion shows a summary.
- Check in the database that `UserProfile.profile_type` is saved.
- Check that `User.onboarding_completed` and `UserProfile.onboarding_completed` are true after completion.

## C. Voice

- Send a short voice message.
- Confirm the bot transcribes it.
- Confirm minutes are deducted only after successful transcription.
- Confirm failed transcription does not deduct minutes.
- Confirm the transcript is saved with `status="completed"` after success.

## D. Universal actions

For one successful transcription, click:

- `🧹 Очистить`
- `📝 Саммари`
- `✅ Задачи`
- `🔍 Ключевые мысли`
- `❓ Вопросы`
- `📌 Следующие шаги`

Expected result: each action returns a structured artifact and does not deduct extra minutes.

## E. Role-specific actions

For each profile, run at least one role-specific action:

- HR: click one of `📋 HR-саммари`, `🧠 Компетенции`, `⚖️ Факты / интерпретации`, `🧾 HR-отчёт`.
- PM/BA: click one of `📌 Протокол`, `🧩 User Story`, `☑️ Критерии`, `⚠️ Риски`.
- Founder: click one of `🚀 Идея`, `🧪 Гипотезы`, `🧱 MVP`, `🎤 Pitch`.
- Student/Researcher: click one of `🎓 Конспект`, `🔍 Исследование`, `🧠 Объяснить проще`, `🗂️ Карточки`.
- Personal Notes: click one of `🧠 Рефлексия`, `🗂️ Категории`, `🏷️ Теги`, `📅 План`.

Expected result: each action returns a role-specific artifact and does not deduct extra minutes.

## F. Gating

- Set profile to HR / Assessor and confirm only HR role buttons are shown.
- Set profile to PM / BA and confirm only PM/BA role buttons are shown.
- Set profile to Founder and confirm only Founder role buttons are shown.
- Set profile to Student / Researcher and confirm only Student/Researcher role buttons are shown.
- Set profile to Personal Notes and confirm only Personal Notes role buttons are shown.
- Confirm users do not see buttons for other profiles.
- If testing callbacks manually, confirm a mismatched profile receives `Эта функция недоступна для вашего профиля.`

## G. History

- Send `/history`.
- Confirm latest successful transcriptions are listed.
- Click `📄 Текст` and confirm full text opens.
- Run one universal action from history.
- Confirm role-specific buttons in history match the current `UserProfile.profile_type`.

## H. Payments/admin

- Send `/buy`.
- Start a manual payment.
- Click `Я оплатил`.
- As admin, approve the payment.
- As admin, reject another payment.
- As admin, add minutes manually.
- As admin, remove minutes manually.
- As admin, check stats.

Expected result: balances and payment statuses update correctly.

## I. Railway

- Deploy the latest branch.
- Confirm deploy logs are clean.
- Confirm migrations have been applied with `alembic upgrade head`.
- Confirm the bot responds after redeploy.
- Send one smoke-test command in Telegram.
