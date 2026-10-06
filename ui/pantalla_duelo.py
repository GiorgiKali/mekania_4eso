"""Modo duelo 1v1 local: dos jugadores alternan turnos con las mismas preguntas."""
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QGridLayout, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from ui.widgets.animaciones import aplicar_sombra, mostrar_toast, AvatarWidget
from ui.widgets.fondo_animado import WidgetConFondo
from logic.motor_preguntas import cargar_json
from logic.avatares_custom import es_ruta_custom, obtener_ruta_custom


class PantallaDuelo(QWidget):
    def __init__(self, ventana, db, banco):
        super().__init__(ventana)
        self.ventana = ventana
        self.db = db
        self.banco = banco
        self._construir()

    def _construir(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        fondo = WidgetConFondo()
        layout.addWidget(fondo)

        self.pila = QVBoxLayout(fondo)
        self.pila.setContentsMargins(30, 15, 30, 15)
        self.pila.setSpacing(10)

        self._pantalla_configuracion()

    # ==================== CONFIG ====================
    def _pantalla_configuracion(self):
        self._limpiar()

        tit = QLabel("⚔️  Duelo 1 vs 1")
        tit.setObjectName("titulo")
        tit.setAlignment(Qt.AlignCenter)
        self.pila.addWidget(tit)

        sub = QLabel("Dos jugadores, las mismas preguntas, gana quien más acierte")
        sub.setObjectName("subtitulo")
        sub.setAlignment(Qt.AlignCenter)
        self.pila.addWidget(sub)

        jugadores = self.db.lista_usuarios_para_duelo()
        if len(jugadores) < 2:
            aviso = QLabel("Necesitas al menos 2 usuarios registrados para jugar un duelo.\n"
                           "Pide a un compañero que cree su cuenta.")
            aviso.setWordWrap(True)
            aviso.setAlignment(Qt.AlignCenter)
            aviso.setObjectName("tarjeta")
            self.pila.addWidget(aviso)
            btn = QPushButton("← Volver")
            btn.setObjectName("botonSecundario")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda: self.ventana._ir_a(0))
            self.pila.addWidget(btn, alignment=Qt.AlignLeft)
            return

        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta")
        tv = QVBoxLayout(tarjeta)
        tv.setContentsMargins(20, 20, 20, 20)
        tv.setSpacing(14)

        tv.addWidget(self._label("Jugador 1"))
        self.combo1 = QComboBox()
        for j in jugadores:
            self.combo1.addItem(f"{j['nombre']}  (Nivel {j['nivel']}, {j['xp']} XP)", j["id"])
        tv.addWidget(self.combo1)

        tv.addWidget(self._label("Jugador 2"))
        self.combo2 = QComboBox()
        for j in jugadores:
            self.combo2.addItem(f"{j['nombre']}  (Nivel {j['nivel']}, {j['xp']} XP)", j["id"])
        if self.combo2.count() > 1:
            self.combo2.setCurrentIndex(1)
        tv.addWidget(self.combo2)

        tv.addWidget(self._label("Número de preguntas"))
        self.combo_n = QComboBox()
        for n in (10, 15, 20, 30):
            self.combo_n.addItem(f"{n} preguntas", n)
        tv.addWidget(self.combo_n)

        aplicar_sombra(tarjeta, blur=20, offset_y=5, alpha=130)
        self.pila.addWidget(tarjeta)

        btn_empezar = QPushButton("🔥  EMPEZAR DUELO")
        btn_empezar.setObjectName("botonPrimario")
        btn_empezar.setMinimumHeight(52)
        btn_empezar.setCursor(Qt.PointingHandCursor)
        btn_empezar.clicked.connect(self._empezar)
        self.pila.addWidget(btn_empezar)

        btn_volver = QPushButton("← Volver")
        btn_volver.setObjectName("botonSecundario")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.clicked.connect(lambda: self.ventana._ir_a(0))
        self.pila.addWidget(btn_volver, alignment=Qt.AlignLeft)

    def _label(self, texto):
        l = QLabel(texto)
        l.setObjectName("labelForm")
        return l

    def _limpiar(self):
        while self.pila.count():
            it = self.pila.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

    # ==================== JUEGO ====================
    def _empezar(self):
        j1_id = self.combo1.currentData()
        j2_id = self.combo2.currentData()
        if j1_id == j2_id:
            mostrar_toast(self, "❌ Deben ser usuarios distintos", "error")
            return
        n = self.combo_n.currentData()

        # Cargar datos de jugadores
        self.j1 = self.db.obtener_por_id(j1_id)
        self.j2 = self.db.obtener_por_id(j2_id)

        # Seleccionar preguntas aleatorias (mismas para ambos)
        ids = self.banco.todas_ids()
        random.shuffle(ids)
        self.preguntas_duelo = ids[:n]

        # Estado
        self.pregunta_idx = 0
        self.turno = 1   # 1 = jugador 1, 2 = jugador 2
        self.aciertos = {1: 0, 2: 0}
        self.respuestas_turno = {1: [], 2: []}

        self._pantalla_juego()

    def _pantalla_juego(self):
        self._limpiar()

        # Cabecera
        cab = QHBoxLayout()
        self.lbl_jugador_turno = QLabel()
        self.lbl_jugador_turno.setObjectName("titulo")
        cab.addWidget(self.lbl_jugador_turno)
        cab.addStretch()
        self.lbl_progreso = QLabel()
        self.lbl_progreso.setObjectName("hud")
        cab.addWidget(self.lbl_progreso)
        self.pila.addLayout(cab)

        # Marcadores
        marcadores = QHBoxLayout()
        marcadores.setSpacing(20)

        self.marcador1 = self._marcador(self.j1, "#22D3EE")
        self.marcador2 = self._marcador(self.j2, "#F472B6")
        marcadores.addWidget(self.marcador1["card"])
        marcadores.addWidget(self.marcador2["card"])
        self.pila.addLayout(marcadores)

        # Pregunta
        self.card_pregunta = QFrame()
        self.card_pregunta.setObjectName("tarjetaPregunta")
        cp = QVBoxLayout(self.card_pregunta)
        cp.setContentsMargins(28, 22, 28, 22)
        cp.setSpacing(12)

        self.lbl_pregunta = QLabel()
        self.lbl_pregunta.setObjectName("pregunta")
        self.lbl_pregunta.setWordWrap(True)
        self.lbl_pregunta.setMinimumHeight(70)
        cp.addWidget(self.lbl_pregunta)

        self.botones_opciones = []
        for i in range(4):
            b = QPushButton()
            b.setObjectName("opcion")
            b.setMinimumHeight(52)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, idx=i: self._responder(idx))
            cp.addWidget(b)
            self.botones_opciones.append(b)

        self.lbl_feedback = QLabel()
        self.lbl_feedback.setObjectName("feedback")
        self.lbl_feedback.setWordWrap(True)
        self.lbl_feedback.hide()
        cp.addWidget(self.lbl_feedback)

        aplicar_sombra(self.card_pregunta, blur=24, offset_y=6, alpha=140)
        self.pila.addWidget(self.card_pregunta, 1)

        # Volver
        btn_volver = QPushButton("← Abandonar")
        btn_volver.setObjectName("botonSecundario")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.clicked.connect(self._abandonar)
        self.pila.addWidget(btn_volver, alignment=Qt.AlignLeft)

        self._actualizar_turno()

    def _marcador(self, jugador, color):
        card = QFrame()
        card.setObjectName("filaRanking")
        cv = QHBoxLayout(card)
        cv.setContentsMargins(14, 10, 14, 10)
        cv.setSpacing(10)

        av_widget = self._crear_avatar(jugador["avatar"])
        cv.addWidget(av_widget)

        col = QVBoxLayout()
        col.setSpacing(0)
        nombre = QLabel(jugador["nombre"])
        nombre.setStyleSheet("font-size: 14px; font-weight: 800; background: transparent;")
        col.addWidget(nombre)
        aciertos = QLabel("0 aciertos")
        aciertos.setStyleSheet(f"font-size: 12px; color: {color}; font-weight: 700; background: transparent;")
        col.addWidget(aciertos)
        cv.addLayout(col, 1)

        aplicar_sombra(card, blur=14, offset_y=3, alpha=110)
        return {"card": card, "nombre": nombre, "aciertos": aciertos}

    def _crear_avatar(self, avatar_id):
        if es_ruta_custom(avatar_id):
            return AvatarWidget(obtener_ruta_custom(avatar_id), diametro=40, es_ruta=True)
        avatares = cargar_json("data/avatares.json")
        av = next((a for a in avatares if a["id"] == avatar_id), avatares[0])
        return AvatarWidget(av["emoji"], diametro=40)

    def _actualizar_turno(self):
        if self.pregunta_idx >= len(self.preguntas_duelo):
            self._fin_del_duelo()
            return

        turno = self.turno
        jugador = self.j1 if turno == 1 else self.j2
        color = "#22D3EE" if turno == 1 else "#F472B6"
        self.lbl_jugador_turno.setText(f"👉 Turno de: {jugador['nombre']}")
        self.lbl_jugador_turno.setStyleSheet(
            f"color: {color}; font-size: 20px; font-weight: 900; background: transparent;")

        total_turnos = len(self.preguntas_duelo) * 2
        realizados = self.pregunta_idx * 2 + (turno - 1)
        self.lbl_progreso.setText(f"{realizados+1}/{total_turnos}")

        # Pregunta
        p = self.banco.obtener(self.preguntas_duelo[self.pregunta_idx])
        self.pregunta_actual = p
        self.lbl_pregunta.setText(p["p"])
        for i, b in enumerate(self.botones_opciones):
            b.setText(f"  {chr(65+i)}.   {p['o'][i]}")
            b.setEnabled(True)
            b.setProperty("estado", "")
            b.style().unpolish(b)
            b.style().polish(b)
        self.lbl_feedback.hide()

        self.marcador1["aciertos"].setText(f"{self.aciertos[1]} aciertos")
        self.marcador2["aciertos"].setText(f"{self.aciertos[2]} aciertos")

    def _responder(self, idx):
        p = self.pregunta_actual
        acierto = (idx == p["c"])

        for b in self.botones_opciones:
            b.setEnabled(False)
            b.setProperty("estado", "correcto" if b == self.botones_opciones[p["c"]] else "incorrecto")
            b.style().unpolish(b)
            b.style().polish(b)

        if acierto:
            self.aciertos[self.turno] += 1
            self.lbl_feedback.setText(
                f"<b style='color:#22C55E;'>✅ ¡Correcto!</b>  "
                f"{p['e']}"
            )
        else:
            self.lbl_feedback.setText(
                f"<b style='color:#EF4444;'>❌ Fallo</b>  ·  Respuesta correcta: "
                f"<b>{chr(65+p['c'])}. {p['o'][p['c']]}</b><br>{p['e']}"
            )
        self.lbl_feedback.show()

        self.marcador1["aciertos"].setText(f"{self.aciertos[1]} aciertos")
        self.marcador2["aciertos"].setText(f"{self.aciertos[2]} aciertos")

        QTimer.singleShot(2400, self._siguiente_turno)

    def _siguiente_turno(self):
        if self.turno == 1:
            # Cambia al jugador 2 con la MISMA pregunta
            self.turno = 2
        else:
            # Ambos jugadores han respondido: siguiente pregunta
            self.turno = 1
            self.pregunta_idx += 1
        self._actualizar_turno()

    def _fin_del_duelo(self):
        self._limpiar()

        tit = QLabel("🏁  Fin del duelo")
        tit.setObjectName("titulo")
        tit.setAlignment(Qt.AlignCenter)
        self.pila.addWidget(tit)

        if self.aciertos[1] > self.aciertos[2]:
            ganador_nombre = self.j1["nombre"]
            ganador_color = "#22D3EE"
        elif self.aciertos[2] > self.aciertos[1]:
            ganador_nombre = self.j2["nombre"]
            ganador_color = "#F472B6"
        else:
            ganador_nombre = "¡Empate!"
            ganador_color = "#FACC15"

        lbl = QLabel(f"<b style='font-size:28px; color:{ganador_color};'>{ganador_nombre}</b>")
        lbl.setAlignment(Qt.AlignCenter)
        self.pila.addWidget(lbl)

        marcador = QLabel(
            f"<div style='font-size:20px;'>"
            f"<b>{self.j1['nombre']}:</b> {self.aciertos[1]} aciertos<br>"
            f"<b>{self.j2['nombre']}:</b> {self.aciertos[2]} aciertos"
            f"</div>"
        )
        marcador.setObjectName("tarjeta")
        marcador.setAlignment(Qt.AlignCenter)
        self.pila.addWidget(marcador)

        # Registrar puntuación en el ranking
        try:
            self.db.agregar_ranking_para(self.j1["id"], self.aciertos[1])
            self.db.agregar_ranking_para(self.j2["id"], self.aciertos[2])
        except Exception:
            pass

        self.pila.addStretch()

        btn_revancha = QPushButton("🔄  Revancha")
        btn_revancha.setObjectName("botonPrimario")
        btn_revancha.setMinimumHeight(48)
        btn_revancha.setCursor(Qt.PointingHandCursor)
        btn_revancha.clicked.connect(self._empezar)
        self.pila.addWidget(btn_revancha)

        btn_volver = QPushButton("← Volver al inicio")
        btn_volver.setObjectName("botonSecundario")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.clicked.connect(lambda: self.ventana._ir_a(0))
        self.pila.addWidget(btn_volver)

    def _abandonar(self):
        r = QMessageBox.question(self, "Abandonar", "¿Seguro que quieres abandonar el duelo?")
        if r == QMessageBox.Yes:
            self.ventana._ir_a(0)
