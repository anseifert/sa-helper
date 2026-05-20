from cryptography.fernet import Fernet

from app.config import get_settings

_fernet: Fernet | None = None


def _load_key() -> bytes:
    settings = get_settings()
    if settings.fernet_key:
        return settings.fernet_key.encode()
    return Fernet.generate_key()


def get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        raw = _load_key()
        try:
            _fernet = Fernet(raw)
        except Exception:
            _fernet = Fernet(Fernet.generate_key())
    return _fernet


def encrypt_token(value: str) -> str:
    return get_fernet().encrypt(value.encode()).decode()


def decrypt_token(value: str) -> str:
    return get_fernet().decrypt(value.encode()).decode()
