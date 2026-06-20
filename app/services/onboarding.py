from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, UserProfile
from app.services.plans import FEATURE_DISPLAY_LABELS, get_available_features, get_profile


GOALS = (
    "hr_assessor",
    "pm_ba",
    "founder",
    "student_researcher",
    "personal_notes",
)

PUBLIC_ONBOARDING_GOALS = {
    "hr_assessor",
    "personal_notes",
}

PREFERRED_OUTPUTS = (
    "clean_text",
    "summary",
    "tasks",
    "structured_report",
    "requirements",
    "risks_questions",
)

AUDIO_SOURCES = (
    "personal_thoughts",
    "meeting_notes",
    "interviews",
    "team_tasks",
    "product_ideas",
    "lectures",
)

QUALITY_PREFERENCES = (
    "cheap",
    "balanced",
    "maximum_accuracy",
)

USAGE_FREQUENCIES = (
    "low",
    "medium",
    "high",
    "power",
    "unknown",
)

PLAN_LABELS = {
    "free": "Бесплатный",
    "personal": "Личный",
    "professional": "Профессиональный",
    "premium": "Премиум",
}

QUALITY_LABELS = {
    "fast": "быстрый",
    "premium": "премиум",
}

FEATURE_LABELS = {
    **FEATURE_DISPLAY_LABELS,
    "history": "история транскрипций",
    "meeting_notes": "Протокол",
    "role_report": "ролевой отчет",
    "follow_up": "follow-up",
    "user_story": "User Story",
    "acceptance_criteria": "Критерии приёмки",
    "risks_assumptions": "Риски и допущения",
    "risks": "риски",
    "idea_brief": "Идея",
    "business_hypotheses": "Гипотезы",
    "mvp_scope": "MVP Scope",
    "pitch_summary": "Pitch",
}


def _answer(answers: dict[str, Any], key: str) -> str:
    value = answers.get(key)
    return value if isinstance(value, str) else ""


def calculate_profile(answers: dict[str, Any]) -> str:
    goal = _answer(answers, "goal")
    preferred_output = _answer(answers, "preferred_output")
    audio_source = _answer(answers, "audio_source")
    quality_preference = _answer(answers, "quality_preference")

    if goal in PUBLIC_ONBOARDING_GOALS:
        return goal

    scores = dict.fromkeys(GOALS, 0)

    scores["hr_assessor"] += 3 if goal == "hr_assessor" else 0
    scores["hr_assessor"] += 2 if audio_source == "interviews" else 0
    scores["hr_assessor"] += 2 if preferred_output == "structured_report" else 0
    scores["hr_assessor"] += 1 if quality_preference == "maximum_accuracy" else 0

    scores["pm_ba"] += 3 if goal == "pm_ba" else 0
    scores["pm_ba"] += 2 if preferred_output == "requirements" else 0
    scores["pm_ba"] += 2 if audio_source == "team_tasks" else 0
    scores["pm_ba"] += 1 if preferred_output == "tasks" else 0
    scores["pm_ba"] += 1 if audio_source == "meeting_notes" else 0

    scores["founder"] += 3 if goal == "founder" else 0
    scores["founder"] += 2 if audio_source == "product_ideas" else 0
    scores["founder"] += 2 if preferred_output == "risks_questions" else 0
    scores["founder"] += 1 if preferred_output == "structured_report" else 0

    scores["student_researcher"] += 3 if goal == "student_researcher" else 0
    scores["student_researcher"] += 2 if audio_source == "lectures" else 0
    scores["student_researcher"] += 1 if preferred_output == "summary" else 0
    scores["student_researcher"] += 1 if preferred_output == "clean_text" else 0

    scores["personal_notes"] += 3 if goal == "personal_notes" else 0
    scores["personal_notes"] += 2 if audio_source == "personal_thoughts" else 0
    scores["personal_notes"] += 1 if preferred_output == "clean_text" else 0
    scores["personal_notes"] += 1 if preferred_output == "summary" else 0
    scores["personal_notes"] += 1 if preferred_output == "tasks" else 0

    highest_score = max(scores.values())
    tied_profiles = [
        profile_type
        for profile_type, score in scores.items()
        if score == highest_score
    ]
    if goal in GOALS and goal in tied_profiles:
        return goal
    if highest_score == 0:
        return "personal_notes"
    return tied_profiles[0]


def recommend_plan(profile_type: str, answers: dict[str, Any]) -> str:
    preferred_output = _answer(answers, "preferred_output")
    usage_frequency = _answer(answers, "usage_frequency") or "unknown"
    quality_preference = _answer(answers, "quality_preference")
    is_free_candidate = usage_frequency in {"low", "unknown"} and preferred_output in {
        "clean_text",
        "summary",
    }

    if (
        usage_frequency == "power"
        or quality_preference == "maximum_accuracy"
        and usage_frequency in {"high", "power"}
    ):
        return "premium"

    if (
        profile_type in {"hr_assessor", "pm_ba", "founder"}
        or usage_frequency == "high"
        or preferred_output
        in {"structured_report", "requirements", "risks_questions"}
    ):
        return "professional"

    if is_free_candidate:
        return "free"

    if profile_type in {"personal_notes", "student_researcher"}:
        return "personal"

    if usage_frequency in {"low", "medium"}:
        return "personal"

    return "personal"


def recommend_quality(answers: dict[str, Any], recommended_plan: str) -> str:
    if recommended_plan == "premium":
        return "premium"
    return "fast"


def build_onboarding_summary(
    profile_type: str,
    recommended_plan: str,
    quality: str,
    answers: dict[str, Any],
) -> str:
    profile = get_profile(profile_type) or {}
    profile_label = profile.get("label", profile_type)
    plan_label = PLAN_LABELS.get(recommended_plan, recommended_plan)
    quality_label = QUALITY_LABELS.get(quality, quality)
    features = get_available_features(profile_type, recommended_plan)
    feature_labels = [
        FEATURE_LABELS.get(feature_key, feature_key)
        for feature_key in features[:8]
    ]
    useful_features = ", ".join(feature_labels)

    return (
        "Результат настройки:\n"
        f"- Профиль: {profile_label}\n"
        f"- Рекомендованный план: {plan_label}\n"
        f"- Режим качества: {quality_label}\n"
        f"- Полезные функции: {useful_features}"
    )


async def upsert_user_profile(
    session: AsyncSession,
    user: User,
    answers: dict[str, Any],
) -> tuple[UserProfile, str]:
    profile_type = calculate_profile(answers)
    recommended_plan = recommend_plan(profile_type, answers)
    quality = recommend_quality(answers, recommended_plan)

    result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    user_profile = result.scalar_one_or_none()
    if user_profile is None:
        user_profile = UserProfile(user_id=user.id)
        session.add(user_profile)

    user_profile.profile_type = profile_type
    user_profile.primary_goal = _answer(answers, "goal") or None
    user_profile.preferred_output = _answer(answers, "preferred_output") or None
    user_profile.audio_source = _answer(answers, "audio_source") or None
    user_profile.quality_preference = _answer(answers, "quality_preference") or None
    user_profile.usage_frequency = _answer(answers, "usage_frequency") or None
    user_profile.recommended_plan = recommended_plan
    user_profile.onboarding_completed = True

    user.onboarding_completed = True
    if not user.current_plan:
        user.current_plan = "free"
    user.transcription_quality = "premium" if user.current_plan == "premium" else "fast"

    await session.flush()
    summary = build_onboarding_summary(
        profile_type,
        recommended_plan,
        quality,
        answers,
    )
    return user_profile, summary
