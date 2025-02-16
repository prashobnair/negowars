from config import VALIDATION_RANGES

def validate_offer(salary: int, bonus: int, remote_days: int) -> tuple[bool, str]:
    """
    Validates an offer's values.
    Returns (is_valid: bool, error_message: str)
    """
    try:
        # Validate salary
        if not isinstance(salary, (int, float)) or not float(salary).is_integer():
            return False, "Salary must be a whole number"
        salary = int(salary)
        if salary < VALIDATION_RANGES["salary"]["min"] or salary > VALIDATION_RANGES["salary"]["max"]:
            return False, f"Salary must be between ${VALIDATION_RANGES['salary']['min']} and ${VALIDATION_RANGES['salary']['max']}"

        # Validate bonus
        if not isinstance(bonus, (int, float)) or not float(bonus).is_integer():
            return False, "Bonus must be a whole number"
        bonus = int(bonus)
        if bonus < VALIDATION_RANGES["bonus"]["min"] or bonus > VALIDATION_RANGES["bonus"]["max"]:
            return False, f"Bonus must be between ${VALIDATION_RANGES['bonus']['min']} and ${VALIDATION_RANGES['bonus']['max']}"

        # Validate remote days
        if not isinstance(remote_days, (int, float)) or not float(remote_days).is_integer():
            return False, "Remote days must be a whole number"
        remote_days = int(remote_days)
        if remote_days < VALIDATION_RANGES["remote_days"]["min"] or remote_days > VALIDATION_RANGES["remote_days"]["max"]:
            return False, f"Remote days must be between {VALIDATION_RANGES['remote_days']['min']} and {VALIDATION_RANGES['remote_days']['max']}"

        return True, ""
    except (ValueError, TypeError):
        return False, "Invalid offer values"