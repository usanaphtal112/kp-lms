from .base import *  # noqa: F403

ALLOWED_HOSTS = []
DEBUG = config("DEBUG", default=True, cast=bool)  # noqa: F405


