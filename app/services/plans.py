from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import UserProfile
from app.services.billing import get_or_create_balance, set_balance_minutes


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
    "people": "Люди",
    "strengths_growth": "Сильные стороны / зоны роста",
    "development_recommendations": "Рекомендации по развитию",
    "hr_report": "HR-отчёт",
    "idea_brief": "Идея",
    "business_hypotheses": "Гипотезы",
    "mvp_scope": "MVP Scope",
    "pitch_summary": "Pitch",
    "study_notes": "Конспект",
    "research_summary": "Исследовательское саммари",
    "explain_simply": "Объяснить проще",
    "flashcards": "Карточки",
    "reflection": "Рефлексия",
    "categorize_note": "Категории",
    "tags": "Теги",
    "action_plan": "План действий",
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
    "people",
    "hr_report",
    "competency_notes",
    "evidence",
    "strengths_growth",
    "development_recommendations",
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
    "reflection",
    "categorize_note",
    "tags",
    "action_plan",
]

PLANS: dict[str, PlanConfig] = {
    "free": {
        "label": "Free",
        "display_label": "Free",
        "minutes": 30,
        "duration_days": None,
        "default_profile": "personal_notes",
        "quality": "fast",
        "transcription": "fast",
        "actions": "basic",
        "features": [*CORE_FEATURES],
        "premium_rerun": False,
    },
    "personal": {
        "label": "Personal",
        "display_label": "Personal",
        "minutes": 300,
        "days": 60,
        "duration_days": 60,
        "default_profile": "personal_notes",
        "quality": "fast",
        "transcription": "fast",
        "actions": "personal_notes",
        "price": 199,
        "currency": "RUB",
        "features": [*CORE_FEATURES, "tasks"],
        "premium_rerun": False,
    },
    "professional": {
        "label": "Professional",
        "display_label": "Professional",
        "status": "legacy/internal",
        "minutes": 600,
        "days": 60,
        "duration_days": 60,
        "default_profile": None,
        "quality": "premium",
        "transcription": "premium",
        "actions": "pm_ba",
        "price": 590,
        "currency": "RUB",
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
        "label": "Premium HR",
        "display_label": "Premium HR",
        "minutes": 1000,
        "days": 60,
        "duration_days": 60,
        "default_profile": "hr_assessor",
        "quality": "premium",
        "transcription": "premium",
        "actions": "hr",
        "price": 1290,
        "currency": "RUB",
        "features": "all",
        "premium_rerun": True,
    },
    "premium_trial": {
        "label": "Premium HR Trial",
        "display_label": "Premium HR Trial",
        "stored_plan_key": "premium",
        "minutes": 1000,
        "days": 7,
        "duration_days": 7,
        "default_profile": "hr_assessor",
        "quality": "premium",
        "transcription": "premium",
        "actions": "hr",
        "price": 0,
        "currency": "RUB",
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
        "default_features": [
            "clean",
            "summary",
            "tasks",
            "history",
            "reflection",
            "categorize_note",
            "tags",
            "action_plan",
        ],
        "recommended_plan": "personal",
    },
}


def get_plan(plan_key: str) -> PlanConfig:
    return PLANS.get(plan_key, PLANS["free"])


def get_profile(profile_key: str) -> ProfileConfig | None:
    return PROFILES.get(profile_key)


def get_plan_minutes(plan_key: str) -> int:
    return int(get_plan(plan_key)["minutes"])


def get_default_profile_for_plan(plan_key: str) -> str | None:
    return get_plan(plan_key).get("default_profile")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _compare_now_for_expires_at(expires_at: datetime, now: datetime) -> datetime:
    if expires_at.tzinfo is None and now.tzinfo is not None:
        return now.replace(tzinfo=None)
    if expires_at.tzinfo is not None and now.tzinfo is None:
        return now.replace(tzinfo=timezone.utc)
    return now


def is_plan_expired(user: object, now: datetime | None = None) -> bool:
    plan_key = getattr(user, "current_plan", "free") or "free"
    if plan_key == "free":
        return False

    expires_at = getattr(user, "plan_expires_at", None)
    if expires_at is None:
        return False

    now = _compare_now_for_expires_at(expires_at, now or _now_utc())
    return now > expires_at


def get_effective_plan(user: object, now: datetime | None = None) -> str:
    if is_plan_expired(user, now=now):
        return "free"
    return getattr(user, "current_plan", "free") or "free"


def get_plan_expiration_text(user: object) -> str:
    expires_at = getattr(user, "plan_expires_at", None)
    if expires_at is None:
        plan_key = getattr(user, "current_plan", "free") or "free"
        return "не ограничен" if plan_key == "free" else "не указано"
    return expires_at.strftime("%Y-%m-%d %H:%M UTC")


