from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.user import user_menu_keyboard
from app.config import get_settings
from app.db.models import User
from app.services.billing import get_or_create_balance
from app.services.onboarding import upsert_user_profile
from app.services.users import get_or_create_user


router = Router(name="onboarding")


class OnboardingStates(StatesGroup):
    waiting_for_goal = State()
    waiting_for_output = State()
    waiting_for_source = State()
    waiting_for_quality = State()
    waiting_for_frequency = State()


def onboarding_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Начать настройку",
                    callback_data="onboarding:start",
                ),
                InlineKeyboardButton(
                    text="⏭ Пропустить",
                    callback_data="onboarding:skip",
                ),
            ]
        ]
    )


def onboarding_finished_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Продолжить",
                    callback_data="onboarding:continue",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔁 Пройти настройку заново",
                    callback_data="onboarding:restart",
                )
            ],
        ]
    )


def _answer_keyboard(prefix: str, options: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"onboarding:{prefix}:{value}",
                )
            ]
            for label, value in options
        ]
    )


async def prompt_onboarding_start(message: Message) -> None:
    await message.answer(
        "Давайте быстро настроим бота под ваши задачи. Это займёт меньше минуты.",
        reply_markup=onboarding_start_keyboard(),
    )


async def start_onboarding(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(OnboardingStates.waiting_for_goal)
    await message.answer(
        "Для чего вы чаще всего будете использовать голосовые заметки?",
        reply_markup=_answer_keyboard(
            "goal",
            [
                ("📋 Оценка персонала / интервью", "hr_assessor"),
                ("🧩 Проекты / требования / встречи", "pm_ba"),
                ("🚀 Идеи для бизнеса / продукта", "founder"),
                ("🎓 Учёба / исследования", "student_researcher"),
                ("🧠 Личные заметки", "personal_notes"),
            ],
        ),
    )


async def _send_output_question(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OnboardingStates.waiting_for_output)
    await callback.message.answer(
        "Какой результат вы чаще всего хотите получать после голосовой заметки?",
        reply_markup=_answer_keyboard(
            "output",
            [
                ("Только аккуратный текст", "clean_text"),
                ("Краткое summary", "summary"),
                ("Список задач", "tasks"),
                ("Структурированный отчёт", "structured_report"),
                ("Требования / user stories", "requirements"),
                ("Риски и вопросы для уточнения", "risks_questions"),
            ],
        ),
    )


async def _send_source_question(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OnboardingStates.waiting_for_source)
    await callback.message.answer(
        "Что чаще всего будет в голосовых?",
        reply_markup=_answer_keyboard(
            "source",
            [
                ("Мои личные мысли", "personal_thoughts"),
                ("Итоги встреч", "meeting_notes"),
                ("Интервью с людьми", "interviews"),
                ("Обсуждение задач с командой", "team_tasks"),
                ("Идеи продукта / бизнеса", "product_ideas"),
                ("Учебные материалы / лекции", "lectures"),
            ],
        ),
    )


async def _send_quality_question(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OnboardingStates.waiting_for_quality)
    await callback.message.answer(
        "Что для вас важнее?",
        reply_markup=_answer_keyboard(
            "quality",
            [
                ("💸 Дешевле, можно чуть менее точно", "cheap"),
                ("⚖️ Баланс цены и качества", "balanced"),
                ("🎯 Максимальная точность", "maximum_accuracy"),
            ],
        ),
    )


async def _send_frequency_question(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OnboardingStates.waiting_for_frequency)
    await callback.message.answer(
        "Сколько голосовых заметок вы примерно будете отправлять?",
        reply_markup=_answer_keyboard(
            "frequency",
            [
                ("Несколько в неделю", "low"),
                ("1–5 в день", "medium"),
                ("5–15 в день", "high"),
                ("Много, почти каждый рабочий день", "power"),
                ("Пока не знаю", "unknown"),
            ],
        ),
    )


async def _get_or_create_current_user(
    message_or_callback: Message | CallbackQuery,
    session: AsyncSession,
) -> tuple[User, bool]:
    telegram_user = message_or_callback.from_user
    settings = get_settings()
    user = await get_or_create_user(
        session,
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        language_code=telegram_user.language_code,
        admin_telegram_ids=settings.admin_telegram_ids,
    )
    await get_or_create_balance(session, user.id)
    return user, settings.is_admin(telegram_user.id)


@router.message(Command("setup"))
async def setup_command(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return
    await _get_or_create_current_user(message, session)
    await start_onboarding(message, state)


@router.callback_query(F.data == "onboarding:start")
async def onboarding_start_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message is not None:
        await start_onboarding(callback.message, state)


@router.callback_query(F.data == "onboarding:restart")
async def onboarding_restart_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message is not None:
        await start_onboarding(callback.message, state)


@router.callback_query(F.data == "onboarding:skip")
async def onboarding_skip_callback(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await callback.answer()
    user, is_admin = await _get_or_create_current_user(callback, session)
    await upsert_user_profile(
        session,
        user,
        {
            "goal": "personal_notes",
            "preferred_output": "summary",
            "audio_source": "personal_thoughts",
            "quality_preference": "cheap",
            "usage_frequency": "unknown",
        },
    )
    if not user.current_plan:
        user.current_plan = "free"
    user.transcription_quality = "fast"
    await session.flush()
    await state.clear()
    await callback.message.answer(
        "Настройку пропустили. Я буду использовать базовый профиль личных заметок.",
        reply_markup=user_menu_keyboard(is_admin=is_admin),
    )


@router.callback_query(OnboardingStates.waiting_for_goal, F.data.startswith("onboarding:goal:"))
async def onboarding_goal_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    value = (callback.data or "").split(":", maxsplit=2)[2]
    await state.update_data(goal=value)
    await _send_output_question(callback, state)


@router.callback_query(
    OnboardingStates.waiting_for_output,
    F.data.startswith("onboarding:output:"),
)
async def onboarding_output_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    value = (callback.data or "").split(":", maxsplit=2)[2]
    await state.update_data(preferred_output=value)
    await _send_source_question(callback, state)


@router.callback_query(
    OnboardingStates.waiting_for_source,
    F.data.startswith("onboarding:source:"),
)
async def onboarding_source_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    value = (callback.data or "").split(":", maxsplit=2)[2]
    await state.update_data(audio_source=value)
    await _send_quality_question(callback, state)


@router.callback_query(
    OnboardingStates.waiting_for_quality,
    F.data.startswith("onboarding:quality:"),
)
async def onboarding_quality_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    value = (callback.data or "").split(":", maxsplit=2)[2]
    await state.update_data(quality_preference=value)
    await _send_frequency_question(callback, state)


@router.callback_query(
    OnboardingStates.waiting_for_frequency,
    F.data.startswith("onboarding:frequency:"),
)
async def onboarding_frequency_callback(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await callback.answer()
    value = (callback.data or "").split(":", maxsplit=2)[2]
    await state.update_data(usage_frequency=value)
    answers = await state.get_data()
    user, _ = await _get_or_create_current_user(callback, session)
    _, summary = await upsert_user_profile(session, user, answers)
    await state.clear()
    await callback.message.answer(summary, reply_markup=onboarding_finished_keyboard())


@router.callback_query(F.data == "onboarding:continue")
async def onboarding_continue_callback(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await callback.answer()
    await state.clear()
    _, is_admin = await _get_or_create_current_user(callback, session)
    await callback.message.answer(
        "Готово. Можно отправлять voice-сообщение.",
        reply_markup=user_menu_keyboard(is_admin=is_admin),
    )
