"""Autenticación segura: PBKDF2-HMAC-SHA256 con salt único por usuario.
Usa solo la librería estándar de Python (hashlib, secrets, base64)."""
import hashlib
import secrets
import base64


ITERACIONES = 120_000   # ~150 ms en CPU débil, seguro contra fuerza bruta
LONGITUD_HASH = 32


def generar_salt() -> str:
    """Genera un salt aleatorio de 16 bytes codificado en base64."""
    return base64.b64encode(secrets.token_bytes(16)).decode("ascii")


def hash_password(password: str, salt_b64: str) -> str:
    """Deriva la contraseña con PBKDF2-HMAC-SHA256.
    Devuelve el hash codificado en base64."""
    salt = base64.b64decode(salt_b64)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, ITERACIONES, dklen=LONGITUD_HASH
    )
    return base64.b64encode(dk).decode("ascii")


def verificar_password(password: str, salt_b64: str, hash_guardado: str) -> bool:
    """Verifica en tiempo constante."""
    calculado = hash_password(password, salt_b64)
    return secrets.compare_digest(calculado, hash_guardado)


def validar_nombre(nombre: str):
    if not nombre:
        return False, "Introduce un nombre."
    nombre = nombre.strip()
    if len(nombre) < 3:
        return False, "El nombre debe tener al menos 3 caracteres."
    if len(nombre) > 20:
        return False, "El nombre no puede superar 20 caracteres."
    if not all(c.isalnum() or c in "_-" for c in nombre):
        return False, "Solo letras, números, guiones y guiones bajos."
    return True, ""


def validar_password(password: str):
    if not password:
        return False, "Introduce una contraseña."
    if len(password) < 4:
        return False, "Mínimo 4 caracteres."
    if len(password) > 64:
        return False, "Máximo 64 caracteres."
    return True, ""


def validar_confirmacion(p1: str, p2: str):
    if p1 != p2:
        return False, "Las contraseñas no coinciden."
    return True, ""
