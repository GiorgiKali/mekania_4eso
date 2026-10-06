"""Gestión de avatares personalizados: copiar imagen a carpeta segura."""
import os
import shutil
import secrets
from pathlib import Path


def carpeta_avatares():
    base = Path(os.environ.get("APPDATA", Path.home())) if os.name == "nt" else Path.home() / ".config"
    carpeta = base / "Mecania" / "avatares"
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


FORMATOS_PERMITIDOS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")


def importar_avatar(ruta_origen: str) -> str:
    """
    Copia la imagen a la carpeta de avatares del usuario con nombre único.
    Devuelve la ruta absoluta donde se guardó.
    """
    origen = Path(ruta_origen)
    if not origen.exists():
        raise FileNotFoundError(f"No existe: {ruta_origen}")
    ext = origen.suffix.lower()
    if ext not in FORMATOS_PERMITIDOS:
        raise ValueError(f"Formato no soportado: {ext}")

    nombre = f"custom_{secrets.token_hex(8)}{ext}"
    destino = carpeta_avatares() / nombre
    shutil.copy2(str(origen), str(destino))
    return str(destino)


def es_ruta_custom(avatar_id: str) -> bool:
    """Un avatar custom empieza por 'custom:'."""
    return isinstance(avatar_id, str) and avatar_id.startswith("custom:")


def obtener_ruta_custom(avatar_id: str) -> str:
    if es_ruta_custom(avatar_id):
        return avatar_id[len("custom:"):]
    return ""


def eliminar_avatar(ruta: str):
    try:
        p = Path(ruta)
        if p.exists() and p.parent == carpeta_avatares():
            p.unlink()
    except Exception:
        pass
