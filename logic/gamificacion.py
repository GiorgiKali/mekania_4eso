"""XP, monedas, niveles, rangos y logros."""
RANGOS = [
    (0, "Aprendiz"), (200, "Técnico"), (600, "Ingeniero"),
    (1500, "Maestro"), (3000, "Leyenda MECANIA"),
]


def xp_para_nivel(n):
    return int(50 * (n - 1) ** 1.6)


class Gamificacion:
    def __init__(self, db):
        self.db = db

    def otorgar_xp(self, cantidad, racha=0):
        j = self.db.jugador()
        mult = 5 if racha >= 20 else 3 if racha >= 10 else 2 if racha >= 5 else 1
        xp_ganada = int(cantidad * mult)
        nuevo_xp = j["xp"] + xp_ganada
        nuevo_nivel = j["nivel"]
        while xp_para_nivel(nuevo_nivel + 1) <= nuevo_xp:
            nuevo_nivel += 1
        rango = "Aprendiz"
        for umbral, nombre in RANGOS:
            if nuevo_xp >= umbral:
                rango = nombre
        subio = nuevo_nivel > j["nivel"]
        self.db.actualizar_jugador(xp=nuevo_xp, nivel=nuevo_nivel, rango=rango)
        return {"xp_ganada": xp_ganada, "multiplicador": mult,
                "nivel": nuevo_nivel, "subio_nivel": subio}

    def otorgar_monedas(self, cantidad):
        j = self.db.jugador()
        self.db.actualizar_jugador(monedas=j["monedas"] + cantidad)

    def gastar_monedas(self, cantidad):
        j = self.db.jugador()
        if j["monedas"] < cantidad:
            return False
        self.db.actualizar_jugador(monedas=j["monedas"] - cantidad)
        return True

    def comprobar_logros(self, ctx):
        nuevos = []
        reglas = [
            ("racha_10", lambda c: c.get("racha", 0) >= 10),
            ("sin_fallos", lambda c: c.get("sin_fallos", False)),
            ("rey_palancas", lambda c: c.get("bloque_B5_dominado", False)),
            ("ingeniero", lambda c: c.get("dominadas_total", 0) >= 50),
            ("sabio", lambda c: c.get("dominadas_total", 0) >= 100),
        ]
        for lid, cond in reglas:
            if not self.db.logro_desbloqueado(lid) and cond(ctx):
                self.db.desbloquear_logro(lid)
                nuevos.append(lid)
        return nuevos


# ═══════════════════════════════════════════════════════
# CONSEJOS HUMANIZADOS — se muestran aleatoriamente al inicio
# ═══════════════════════════════════════════════════════
CONSEJOS = [
    "💡 Recuerda: la polea fija NO reduce la fuerza, solo cambia la dirección.",
    "💡 En las palancas de 1er género, el fulcro está en medio.",
    "💡 Los engranajes helicoidales son los más silenciosos.",
    "💡 F·BF = R·BR  — la ley de la palanca, grabátela.",
    "💡 El pistón se mueve de forma alternativa; el cigüeñal lo convierte en giro.",
    "💡 Si te equivocas, no pasa nada: la pregunta volverá hasta que la domines.",
    "💡 La masa se mide en kg; el peso en newtons (N).",
    "💡 El piñón-cremallera transforma giro en movimiento lineal continuo.",
    "💡 Un polipasto multiplica la ventaja mecánica: menos esfuerzo, más cuerda.",
    "💡 Los engranajes cónicos transmiten entre ejes perpendiculares.",
    "💡 La leva NO es reversible. Esa es su firma.",
    "💡 En un sistema reductor: baja las rpm y sube el par.",
]

import random as _random
def consejo_aleatorio():
    return _random.choice(CONSEJOS)