def calculate_plan_expiration(
    plan_key: str,
    now: datetime | None = None,
    *,
    trial: bool = False,
) -> datetime | None:
    if plan_key == "free":
        return None

    config_key = "premium_trial" if trial and plan_key == "premium" else plan_key
    duration_days = get_plan(config_key).get("duration_days")
    if duration_days is None:
        return None

    return (now or _now_utc()) + timedelta(days=int(duration_days))


async def apply_plan_to_user(
    session: AsyncSession,
    user: object,
    profile: UserProfile | None,
    plan_key: str,
    *,
    trial: bool = False,
) -> dict[str, Any]:
    config_key = "premium_trial" if trial and plan_key == "premium" else plan_key
    if config_key not in PLANS:
        raise ValueError("Unknown plan.")

    plan = get_plan(config_key)
    effective_trial = trial or config_key == "premium_trial"
    stored_plan_key = str(plan.get("stored_plan_key") or plan_key)
    old_plan = getattr(user, "current_plan", None) or "free"
    old_balance = await get_or_create_balance(session, getattr(user, "id"))
    old_balance_minutes = Decimal(old_balance.minutes_remaining)
    package_minutes = int(plan["minutes"])
    new_balance = await set_balance_minutes(session, getattr(user, "id"), package_minutes)

    old_profile_type = profile.profile_type if profile and profile.profile_type else "-"
    default_profile_type = get_default_profile_for_plan(config_key)
    new_profile_type = old_profile_type

    if stored_plan_key in {"personal", "premium"} and default_profile_type:
        if profile is None:
            profile = UserProfile(user_id=getattr(user, "id"))
            session.add(profile)
            await session.flush()
        profile.profile_type = default_profile_type
        new_profile_type = profile.profile_type or "-"
    elif stored_plan_key == "free" and profile is None and default_profile_type:
        profile = UserProfile(user_id=getattr(user, "id"))
        session.add(profile)
        await session.flush()
        profile.profile_type = default_profile_type
        new_profile_type = profile.profile_type or "-"

    setattr(user, "current_plan", stored_plan_key)
    setattr(
        user,
        "plan_expires_at",
        calculate_plan_expiration(stored_plan_key, trial=effective_trial),
    )
    await session.flush()

    return {
        "old_plan": old_plan,
        "new_plan": stored_plan_key,
        "old_balance": old_balance_minutes,
        "new_balance": Decimal(new_balance.minutes_remaining),
        "old_profile": old_profile_type,
        "new_profile": new_profile_type,
        "plan_expires_at": getattr(user, "plan_expires_at", None),
        "minutes_granted": package_minutes,
        "trial": effective_trial,
    }


def get_text_model_for_plan(plan_key: str, profile_type: str | None = None) -> str:
    settings = get_settings()
    if plan_key == "free":
        return settings.text_model_free
    if plan_key == "personal":
        return settings.text_model_paid
    if plan_key == "professional":
        return settings.text_model_legacy
    if plan_key == "premium":
        if profile_type == "hr_assessor":
            return settings.text_model_hr
        return settings.text_model_paid
    return settings.text_model or settings.text_model_paid


def get_transcription_model_for_plan(
    plan_key: str,
    profile_type: str | None = None,
) -> str:
    settings = get_settings()
    if plan_key in {"free", "personal"}:
        return settings.transcription_model_fast
    if plan_key in {"professional", "premium"}:
        return settings.transcription_model_premium
    return settings.transcription_model_fast or settings.transcription_model


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
    plan_key = get_effective_plan(user)
    profile = getattr(user, "__dict__", {}).get("profile")
    profile_key = getattr(profile, "profile_type", None) or ""
    return feature_key in get_available_features(profile_key, plan_key)


def get_text_model_for_user(user: object) -> str:
    plan_key = get_effective_plan(user)
    profile = getattr(user, "__dict__", {}).get("profile")
    profile_key = getattr(profile, "profile_type", None)
    return get_text_model_for_plan(plan_key, profile_key)


def get_transcription_model_for_user(user: object) -> str:
    plan_key = get_effective_plan(user)
    profile = getattr(user, "__dict__", {}).get("profile")
    profile_key = getattr(profile, "profile_type", None)
    return get_transcription_model_for_plan(plan_key, profile_key)


def can_use_premium_rerun(user: object) -> bool:
    plan_key = get_effective_plan(user)
    return bool(get_plan(plan_key)["premium_rerun"])
