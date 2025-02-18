# immich_go_gui/utils/validators.py
import re

def validate_server_url(url):
    """Validates the server URL."""
    return bool(re.match(r"^https?://.+", url))

def validate_api_key(key):
    """Validates the API key (basic check for non-emptiness)."""
    return bool(key.strip())