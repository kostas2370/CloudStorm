from django.conf import settings
import fernet


def encrypt(cleartext: str) -> str:
    print(settings.ENCRYPTION_KEY)
    key = str.encode(settings.ENCRYPTION_KEY)
    f = fernet.Fernet(key)
    return f.encrypt(cleartext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    key = str.encode(settings.ENCRYPTION_KEY)
    f = fernet.Fernet(key)
    return f.decrypt(ciphertext.encode()).decode()

