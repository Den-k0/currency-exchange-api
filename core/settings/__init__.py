import os

settings_module = os.getenv("DJANGO_SETTINGS_MODULE")

if settings_module == "core.settings.prod":
    from .prod import *
else:
    from .dev import *
