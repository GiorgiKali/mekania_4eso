"""Widgets animados: sombra, confeti, toast, barra XP, avatar, ripple, typewriter."""
import random
from PySide6.QtWidgets import (
    QWidget, QLabel, QFrame, QProgressBar, QGraphicsDropShadowEffect,
    QVBoxLayout, QPushButton
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QPointF, QRectF, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QPixmap, QPainterPath


def aplicar_sombra(widget, blur=24, offset_y=6, alpha=140):
    s = QGraphicsDropShadowEffect(widget)
    s.setBlurRadius(blur)
    s.setXOffset(0)
    s.setYOffset(offset_y)
    s.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(s)
    return s


class BarraXPAnimada(QWidget):
    """Barra XP con etiqueta SUPERIOR — el texto nunca se solapa con el relleno."""
    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)

        self.lbl = QLabel("")
        self.lbl.setObjectName("etiquetaXP")
        self.lbl.setAlignment(Qt.AlignCenter)
        v.addWidget(self.lbl)

        self.barra = QProgressBar()
        self.barra.setObjectName("barraXP")
        self.barra.setTextVisible(False)
        self.barra.setMinimumHeight(14)
        v.addWidget(self.barra)

        self._anim = None

    def setFormat(self, txt):
        self.lbl.setText(txt)

    def setValue(self, v):
        self.barra.setValue(v)

    def value(self):
        return self.barra.value()

    def animar_a(self, valor, duracion=800):
        self._anim = QPropertyAnimation(self.barra, b"value")
        self._anim.setDuration(duracion)
        self._anim.setStartValue(self.barra.value())
        self._anim.setEndValue(valor)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()


