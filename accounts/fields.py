import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _get_fernet():
    """Derive a stable Fernet key from the project's SECRET_KEY.

    Reuses the existing secret instead of introducing a second key to manage/rotate.
    """
    key_material = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_material)
    return Fernet(fernet_key)


class EncryptedCharField(models.TextField):
    """A text field that is encrypted at rest with Fernet (AES-128-CBC + HMAC-SHA256).

    Encryption happens in get_prep_value (right before the value is sent to the
    database), and decryption happens in from_db_value (right after it's read back),
    so the ciphertext is what actually lives in the database column — the plaintext
    only ever exists in the Python process, never on disk.
    """

    description = 'Text encrypted at rest using Fernet symmetric encryption'

    def get_prep_value(self, value):
        if value is None or value == '':
            return value
        return _get_fernet().encrypt(str(value).encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value
        try:
            return _get_fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            # Value predates encryption (or the key changed) — surface it as-is
            # rather than crashing the whole page.
            return value
