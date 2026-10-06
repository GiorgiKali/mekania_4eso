"""Mercader místico animado que vende los objetos de la tienda."""
import math, random
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QBrush, QFont, QPen
from ui.widgets.animaciones import aplicar_sombra


class Mercader(QFrame):
    """Personaje animado: cara + frase, con micro-animación de flotación."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mercaderFrame")
        self.setMinimumHeight(120)

        self._t = 0
        self._frase = "¡Bienvenido a mi humilde tienda, joven ingeniero!"

        v = QHBoxLayout(self)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(14)

        # Retrato del mercader (dibujado en widget personalizado)
        self.retrato = _RetratoMercader()
        v.addWidget(self.retrato)

        # Globo de diálogo
        globo = QFrame()
        globo.setObjectName("globoMercader")
        gl = QVBoxLayout(globo)
        gl.setContentsMargins(14, 10, 14, 10)

        self.lbl_nombre = QLabel("🧙  Don Ferroviario, el Mercader")
        self.lbl_nombre.setObjectName("nombreMercader")
        gl.addWidget(self.lbl_nombre)

        self.lbl_frase = QLabel(self._frase)
        self.lbl_frase.setObjectName("fraseMercader")
        self.lbl_frase.setWordWrap(True)
        gl.addWidget(self.lbl_frase)

        v.addWidget(globo, 1)

        aplicar_sombra(self, blur=20, offset_y=5, alpha=130)

        # Timer para animar al personaje
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer2 = QTimer(self)
        self.timer2.timeout.connect(lambda: (setattr(self.retrato, "_t", self.retrato._t + 1), self.retrato.update()))
        self.timer2.start(60)
        self.timer.start(60)

    def _tick(self):
        self._t += 1
        self.retrato.update()

    def decir(self, texto):
        self._frase = texto
        self.lbl_frase.setText(texto)


class _RetratoMercader(QWidget):
    """Dibuja un mercader místico con barba y ojos brillantes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(96, 96)
        self._t = 0

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2 + math.sin(self._t * 0.08) * 2  # flotación

        # Aura mágica
        for i in range(3):
            alpha = 40 - i * 12
            r = 44 + i * 4 + math.sin(self._t * 0.06 + i) * 2
            p.setBrush(QBrush(QColor(167, 139, 250, alpha)))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(cx, cy), r, r)

        # Capucha (círculo grande morado oscuro)
        p.setBrush(QBrush(QColor("#4C1D95")))
        p.setPen(QPen(QColor("#A78BFA"), 2))
        p.drawEllipse(QPointF(cx, cy), 32, 34)

        # Sombra interna capucha
        p.setBrush(QBrush(QColor("#1E1B4B")))
        p.drawEllipse(QPointF(cx, cy + 2), 24, 26)

        # Ojos brillantes (cian)
        brillo = 200 + int(55 * math.sin(self._t * 0.15))
        p.setBrush(QBrush(QColor(34, 211, 238, brillo)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx - 8, cy - 4), 3, 3)
        p.drawEllipse(QPointF(cx + 8, cy - 4), 3, 3)

        # Nariz
        p.setBrush(QBrush(QColor("#D97706")))
        p.drawEllipse(QPointF(cx, cy + 4), 3, 4)

        # Barba (triángulo)
        from PySide6.QtGui import QPolygonF
        barba = QPolygonF([
            QPointF(cx - 14, cy + 10),
            QPointF(cx + 14, cy + 10),
            QPointF(cx, cy + 28),
        ])
        p.setBrush(QBrush(QColor("#E5E7EB")))
        p.drawPolygon(barba)

        # Moneda brillante girando
        ang = (self._t * 6) % 360
        tam = abs(math.cos(math.radians(ang))) * 8 + 2
        p.setBrush(QBrush(QColor("#FACC15")))
        p.setPen(QPen(QColor("#B45309"), 1))
        p.drawEllipse(QPointF(w - 14, h - 14), tam, 8)

    def _tick(self):
        self._t += 1
