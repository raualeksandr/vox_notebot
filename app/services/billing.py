from decimal import Decimal


def seconds_to_billable_minutes(duration_seconds: int | float) -> Decimal:
    """Convert audio duration to fractional minutes without charging a user."""
    return Decimal(str(duration_seconds)) / Decimal("60")

