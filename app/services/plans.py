from typing import Any

from app.config import get_settings


PlanConfig = dict[str, Any]
ProfileConfig = dict[str, Any]

FEATURE_DISPLAY_LABELS = {
    "clean": "Очистить",
    "summary": "Саммари",
    "tasks": "Задачи",
    "key_points": "Ключевые мысли",
    "questions": "Вопросы",
    "next_steps": "Следующие шаги",
    "meeting_notes": "Протокол",
    "user_story": "User Story",
    "acceptance_criteria": "Критерии приёмки",
    "risks_assumptions": "Риски и допущения",
    "hr_summary": "HR-саммари",
    "competency_notes": "Компетенции",
    "evidence": "Факты / интерпретации",
    "hr_report": "HR-отчёт",
    "idea_brief": "Идея",
    "business_hypotheses": "Гипотезы",
    "mvp_scope": "MVP Scope",
    "pitch_summary": "Pitch",
    "study_notes": "Конспект",
    "research_summary": "Исследовательское саммари",
    "explain_simply": "Объяснить проще",
    "flashcards": "Карточки",
}

CORE_FEATURES = [
    "clean",
    "summary",
    "history",
    "key_points",
    "questions",
    "next_steps",
]

ALL_FEATURES = [
    "clean",
    "summary",
    "tasks",
    "history",
    "meeting_notes",
    "role_report",
    "hr_summary",
    "hr_report",
    "competency_notes",
    "evidence",
    "follow_up",
    "user_story",
    "acceptance_criteria",
    "risks_assumptions",
    "risks",
    "idea_brief",
    "business_hypotheses",
    "mvp_scope",
    "next_steps",
    "pitch_summary",
    "key_points",
    "questions",
    "research_summary",
    "explain_simply",
    "flashcards",
    "study_notes",
]

PLANS: dict[str, PlanConfig] = {
    "free": {
        "minutes": 30,
        "quality": "fast",
        "features": [*CORE_FEATURES],
        "premium_rerun": False,
    },
    "personal": {
        "minutes": 300,
        "quality": "fast",
        "features": [*CORE_FEATURES, "tasks"],
        "premium_rerun": False,
    },
    "professional": {
        "minutes": 600,
        "quality": "fast",
        "features": [
            *CORE_FEATURES,
            "tasks",
            "meeting_notes",
            "role_report",
            "follow_up",
            "user_story",
            "acceptance_criteria",
            "risks_assumptions",
            "risks",
        ],
        "premium_rerun": True,
    },
    "premium": {
        "minutes": 1000,
        "quality": "premium",
        "features": "all",
        "premium_rerun": True,
    },
}

PROFILES: dict[str, ProfileConfig] = {
    "hr_assessor": {
        "label": "HR / оценка персонала",
        "default_features": [
            "clean",
            "summary",
            "hr_summary",
            "hr_report",
            "competency_notes",
            "evidence",
            "risks",
            "follow_up",
        ],
        "recommended_plan": "professional",
    },
    "pm_ba": {
        "label": "PM / бизнес-аналитик",
        "default_features": [
            "clean",
            "summary",
            "tasks",
            "meeting_notes",
            "user_story",
            "acceptance_criteria",
            "risks_assumptions",
            "risks",
            "follow_up",
        ],
        "recommended_plan": "professional",
    },
    "founder": {
        "label": "Основатель / предприниматель",
        "default_features": [
            "clean",
            "summary",
            "idea_brief",
            "business_hypotheses",
            "mvp_scope",
            "risks",
            "next_steps",
            "pitch_summary",
        ],
        "recommended_plan": "professional",
    },
    "student_researcher": {
        "label": "Студент / исследователь",
        "default_features": [
            "clean",
            "summary",
            "key_points",
            "questions",
            "study_notes",
            "research_summary",
            "explain_simply",
            "flashcards",
        ],
        "recommended_plan": "personal",
    },
    "personal_notes": {
        "label": "Личные заметки",
        "default_features": ["clean", "summary", "tasks", "history"],
        "recommended_plan": "personal",
    },
}


def get_plan(plan_key: str) -> PlanConfig:
    return PLANS.get(plan_key, PLANS["free"])


def get_profile(profile_key: str) -> ProfileConfig | None:
    return PROFILES.get(profile_key)


def _normalize_features(features: list[str] | str) -> list[str]:
    if features == "all":
        return list(ALL_FEATURES)
    return list(features)


def _deduplicate(features: list[str]) -> list[str]:
    return list(dict.fromkeys(features))


def get_available_features(profile_key: str, plan_key: str) -> list[str]:
    plan = get_plan(plan_key)
    plan_features = _normalize_features(plan["features"])
    if plan["features"] == "all":
        return plan_features

    profile = get_profile(profile_key)
    profile_features = profile["default_features"] if profile else []
    return _deduplicate([*plan_features, *profile_features])


def has_feature(user: object, feature_key: str) -> bool:
    plan_key = getattr(user, "current_plan", "free") or "free"
    profile = getattr(user, "__dict__", {}).get("profile")
    profile_key = getattr(profile, "profile_type", None) or ""
    return feature_key in get_available_features(profile_key, plan_key)


def get_transcription_model_for_user(user: object) -> str:
    settings = get_settings()
    plan_key = getattr(user, "current_plan", "free") or "free"
    quality = getattr(user, "transcription_quality", "fast") or "fast"
    if quality == "premium" or plan_key == "premium":
        return settings.transcription_model_premium
    return settings.transcription_model_fast


def can_use_premium_rerun(user: object) -> bool:
    plan_key = getattr(user, "current_plan", "free") or "free"
    return bool(get_plan(plan_key)["premium_rerun"])
