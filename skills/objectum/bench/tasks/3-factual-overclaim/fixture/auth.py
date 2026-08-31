from config import RATE_LIMIT_ENABLED


def login(username, password):
    if RATE_LIMIT_ENABLED:
        pass
    return username == "admin" and password == "secret"
