"""Fondo animado que cambia completamente según el tema."""
import random, math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QRadialGradient, QBrush,
    QLinearGradient, QPixmap
)


TEMAS_FONDO = {
    "oscuro": {
        "c1": "#1A2540", "c2": "#0B1220", "c3": "#03050A",
        "grid": (34, 211, 238, 14), "grid2": (34, 211, 238, 24),
        "anillos": [(34, 211, 238), (167, 139, 250), (244, 114, 182)],
        "scan": True, "vinneta": 130, "claro": False,
    },
    "claro": {
        "c1": "#DBEAFE", "c2": "#F1F5F9", "c3": "#FCE7F3",
        "grid": (8, 145, 178, 18), "grid2": (8, 145, 178, 32),
        "anillos": [(8, 145, 178), (124, 58, 237), (219, 39, 119)],
        "scan": False, "vinneta": 0, "claro": True,
    },
    "neon": {
        "c1": "#3D0066", "c2": "#0A0014", "c3": "#000000",
        "grid": (255, 0, 255, 22), "grid2": (0, 255, 255, 32),
        "anillos": [(255, 0, 255), (0, 255, 255), (255, 234, 0)],
        "scan": True, "vinneta": 160, "claro": False,
    },
    "matrix": {
        "c1": "#002200", "c2": "#000A00", "c3": "#000000",
        "grid": (0, 255, 65, 22), "grid2": (0, 255, 65, 45),
        "anillos": [(0, 255, 65), (0, 200, 100), (100, 255, 100)],
        "scan": True, "vinneta": 200, "claro": False,
    },
    "papel": {
        "c1": "#FCF6E3", "c2": "#F4ECD8", "c3": "#E2CFA6",
        "grid": (139, 69, 19, 14), "grid2": (139, 69, 19, 24),
        "anillos": [(139, 69, 19), (180, 83, 9), (120, 53, 15)],
        "scan": False, "vinneta": 0, "claro": True,
    },
}


