# Release notes

## Current MVP

This MVP is a Railway-ready Telegram bot for voice notes, structured text processing, onboarding, profile-specific workflows, and manual minute billing.

Included:

- Voice transcription through OpenAI.
- Minute balance accounting.
- Manual payment claims with admin approve/reject flow.
- Role onboarding through `/start` and `/setup`.
- Five profile modes:
  - HR / Assessor
  - PM / BA
  - Founder
  - Student / Researcher
  - Personal Notes
- Universal text actions:
  - Clean
  - Summary
  - Tasks
  - Key Points
  - Questions
  - Next Steps
- Profile-specific actions gated by `UserProfile.profile_type`.
- `/history` for recent successful transcriptions.
- Text-processing guardrails for artifact-style outputs, unsupported-fact prevention, and conversational-tail suppression.
- Railway deployment configuration.

Not included as finished user-facing features:

- Telegram Stars.
- Premium transcription rerun.
- Bear, Notion, Google Docs, or other exports.
- Automated test suite.

## Next steps

- Separate dev and production Telegram bots.
- Add automated tests for:
  - onboarding scoring
  - profile gating
  - callback routing
  - billing edge cases
  - history actions
- Continue role action refactoring if more profiles or actions are added.
- Add premium transcription rerun when pricing and UX are finalized.
- Add export integrations later:
  - Notion
  - Google Docs
  - Bear
- Add Telegram Stars later if the payment model changes.
