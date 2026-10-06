"""Configuración de temas visuales y calidad gráfica."""


TEMAS_DISPONIBLES = [
    {"id": "oscuro", "nombre": "Oscuro Cyberpunk", "emoji": "🌌", "precio": 0},
    {"id": "claro",  "nombre": "Claro Nítido",     "emoji": "☀️", "precio": 0},
    {"id": "neon",   "nombre": "Neón Magenta",     "emoji": "💜", "precio": 300},
    {"id": "matrix", "nombre": "Matrix Verde",     "emoji": "🟢", "precio": 400},
    {"id": "papel",  "nombre": "Papel Antiguo",    "emoji": "📜", "precio": 500},
]


CALIDADES = {
    "bajo": {
        "nombre": "Bajo (rápido)",
        "emoji": "🐢",
        "descripcion": "Ideal para PCs lentos. Sin animaciones.",
        "fps": 8,
        "particulas": 0,
        "estrellas": 0,
        "anillos": False,
        "linea_scan": False,
        "cache_fondo": True,
    },
    "medio": {
        "nombre": "Medio (equilibrado)",
        "emoji": "⚖️",
        "descripcion": "Buen equilibrio entre belleza y rendimiento.",
        "fps": 16,
        "particulas": 6,
        "estrellas": 30,
        "anillos": True,
        "linea_scan": False,
        "cache_fondo": True,
    },
    "alto": {
        "nombre": "Alto (máxima belleza)",
        "emoji": "✨",
        "descripcion": "Todos los efectos activados.",
        "fps": 25,
        "particulas": 18,
        "estrellas": 84,
        "anillos": True,
        "linea_scan": True,
        "cache_fondo": True,
    },
}


def obtener_calidad(nombre):
    return CALIDADES.get(nombre, CALIDADES["medio"])


def listar_calidades():
    return [
        {"id": k, **v} for k, v in CALIDADES.items()
    ]


def es_tema_claro(tema_id):
    return tema_id in ("claro", "papel")
