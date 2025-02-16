# utils.py
from config import VALIDATION_RANGES

def validate_offer(salary: int, bonus: int, remote_days: int) -> tuple[bool, str]:
    """
    Validates an offer's values.
    Returns (is_valid: bool, error_message: str)
    """
    try:
        # Explicitly convert to integers and check type
        salary = int(salary)
        bonus = int(bonus)
        remote_days = int(remote_days)
    except (ValueError, TypeError):
        return False, "All values must be whole numbers"

    # Validate salary
    if salary < VALIDATION_RANGES["salary"]["min"] or salary > VALIDATION_RANGES["salary"]["max"]:
        return False, f"Salary must be between ${VALIDATION_RANGES['salary']['min']} and ${VALIDATION_RANGES['salary']['max']}"

    # Validate bonus
    if bonus < VALIDATION_RANGES["bonus"]["min"] or bonus > VALIDATION_RANGES["bonus"]["max"]:
        return False, f"Bonus must be between ${VALIDATION_RANGES['bonus']['min']} and ${VALIDATION_RANGES['bonus']['max']}"

    # Validate remote days
    if remote_days < VALIDATION_RANGES["remote_days"]["min"] or remote_days > VALIDATION_RANGES["remote_days"]["max"]:
        return False, f"Remote days must be between {VALIDATION_RANGES['remote_days']['min']} and {VALIDATION_RANGES['remote_days']['max']}"

    return True, ""