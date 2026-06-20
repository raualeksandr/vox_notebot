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

## E. Role-specific actions

For each eligible paid profile, run at least one role-specific action:

- Premium HR: click one of `📋 HR-саммари`, `🧠 Компетенции`, `⚖️ Факты / интерпретации`, `🧾 HR-отчёт`.
- Professional/Premium PM/BA: click one of `📌 Протокол`, `🧩 User Story`, `☑️ Критерии`, `⚠️ Риски`.
- Professional/Premium Founder: click one of `🚀 Идея`, `🧪 Гипотезы`, `🧱 MVP`, `🎤 Pitch`.
- Professional/Premium Student/Researcher: click one of `🎓 Конспект`, `🔍 Исследование`, `🧠 Объяснить проще`, `🗂️ Карточки`.
- Personal/Premium Personal Notes: click one of `🧠 Рефлексия`, `📅 План`.

Expected result: each action returns a role-specific artifact and does not deduct extra minutes.

## F. Gating

- Set profile to HR / Assessor with Free plan and confirm HR buttons are not shown.
- Set profile to HR / Assessor with Premium plan and confirm HR buttons are shown.
- Set profile to Personal Notes with Free plan and confirm only basic actions are shown.
- Set profile to Personal Notes with Personal plan and confirm personal buttons are shown.
- Set legacy profile PM/BA, Founder, or Student/Researcher with Free plan and confirm only basic actions are shown.
- Set legacy profile PM/BA, Founder, or Student/Researcher with Professional/Premium plan and confirm matching legacy role buttons are shown.
- Confirm users do not see buttons for other profiles.
- If testing callbacks manually, confirm a mismatched profile receives `Эта функция недоступна для вашего профиля.`
- If testing HR callbacks manually without Premium, confirm the user receives `HR-функции доступны на тарифе Premium HR.`
- If testing Personal callbacks manually without Personal/Premium, confirm the user receives `Эта функция доступна на тарифе Personal.`

## G. History

- Send `/history`.
- Confirm latest successful transcriptions are listed.
- Click `📄 Текст` and confirm full text opens.
- Run one universal action from history.
- Confirm Free users see only basic actions in history.
- Confirm HR buttons in history are visible only for Premium + `hr_assessor`.
- Confirm Personal buttons in history are visible only for Personal/Premium + `personal_notes`.
- Confirm legacy buttons in history are visible only for Professional/Premium legacy profiles.

## H. Payments/admin

- Send `/buy`.
- Start a manual payment.
- Click `Я оплатил`.
- As admin, approve the payment.
- As admin, reject another payment.
- As admin, add minutes manually.
- As admin, remove minutes manually.
- As admin, open `/admin`, click `💳 Сменить тариф`, enter a user's Telegram ID, and switch plans.
- Confirm Free + HR profile does not see HR buttons.
- Confirm Premium + HR profile sees HR buttons.
- Confirm Free + Personal Notes profile sees only basic actions.
- Confirm Personal + Personal Notes profile sees personal buttons.
- As admin, check stats.

Expected result: balances and payment statuses update correctly.

## I. Railway

- Deploy the latest branch.
- Confirm deploy logs are clean.
- Confirm migrations have been applied with `alembic upgrade head`.
- Confirm the bot responds after redeploy.
- Send one smoke-test command in Telegram.
