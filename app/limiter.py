import os

from slowapi import Limiter
from slowapi.util import get_remote_address


def _rate_key(request):
    if os.getenv("TESTING"):
        return str(id(request))
    return get_remote_address(request)


limiter = Limiter(key_func=_rate_key)