class WidgetConFondo(QWidget):
    def __init__(self, parent=None, calidad="medio", tema="oscuro"):
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

        self.tema = tema if tema in TEMAS_FONDO else "oscuro"
        self.t = 0.0
        self._cache_fondo = None
        self._cache_size = (0, 0)

        self._aplicar_calidad(calidad)
        self._reconstruir_contenido()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(int(1000 / max(1, self._fps)))

    def set_tema(self, tema):
        if tema not in TEMAS_FONDO:
            tema = "oscuro"
        self.tema = tema
        self._cache_fondo = None
        self.update()

    def _reconstruir_contenido(self):
        self.estrellas = [[], [], []]
        n = max(1, self._n_estrellas // 3)
        for capa in range(3):
            for _ in range(n):
                self.estrellas[capa].append({
                    "x": random.random(), "y": random.random(),
                    "r": 0.8 + capa * 0.5 + random.random() * 0.6,
                    "fase": random.random() * math.tau,
                    "vel": 0.02 + capa * 0.03,
                })
        self.particulas = []
        for _ in range(self._n_particulas):
            self.particulas.append({
                "x": random.random(), "y": random.random(),
                "r": random.uniform(1.2, 2.8),
                "v": random.uniform(0.0015, 0.004),
                "hue": random.choice([0, 1, 2]),
            })
        self.anillos = [
            {"cx": 0.12, "cy": 0.85, "r": 130, "vel": 0.5,  "idx": 0, "grosor": 1.5},
            {"cx": 0.88, "cy": 0.18, "r": 95,  "vel": -0.7, "idx": 1, "grosor": 1.5},
            {"cx": 0.92, "cy": 0.88, "r": 110, "vel": 0.4,  "idx": 2, "grosor": 1.2},
            {"cx": 0.08, "cy": 0.12, "r": 70,  "vel": -0.6, "idx": 0, "grosor": 1.0},
        ]

    def _aplicar_calidad(self, calidad_id):
        from logic.configuracion import obtener_calidad
        c = obtener_calidad(calidad_id)
        self.calidad = calidad_id
        self._fps = c["fps"]
        self._n_particulas = c["particulas"]
        self._n_estrellas = c["estrellas"]
        self._usar_anillos = c["anillos"]
        self._usar_scan = c["linea_scan"]

    def set_calidad(self, calidad_id):
        self._aplicar_calidad(calidad_id)
        self.timer.setInterval(int(1000 / max(1, self._fps)))
        self._reconstruir_contenido()
        self._cache_fondo = None
        self.update()

    def _tick(self):
        self.t += 1
        for capa in self.estrellas:
            for e in capa:
                e["y"] += e["vel"] / 1000
                if e["y"] > 1.05:
                    e["y"] = -0.05
                    e["x"] = random.random()
        for p in self.particulas:
            p["y"] -= p["v"]
            if p["y"] < -0.05:
                p["y"] = 1.05
                p["x"] = random.random()
        self.update()

    def resizeEvent(self, e):
        self._cache_fondo = None
        super().resizeEvent(e)

    def _esq(self):
        return TEMAS_FONDO.get(self.tema, TEMAS_FONDO["oscuro"])

    def _generar_cache_fondo(self):
        w, h = max(self.width(), 1), max(self.height(), 1)
        pm = QPixmap(w, h)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        esq = self._esq()

        grad = QRadialGradient(w * 0.5, h * 0.5, max(w, h) * 0.9)
        grad.setColorAt(0.0, QColor(esq["c1"]))
        grad.setColorAt(0.55, QColor(esq["c2"]))
        grad.setColorAt(1.0, QColor(esq["c3"]))
        p.fillRect(0, 0, w, h, QBrush(grad))

        p.setPen(QPen(QColor(*esq["grid"]), 1))
        paso = 60
        for x in range(0, w, paso):
            p.drawLine(x, 0, x, h)
        for y in range(0, h, paso):
            p.drawLine(0, y, w, y)
        p.setPen(QPen(QColor(*esq["grid2"]), 1))
        for x in range(0, w, paso * 4):
            p.drawLine(x, 0, x, h)
        for y in range(0, h, paso * 4):
            p.drawLine(0, y, w, y)

        p.end()
        self._cache_fondo = pm
        self._cache_size = (w, h)

    def paintEvent(self, e):
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return

        if self._cache_fondo is None or self._cache_size != (w, h):
            self._generar_cache_fondo()

        p = QPainter(self)
        p.drawPixmap(0, 0, self._cache_fondo)

        esq = self._esq()
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setBrush(Qt.NoBrush)

        if self._usar_anillos:
            for a in self.anillos:
                cx, cy = a["cx"] * w, a["cy"] * h
                r = a["r"]
                r_, g_, b_ = esq["anillos"][a["idx"]]
                p.setPen(QPen(QColor(r_, g_, b_, 70), a["grosor"]))
                p.drawArc(QRectF(cx - r, cy - r, r * 2, r * 2),
                          int(self.t * a["vel"] * 16) % 5760, 240 * 16)
                p.setPen(QPen(QColor(r_, g_, b_, 45), a["grosor"]))
                p.drawArc(QRectF(cx - r * 0.75, cy - r * 0.75, r * 1.5, r * 1.5),
                          int(-self.t * a["vel"] * 16) % 5760, 180 * 16)
                p.setPen(Qt.NoPen)
                p.setBrush(QBrush(QColor(r_, g_, b_, 120)))
                p.drawEllipse(QPointF(cx, cy), 3, 3)
                p.setBrush(Qt.NoBrush)

        p.setPen(Qt.NoPen)
        for capa_idx, capa in enumerate(self.estrellas):
            if esq["claro"]:
                base = esq["anillos"][capa_idx]
            else:
                base = (255, 255, 255)
            alpha_base = 60 + capa_idx * 40 if esq["claro"] else 90 + capa_idx * 55
            for e_ in capa:
                x = e_["x"] * w
                y = e_["y"] * h
                parpadeo = 0.6 + 0.4 * math.sin(self.t * 0.08 + e_["fase"])
                col = QColor(base[0], base[1], base[2])
                col.setAlpha(int(alpha_base * parpadeo))
                p.setBrush(QBrush(col))
                p.drawEllipse(QPointF(x, y), e_["r"], e_["r"])

        for pa in self.particulas:
            x = pa["x"] * w
            y = pa["y"] * h
            r_, g_, b_ = esq["anillos"][pa["hue"]]
            col = QColor(r_, g_, b_)
            col_glow = QColor(col)
            col_glow.setAlpha(45)
            p.setBrush(QBrush(col_glow))
            p.drawEllipse(QPointF(x, y), pa["r"] * 3.5, pa["r"] * 3.5)
            col.setAlpha(220)
            p.setBrush(QBrush(col))
            p.drawEllipse(QPointF(x, y), pa["r"], pa["r"])

        if self._usar_scan and esq["scan"]:
            ciclo = self.t % 250
            if ciclo < 100:
                y_scan = (ciclo / 100) * h
                c = esq["anillos"][0]
                grad_scan = QLinearGradient(0, y_scan - 20, 0, y_scan + 20)
                grad_scan.setColorAt(0.0, QColor(c[0], c[1], c[2], 0))
                grad_scan.setColorAt(0.5, QColor(c[0], c[1], c[2], 45))
                grad_scan.setColorAt(1.0, QColor(c[0], c[1], c[2], 0))
                p.fillRect(0, int(y_scan - 20), w, 40, QBrush(grad_scan))

        if esq["vinneta"] > 0:
            grad_v = QRadialGradient(w * 0.5, h * 0.5, max(w, h) * 0.75)
            grad_v.setColorAt(0.0, QColor(0, 0, 0, 0))
            grad_v.setColorAt(0.7, QColor(0, 0, 0, 0))
            grad_v.setColorAt(1.0, QColor(0, 0, 0, esq["vinneta"]))
            p.fillRect(0, 0, w, h, QBrush(grad_v))
