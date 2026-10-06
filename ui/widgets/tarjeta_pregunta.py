"""Tarjeta de pregunta con typewriter, confeti, shake y ripple."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint
from ui.widgets.animaciones import (
    aplicar_sombra, Confeti, mostrar_toast, BotonRipple, TextoTypewriter
)


class TarjetaPregunta(QFrame):
    def __init__(self, ventana):
        super().__init__()
        self.ventana = ventana
        self.setObjectName("tarjetaPregunta")
        aplicar_sombra(self, blur=34, offset_y=12, alpha=180)

        v = QVBoxLayout(self)
        v.setContentsMargins(32, 28, 32, 28)
        v.setSpacing(14)

        # Etiqueta superior
        self.lbl_bloque = QLabel()
        self.lbl_bloque.setObjectName("etiquetaBloque")
        v.addWidget(self.lbl_bloque)

        # Pregunta con typewriter
        self.lbl_pregunta = TextoTypewriter()
        self.lbl_pregunta.setObjectName("pregunta")
        self.lbl_pregunta.setWordWrap(True)
        self.lbl_pregunta.setMinimumHeight(80)
        v.addWidget(self.lbl_pregunta)

        # Confianza
        conf = QHBoxLayout()
        et = QLabel("¿Cómo de seguro estás?")
        et.setObjectName("confianzaTexto")
        conf.addWidget(et)
        self.btn_alta = QPushButton("🟢 Seguro")
        self.btn_media = QPushButton("🟡 Dudo")
        self.btn_baja = QPushButton("🔴 No lo sé")
        for b in (self.btn_alta, self.btn_media, self.btn_baja):
            b.setCheckable(True)
            b.setObjectName("confianza")
            b.setCursor(Qt.PointingHandCursor)
            conf.addWidget(b)
        self.btn_media.setChecked(True)
        self.btn_alta.clicked.connect(lambda: self._set_conf("alta"))
        self.btn_media.clicked.connect(lambda: self._set_conf("media"))
        self.btn_baja.clicked.connect(lambda: self._set_conf("baja"))
        conf.addStretch()
        v.addLayout(conf)
        self.confianza = "media"

        # Opciones (4)
        self.botones = []
        for i in range(4):
            b = BotonRipple()
            b.setObjectName("opcion")
            b.setMinimumHeight(56)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, idx=i: self._elegir(idx))
            v.addWidget(b)
            self.botones.append(b)

        # Pista
        self.btn_pista = QPushButton("💡  Ver pista")
        self.btn_pista.setObjectName("pista")
        self.btn_pista.setCursor(Qt.PointingHandCursor)
        self.btn_pista.clicked.connect(self._mostrar_pista)
        v.addWidget(self.btn_pista, alignment=Qt.AlignRight)

        self.lbl_pista = QLabel()
        self.lbl_pista.setObjectName("pistaTexto")
        self.lbl_pista.setWordWrap(True)
        self.lbl_pista.hide()
        v.addWidget(self.lbl_pista)

        # Feedback
        self.lbl_feedback = QLabel()
        self.lbl_feedback.setObjectName("feedback")
        self.lbl_feedback.setWordWrap(True)
        self.lbl_feedback.hide()
        v.addWidget(self.lbl_feedback)

        # Confeti
        self.confeti = Confeti(ventana)

        # Shake animation setup
        self._pos_original = None

        self.pregunta_actual = None
        self.respondida = False
        self.callback = None

    def _set_conf(self, c):
        self.confianza = c
        self.btn_alta.setChecked(c == "alta")
        self.btn_media.setChecked(c == "media")
        self.btn_baja.setChecked(c == "baja")

    def mostrar(self, p, callback):
        self.pregunta_actual = p
        self.callback = callback
        self.respondida = False
        self.lbl_bloque.setText(f"◆  BLOQUE {p['b']}    ·    {p['d'].upper()}")
        self.lbl_pregunta.escribir(p["p"], velocidad_ms=1)
        letras = ["A", "B", "C", "D"]
        for i, b in enumerate(self.botones):
            b.setText(f"  {letras[i]}.   {p['o'][i]}")
            b.setEnabled(True)
            b.setProperty("estado", "")
            b.style().unpolish(b)
            b.style().polish(b)
        self.lbl_pista.hide()
        self.lbl_feedback.hide()
        self.btn_pista.setEnabled(True)
        self._set_conf("media")

    def _mostrar_pista(self):
        if self.pregunta_actual:
            self.lbl_pista.setText("💡  " + self.pregunta_actual["h"])
            self.lbl_pista.show()
            self.btn_pista.setEnabled(False)

    def _elegir(self, idx):
        if self.respondida or not self.pregunta_actual:
            return
        self.respondida = True
        for b in self.botones:
            b.setEnabled(False)
        self.callback(idx, self.confianza)

    def _shake(self):
        """Anima la tarjeta con un pequeño temblor cuando falla."""
        if self._pos_original is None:
            self._pos_original = self.pos()
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(400)
        ox, oy = self._pos_original.x(), self._pos_original.y()
        anim.setKeyValueAt(0.0, QPoint(ox, oy))
        anim.setKeyValueAt(0.15, QPoint(ox - 10, oy))
        anim.setKeyValueAt(0.30, QPoint(ox + 10, oy))
        anim.setKeyValueAt(0.45, QPoint(ox - 8, oy))
        anim.setKeyValueAt(0.60, QPoint(ox + 8, oy))
        anim.setKeyValueAt(0.80, QPoint(ox - 4, oy))
        anim.setKeyValueAt(1.0, QPoint(ox, oy))
        anim.start()
        self._shake_anim = anim

    def mostrar_feedback(self, acierto, p):
        correcta = p["c"]
        for i, b in enumerate(self.botones):
            b.setProperty("estado", "correcto" if i == correcta else "incorrecto")
            b.style().unpolish(b)
            b.style().polish(b)

        if acierto:
            icono = "🎉"
            titulo = "¡CORRECTO!"
            color = "#22C55E"
            self.confeti.lanzar(cantidad=70, duracion_ms=1800)
            mostrar_toast(self.ventana, "✨ ¡Bien!  +XP", "exito", 1400)
        else:
            icono = "😔"
            titulo = "Incorrecto"
            color = "#EF4444"
            self._shake()
            mostrar_toast(self.ventana, "💪 ¡Sigue!", "aviso", 1400)

        self.lbl_feedback.setText(
            f"<div style='font-size:17px;'><b style='color:{color};'>{icono}  {titulo}</b></div>"
            f"<div style='margin-top:8px;'>"
            f"<b>Respuesta correcta:</b> "
            f"<span style='color:#22D3EE;'>{chr(65+correcta)}. {p['o'][correcta]}</span></div>"
            f"<div style='margin-top:6px;'><b>Explicación:</b> {p['e']}</div>"
        )
        self.lbl_feedback.show()
