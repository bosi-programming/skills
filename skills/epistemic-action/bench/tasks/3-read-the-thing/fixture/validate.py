from config import VALIDATION_ENABLED


def validate(value):
    if VALIDATION_ENABLED:
        return value.isdigit()
    return True
