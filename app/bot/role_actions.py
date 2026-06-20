from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.services.text_processing import (
    categorize_personal_note,
    create_acceptance_criteria,
    create_action_plan,
    create_assessment_report,
    create_development_recommendations,
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
    extract_people,
    extract_risks_assumptions,
    extract_strengths_growth_zones,
    separate_evidence_and_interpretation,
)


TextProcessor = Callable[[str], Awaitable[str]]


@dataclass(frozen=True)
class RoleAction:
    callback_key: str
    label: str
    processor: TextProcessor


RoleActionRows = tuple[tuple[RoleAction, ...], ...]

BASIC_UNIVERSAL_CALLBACKS = {
    "text:clean",
    "text:summary",
}
PERSONAL_NOTES_UNIVERSAL_CALLBACKS = {
    *BASIC_UNIVERSAL_CALLBACKS,
    "text:tasks",
}
ALL_UNIVERSAL_CALLBACKS = {
    *PERSONAL_NOTES_UNIVERSAL_CALLBACKS,
    "key_points",
    "questions",
    "next_steps",
}
LEGACY_PROFILE_TYPES = {"pm_ba", "founder", "student_researcher"}
PERSONAL_NOTES_ROLE_CALLBACKS = {
    "reflection",
    "action_plan",
}


ROLE_ACTIONS: dict[str, RoleActionRows] = {
    "hr_assessor": (
        (
            RoleAction("hr_summary", "📋 HR-саммари", create_hr_summary),
        ),
        (
            RoleAction(
                "evidence",
                "⚖️ Факты / интерпретации",
                separate_evidence_and_interpretation,
            ),
        ),
        (
            RoleAction("people", "👥 Люди", extract_people),
            RoleAction("competency_notes", "🧠 Компетенции", extract_competency_notes),
        ),
        (
            RoleAction(
                "strengths_growth",
                "💪 Сильные стороны / зоны роста",
                extract_strengths_growth_zones,
            ),
        ),
        (
            RoleAction(
                "development_recommendations",
                "📈 Рекомендации",
                create_development_recommendations,
            ),
        ),
        (
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


def get_visible_universal_callback_keys(
    profile_type: str | None,
    plan_key: str | None,
) -> set[str]:
    plan_key = plan_key or "free"
    if plan_key == "free":
        return set(BASIC_UNIVERSAL_CALLBACKS)
    if profile_type == "personal_notes" and plan_key in {"personal", "premium"}:
        return set(PERSONAL_NOTES_UNIVERSAL_CALLBACKS)
    if profile_type == "hr_assessor":
        return set(BASIC_UNIVERSAL_CALLBACKS)
    if profile_type in LEGACY_PROFILE_TYPES and plan_key in {"professional", "premium"}:
        return set(ALL_UNIVERSAL_CALLBACKS)
    return set(BASIC_UNIVERSAL_CALLBACKS)


def can_use_universal_callback(
    callback_key: str,
    profile_type: str | None,
    plan_key: str | None,
) -> bool:
    return callback_key in get_visible_universal_callback_keys(profile_type, plan_key)


def can_use_role_actions(profile_type: str | None, plan_key: str | None) -> bool:
    plan_key = plan_key or "free"
    if profile_type == "hr_assessor":
        return plan_key == "premium"
    if profile_type == "personal_notes":
        return plan_key in {"personal", "premium"}
    if profile_type in LEGACY_PROFILE_TYPES:
        return plan_key in {"professional", "premium"}
    return False


def can_use_role_callback(
    callback_key: str,
    profile_type: str | None,
    plan_key: str | None,
) -> bool:
    return can_use_role_actions(profile_type, plan_key)


def role_action_denial_message(profile_type: str) -> str:
    if profile_type == "hr_assessor":
        return "HR-функции доступны на тарифе Premium HR."
    if profile_type == "personal_notes":
        return "Эта функция доступна на тарифе Personal."
    return "Эта функция недоступна на вашем тарифе."


def role_action_keyboard_flags(
    profile_type: str | None,
    plan_key: str | None = None,
) -> dict[str, bool]:
    has_role_access = can_use_role_actions(profile_type, plan_key)
    return {
        "include_hr_actions": has_role_access and profile_type == "hr_assessor",
        "include_pm_ba_actions": has_role_access and profile_type == "pm_ba",
        "include_founder_actions": has_role_access and profile_type == "founder",
        "include_student_researcher_actions": (
            has_role_access and profile_type == "student_researcher"
        ),
        "include_personal_notes_actions": (
            has_role_access and profile_type == "personal_notes"
        ),
    }