class AvatarCircular(QLabel):
    def __init__(self, emoji="🍎", color="#22D3EE", diametro=64, parent=None):
        super().__init__(emoji, parent)
        self.setFixedSize(diametro, diametro)
        self.setAlignment(Qt.AlignCenter)
        f = QFont("Noto Color Emoji", int(diametro * 0.5))
        if not f.exactMatch():
            f = QFont("", int(diametro * 0.45))
        self.setFont(f)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(34, 211, 238, 0.12);
                border: 3px solid {color};
                border-radius: {diametro // 2}px;
                color: white;
            }}
        """)
        aplicar_sombra(self, blur=20, offset_y=4, alpha=100)


class Confeti(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()
        self.particulas = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self._duracion_ticks = 0

    def lanzar(self, cantidad=80, duracion_ms=2200):
        if not self.parent():
            return
        self.resize(self.parent().size())
        self.raise_()
        self.show()
        colores = ["#22D3EE", "#A78BFA", "#F472B6", "#FACC15", "#22C55E", "#F97316", "#EF4444"]
        self.particulas = []
        for _ in range(cantidad):
            self.particulas.append({
                "x": random.uniform(0, self.width()),
                "y": random.uniform(-50, -10),
                "vx": random.uniform(-1.5, 1.5),
                "vy": random.uniform(2.5, 6.0),
                "color": random.choice(colores),
                "size": random.uniform(6, 14),
                "rot": random.uniform(0, 360),
                "vrot": random.uniform(-8, 8),
            })
        self._duracion_ticks = int(duracion_ms / 30)
        self.timer.start(30)

    def _tick(self):
        for p in self.particulas:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.15
            p["rot"] += p["vrot"]
        self._duracion_ticks -= 1
        if self._duracion_ticks <= 0:
            self.timer.stop()
            self.particulas = []
            self.hide()
        self.update()

    def paintEvent(self, e):
        if not self.particulas:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        for c in self.particulas:
            p.save()
            p.translate(c["x"], c["y"])
            p.rotate(c["rot"])
            p.setBrush(QBrush(QColor(c["color"])))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(-c["size"]/2, -c["size"]/4, c["size"], c["size"]/2), 2, 2)
            p.restore()


class Toast(QFrame):
    def __init__(self, texto, tipo="info", padre=None, duracion=2000):
        super().__init__(padre)
        self.setObjectName("toast")
        colores = {"info": "#22D3EE", "exito": "#22C55E", "error": "#EF4444", "aviso": "#FACC15"}
        color = colores.get(tipo, "#22D3EE")
        self.setStyleSheet(f"""
            QFrame#toast {{
                background-color: #111C33;
                border: 2px solid {color};
                border-radius: 14px;
                padding: 14px 22px;
            }}
            QFrame#toast QLabel {{
                color: #F8FAFC; font-size: 15px; font-weight: 700;
                background: transparent;
            }}
        """)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        self.lbl = QLabel(texto)
        v.addWidget(self.lbl)
        aplicar_sombra(self, blur=30, offset_y=8, alpha=180)

        if padre:
            self.adjustSize()
            x = (padre.width() - self.width()) // 2
            y = padre.height() - self.height() - 40
            self.move(x, y + 30)
            self.show()
            self.raise_()
            self._anim_entrada = QPropertyAnimation(self, b"pos")
            self._anim_entrada.setDuration(300)
            self._anim_entrada.setStartValue(self.pos())
            self._anim_entrada.setEndValue(self.pos().__class__(x, y))
            self._anim_entrada.setEasingCurve(QEasingCurve.OutBack)
            self._anim_entrada.start()
            QTimer.singleShot(duracion, self._salir)

    def _salir(self):
        if not self.isVisible():
            return
        self._anim_salida = QPropertyAnimation(self, b"pos")
        self._anim_salida.setDuration(250)
        self._anim_salida.setStartValue(self.pos())
        self._anim_salida.setEndValue(self.pos().__class__(self.x(), self.y() + 30))
        self._anim_salida.setEasingCurve(QEasingCurve.InCubic)
        self._anim_salida.finished.connect(self.deleteLater)
        self._anim_salida.start()


def mostrar_toast(padre, texto, tipo="info", duracion=2200):
    return Toast(texto, tipo=tipo, padre=padre, duracion=duracion)


class BotonRipple(QPushButton):
    def __init__(self, texto="", parent=None):
        super().__init__(texto, parent)
        self.ripples = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(35)
        self.pressed.connect(self._nuevo_ripple)

    def _nuevo_ripple(self):
        from PySide6.QtGui import QCursor
        pos = self.mapFromGlobal(QCursor.pos())
        self.ripples.append({"x": pos.x(), "y": pos.y(), "r": 0, "alpha": 200})

    def _tick(self):
        if not self.ripples:
            return
        for r in self.ripples[:]:
            r["r"] += 12
            r["alpha"] -= 18
            if r["alpha"] <= 0:
                self.ripples.remove(r)
        self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        if not self.ripples:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(Qt.NoBrush)
        for r in self.ripples:
            col = QColor(34, 211, 238, r["alpha"])
            p.setPen(QPen(col, 2))
            p.drawEllipse(QPointF(r["x"], r["y"]), r["r"], r["r"])


class TextoTypewriter(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._texto_completo = ""
        self._idx = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._siguiente)
        self._velocidad = 4

    def escribir(self, texto, velocidad_ms=4):
        self._texto_completo = texto
        self._idx = 0
        self._velocidad = velocidad_ms
        self.setText("")
        self._timer.start(self._velocidad)

    def _siguiente(self):
        if self._idx >= len(self._texto_completo):
            self._timer.stop()
            return
        self._idx += 1
        self.setText(self._texto_completo[:self._idx])


# ───────────────────────────────────────────────
# 8. AVATAR CON SOPORTE DE IMAGEN CUSTOM
# ───────────────────────────────────────────────
from PySide6.QtGui import QPixmap, QPainterPath


class AvatarWidget(QLabel):
    """Widget circular que muestra emoji O imagen PNG/JPG recortada en círculo."""

    def __init__(self, contenido="🍎", diametro=64, parent=None, es_ruta=False):
        super().__init__(parent)
        self.diametro = diametro
        self.setFixedSize(diametro, diametro)
        self.setAlignment(Qt.AlignCenter)
        self._es_ruta = False
        self.set_contenido(contenido, es_ruta)
        aplicar_sombra(self, blur=20, offset_y=4, alpha=100)

    def set_contenido(self, contenido, es_ruta=False):
        self._es_ruta = es_ruta
        if es_ruta:
            self.setPixmap(QPixmap())
            self._cargar_imagen(contenido)
        else:
            self.setText(contenido)
            f = QFont("Noto Color Emoji", int(self.diametro * 0.5))
            if not f.exactMatch():
                f = QFont("", int(self.diametro * 0.45))
            self.setFont(f)

    def _cargar_imagen(self, ruta):
        pm = QPixmap(ruta)
        if pm.isNull():
            self.setText("❓")
            return
        pm = pm.scaled(self.diametro, self.diametro,
                       Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        resultado = QPixmap(self.diametro, self.diametro)
        resultado.fill(Qt.transparent)
        p = QPainter(resultado)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, self.diametro, self.diametro)
        p.setClipPath(path)
        x = (pm.width() - self.diametro) // 2
        y = (pm.height() - self.diametro) // 2
        p.drawPixmap(-x, -y, pm)
        p.end()
        self.setPixmap(resultado)
        # Borde circular decorativo
        self.setStyleSheet(f"""
            QLabel {{
                background-color: transparent;
                border: 3px solid #22D3EE;
                border-radius: {self.diametro // 2}px;
            }}
        """)
