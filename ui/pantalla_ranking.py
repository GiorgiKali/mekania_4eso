"""Pantalla de Ranking Global — compite contra todos los usuarios."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.widgets.animaciones import aplicar_sombra, AvatarWidget, mostrar_toast
from ui.widgets.fondo_animado import WidgetConFondo
from logic.avatares_custom import es_ruta_custom, obtener_ruta_custom
from logic.motor_preguntas import cargar_json


class PantallaRanking(QWidget):
    def __init__(self, ventana, db):
        super().__init__(ventana)
        self.ventana = ventana
        self.db = db
        self._modo = "xp"
        self._construir()

    def _construir(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        fondo = WidgetConFondo()
        layout.addWidget(fondo)

        v = QVBoxLayout(fondo)
        v.setContentsMargins(30, 15, 30, 15)
        v.setSpacing(10)

        # Cabecera
        cab = QHBoxLayout()
        btn = QPushButton("← Volver")
        btn.setObjectName("botonSecundario")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self.ventana._ir_a(0))
        cab.addWidget(btn)
        cab.addStretch()
        tit = QLabel("🏆  Ranking Global")
        tit.setObjectName("titulo")
        cab.addWidget(tit)
        cab.addStretch()
        v.addLayout(cab)

        sub = QLabel("Compite contra los demás alumnos de la clase")
        sub.setObjectName("subtitulo")
        sub.setAlignment(Qt.AlignCenter)
        v.addWidget(sub)

        # Pestañas de categoría
        tabs = QHBoxLayout()
        tabs.setSpacing(8)
        self.botones = {}
        for cat, texto in [("xp", "⭐ Más XP"),
                           ("dominadas", "📚 Más dominadas"),
                           ("examen", "📝 Mejor examen")]:
            b = QPushButton(texto)
            b.setObjectName("tabRanking")
            b.setCheckable(True)
            b.setMinimumHeight(42)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, c=cat: self._cambiar_tab(c))
            tabs.addWidget(b)
            self.botones[cat] = b
        self.botones["xp"].setChecked(True)
        v.addLayout(tabs)

        # Lista
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        cont = QWidget()
        cont.setStyleSheet("background: transparent;")
        self.lista_grid = QVBoxLayout(cont)
        self.lista_grid.setSpacing(8)
        scroll.setWidget(cont)
        v.addWidget(scroll, 1)

        self.recargar()

    def _cambiar_tab(self, cat):
        for c, b in self.botones.items():
            b.setChecked(c == cat)
        self._modo = cat
        self.recargar()

    def recargar(self):
        while self.lista_grid.count():
            it = self.lista_grid.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        if self._modo == "xp":
            datos = self.db.ranking_por_xp(30)
            self._pintar_xp(datos)
        elif self._modo == "dominadas":
            datos = self.db.ranking_por_dominadas(30)
            self._pintar_dominadas(datos)
        else:
            datos = self.db.ranking_por_examen(30)
            self._pintar_examen(datos)

    def _pintar_xp(self, datos):
        jugador_actual = self.db.jugador()
        for i, d in enumerate(datos):
            color = self._color_pos(i)
            card = self._fila(
                pos=i + 1, nombre=d["nombre"],
                valor=f"⭐ {d['xp']} XP  ·  Nivel {d['nivel']}  ·  {d['rango']}",
                avatar_id=d["avatar"], color=color,
                es_actual=(jugador_actual and jugador_actual["nombre"] == d["nombre"])
            )
            self.lista_grid.addWidget(card)

    def _pintar_dominadas(self, datos):
        jugador_actual = self.db.jugador()
        total = 100
        for i, d in enumerate(datos):
            color = self._color_pos(i)
            card = self._fila(
                pos=i + 1, nombre=d["nombre"],
                valor=f"📚 {d['dominadas']}/{total} dominadas  ·  ⭐ {d['xp']} XP",
                avatar_id=d["avatar"], color=color,
                es_actual=(jugador_actual and jugador_actual["nombre"] == d["nombre"])
            )
            self.lista_grid.addWidget(card)

    def _pintar_examen(self, datos):
        jugador_actual = self.db.jugador()
        for i, d in enumerate(datos):
            color = self._color_pos(i)
            card = self._fila(
                pos=i + 1, nombre=d["nombre"],
                valor=f"📝 Mejor examen: {d['mejor']} aciertos",
                avatar_id=d["avatar"], color=color,
                es_actual=(jugador_actual and jugador_actual["nombre"] == d["nombre"])
            )
            self.lista_grid.addWidget(card)

    def _color_pos(self, i):
        if i == 0: return "#FACC15"   # oro
        if i == 1: return "#94A3B8"   # plata
        if i == 2: return "#B45309"   # bronce
        return "#22D3EE"

    def _fila(self, pos, nombre, valor, avatar_id, color, es_actual=False):
        card = QFrame()
        card.setObjectName("filaRankingActual" if es_actual else "filaRanking")
        card.setMinimumHeight(62)
        cv = QHBoxLayout(card)
        cv.setContentsMargins(14, 8, 14, 8)
        cv.setSpacing(12)

        # Posición
        lbl_pos = QLabel(f"#{pos}")
        lbl_pos.setFixedWidth(48)
        f = QFont()
        f.setPointSize(16)
        f.setBold(True)
        lbl_pos.setFont(f)
        lbl_pos.setStyleSheet(f"color: {color}; background: transparent;")
        lbl_pos.setAlignment(Qt.AlignCenter)
        cv.addWidget(lbl_pos)

        # Avatar
        av_widget = self._crear_avatar(avatar_id, color)
        cv.addWidget(av_widget)

        # Nombre + valor
        col = QVBoxLayout()
        col.setSpacing(0)
        lbl_n = QLabel(nombre)
        lbl_n.setStyleSheet("font-size: 15px; font-weight: 800; background: transparent;")
        col.addWidget(lbl_n)
        lbl_v = QLabel(valor)
        lbl_v.setStyleSheet("font-size: 12px; opacity: 0.75; background: transparent;")
        col.addWidget(lbl_v)
        cv.addLayout(col, 1)

        aplicar_sombra(card, blur=14, offset_y=3, alpha=110)
        return card

    def _crear_avatar(self, avatar_id, color):
        if es_ruta_custom(avatar_id):
            ruta = obtener_ruta_custom(avatar_id)
            return AvatarWidget(ruta, diametro=42, es_ruta=True)
        avatares = cargar_json("data/avatares.json")
        av = next((a for a in avatares if a["id"] == avatar_id), avatares[0])
        return AvatarWidget(av["emoji"], diametro=42)
