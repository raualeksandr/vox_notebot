from app.config import get_settings
from app.services.openai_client import get_openai_client


async def _process_text(text: str, instructions: str) -> str:
    source_text = text.strip()
    if not source_text:
        raise ValueError("Text is empty.")

    settings = get_settings()
    client = get_openai_client()
    response = await client.responses.create(
        model=settings.text_model,
        instructions=instructions,
        input=source_text,
    )
    result = response.output_text.strip()
    if not result:
        raise RuntimeError("OpenAI returned an empty text result.")
    return result


async def clean_text(text: str) -> str:
    return await _process_text(
        text,
        (
            "Очисти русскоязычную расшифровку устной речи. Исправь пунктуацию, "
            "явные опечатки и ошибки распознавания, убери слова-паразиты и "
            "ненужные повторы. Сохрани исходный смысл, тон и все факты. "
            "Не добавляй новые сведения, комментарии или заголовки. "
            "Верни только очищенный текст."
        ),
    )


async def summarize_text(text: str) -> str:
    return await _process_text(
        text,
        (
            "Сделай короткое структурированное резюме русскоязычного текста. "
            "Сначала укажи главную мысль, затем перечисли только ключевые пункты. "
            "Не добавляй фактов, которых нет в исходном тексте. "
            "Верни только готовое резюме."
        ),
    )


async def extract_tasks(text: str) -> str:
    return await _process_text(
        text,
        (
            "Найди в русскоязычном тексте конкретные задачи, обязательства и "
            "следующие действия. Верни их кратким нумерованным списком. "
            "Не придумывай задачи. Если явных задач нет, верни точно: "
            "«Явных задач не найдено.»"
        ),
    )


async def extract_key_points(text: str) -> str:
    return await _process_text(
        text,
        (
            "Выдели главные тезисы из русскоязычного текста. Не дублируй весь "
            "текст, не добавляй новых фактов и не делай выводов, которых нет в "
            "источнике. Верни структурированный список. Если тезисов мало, "
            "ответь кратко. Начни ответ с точного заголовка: "
            "«🔍 Ключевые мысли:»"
        ),
    )


async def extract_questions(text: str) -> str:
    return await _process_text(
        text,
        (
            "Проанализируй русскоязычный текст и выдели вопросы. Не выдумывай "
            "факты. Если явных вопросов нет, в разделе явных вопросов напиши "
            "точно: «Явных вопросов не найдено.» Затем добавь вопросы для "
            "уточнения, только если они логически следуют из текста. Формат "
            "ответа:\n"
            "❓ Вопросы:\n"
            "1. Явные вопросы\n"
            "2. Вопросы для уточнения"
        ),
    )


async def suggest_next_steps(text: str) -> str:
    return await _process_text(
        text,
        (
            "Предложи следующие шаги на основе русскоязычного текста. Отдели "
            "явно названные действия от предположений. Не выдавай предположения "
            "за факты и не добавляй деталей, которых нет в тексте. Формат "
            "ответа:\n"
            "📌 Следующие шаги:\n"
            "1. Явно названные действия\n"
            "2. Возможные следующие шаги"
        ),
    )
