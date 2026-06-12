def clean_text(text: str) -> str:
    """Apply minimal cleanup while the processing pipeline is a stub."""
    return " ".join(text.split())


async def summarize_text(text: str) -> str:
    _ = text
    return "Краткое содержание пока не подключено."


async def extract_tasks(text: str) -> list[str]:
    _ = text
    return []

