from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.services.text_processing import (
    categorize_personal_note,
    create_acceptance_criteria,
    create_action_plan,
    create_assessment_report,
    create_flashcards,
    create_hr_summary,
    create_idea_brief,
    create_meeting_notes,
    create_mvp_scope,
    create_pitch_summary,
    create_reflection,
    create_research_summary,
    create_study_notes,
    create_tags,
    create_user_story,
    explain_simply,
    extract_business_hypotheses,
    extract_competency_notes,
    extract_risks_assumptions,
    separate_evidence_and_interpretation,
)


TextProcessor = Callable[[str], Awaitable[str]]


@dataclass(frozen=True)
class RoleAction:
    callback_key: str
    label: str
    processor: TextProcessor


RoleActionRows = tuple[tuple[RoleAction, ...], ...]


ROLE_ACTIONS: dict[str, RoleActionRows] = {
    "hr_assessor": (
        (
            RoleAction("hr_summary", "📋 HR-саммари", create_hr_summary),
            RoleAction("competency_notes", "🧠 Компетенции", extract_competency_notes),
        ),
        (
            RoleAction(
                "evidence",
                "⚖️ Факты / интерпретации",
                separate_evidence_and_interpretation,
            ),
            RoleAction("hr_report", "🧾 HR-отчёт", create_assessment_report),
        ),
    ),
    "pm_ba": (
        (
            RoleAction("meeting_notes", "📌 Протокол", create_meeting_notes),
            RoleAction("user_story", "🧩 User Story", create_user_story),
        ),
        (
            RoleAction(
                "acceptance_criteria",
                "☑️ Критерии",
                create_acceptance_criteria,
            ),
            RoleAction("risks_assumptions", "⚠️ Риски", extract_risks_assumptions),
        ),
    ),
    "founder": (
        (
            RoleAction("idea_brief", "🚀 Идея", create_idea_brief),
            RoleAction(
                "business_hypotheses",
                "🧪 Гипотезы",
                extract_business_hypotheses,
            ),
        ),
        (
            RoleAction("mvp_scope", "🧱 MVP", create_mvp_scope),
            RoleAction("pitch_summary", "🎤 Pitch", create_pitch_summary),
        ),
    ),
    "student_researcher": (
        (
            RoleAction("study_notes", "🎓 Конспект", create_study_notes),
            RoleAction(
                "research_summary",
                "🔍 Исследование",
                create_research_summary,
            ),
        ),
        (
            RoleAction("explain_simply", "🧠 Объяснить проще", explain_simply),
            RoleAction("flashcards", "🗂️ Карточки", create_flashcards),
        ),
    ),
    "personal_notes": (
        (
            RoleAction("reflection", "🧠 Рефлексия", create_reflection),
            RoleAction(
                "categorize_note",
                "🗂️ Категории",
                categorize_personal_note,
            ),
        ),
        (
            RoleAction("tags", "🏷️ Теги", create_tags),
            RoleAction("action_plan", "📅 План", create_action_plan),
        ),
    ),
}

ROLE_ACTIONS_BY_CALLBACK_KEY = {
    action.callback_key: (profile_type, action)
    for profile_type, rows in ROLE_ACTIONS.items()
    for row in rows
    for action in row
}


def role_action_keyboard_flags(profile_type: str | None) -> dict[str, bool]:
    return {
        "include_hr_actions": profile_type == "hr_assessor",
        "include_pm_ba_actions": profile_type == "pm_ba",
        "include_founder_actions": profile_type == "founder",
        "include_student_researcher_actions": profile_type == "student_researcher",
        "include_personal_notes_actions": profile_type == "personal_notes",
    }
