"""Ventana principal — temas dinámicos, calidad gráfica y tienda con mercader."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QStackedWidget, QMessageBox, QFrame, QScrollArea,
    QGridLayout, QComboBox, QCheckBox, QSpinBox, QLineEdit
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint
from PySide6.QtGui import QKeySequence, QShortcut, QFont

from logic.motor_preguntas import BancoPreguntas, cargar_json, ruta_recurso
from logic.configuracion import TEMAS_DISPONIBLES, listar_calidades, es_tema_claro
from ui.widgets.tarjeta_pregunta import TarjetaPregunta
from ui.widgets.animaciones import (
    BarraXPAnimada, aplicar_sombra, mostrar_toast, AvatarCircular, AvatarWidget
)
from ui.dialogo_avatar_custom import DialogoAvatarCustom
from logic.avatares_custom import es_ruta_custom, obtener_ruta_custom
from ui.widgets.fondo_animado import WidgetConFondo
from ui.widgets.mercader import Mercader
from ui.pantalla_ranking import PantallaRanking
from ui.pantalla_duelo import PantallaDuelo
from ui.pantalla_duelo_online import PantallaDueloOnline


class VentanaPrincipal(QMainWindow):
    def __init__(self, db, leitner, gam):
        super().__init__()
        self.db = db
        self.leitner = leitner
        self.gam = gam
        self.banco = BancoPreguntas()
        self.avatares = cargar_json("data/avatares.json")
        self.logros = cargar_json("data/logros.json")
        self.tienda_items = cargar_json("data/tienda.json")

        self.setWindowTitle("MECANIA 4ESO — Máquinas y Mecanismos")
        self.resize(1300, 720)
        self.setMinimumSize(1000, 640)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.sesion_ids = []
        self.sesion_idx = 0
        self.sesion_aciertos = 0
        self.sesion_fallos = 0
        self.sesion_racha = 0
        self.sesion_xp = 0
        self.sesion_monedas = 0
        self.sesion_modo = "estudio"
        self.vidas = 3
        self.falladas_sesion = []

        self._construir_inicio()
        self._construir_avatares()
        self._construir_juego()
        self._construir_tienda()
        self._construir_logros()
        self._construir_estadisticas()
        self._construir_ajustes()
        self.pantalla_ranking = PantallaRanking(self, db)
        self.pantalla_duelo = PantallaDuelo(self, db, self.banco)
        self.pantalla_duelo_online = PantallaDueloOnline(self, db, self.banco)
        self.stack.addWidget(self.pantalla_ranking)
        self.stack.addWidget(self.pantalla_duelo)
        self.stack.addWidget(self.pantalla_duelo_online)

        QShortcut(QKeySequence("F11"), self, activated=self._toggle_fullscreen)
        QShortcut(QKeySequence("Ctrl+Q"), self, activated=self.close)

        self._aplicar_config_inicial()

    # ==================== CONFIG INICIAL ====================
    def _aplicar_config_inicial(self):
        j = self.db.jugador()
        if not j:
            return
        calidad = j.get("calidad", "medio") if isinstance(j, dict) else "medio"
        tema = j.get("tema", "oscuro")
        self.aplicar_tema(tema)
        self.aplicar_calidad(calidad)

    def ajustar_a_pantalla(self, pantalla):
        w, h = pantalla.width(), pantalla.height()
        ancho = min(w - 30, 1300)
        alto = min(h - 30, 720)
        self.resize(ancho, alto)
        self.move((w - ancho) // 2, (h - alto) // 2)

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    # ==================== INICIO ====================
    def _construir_inicio(self):
        w = WidgetConFondo()
        v = QVBoxLayout(w)
        v.setContentsMargins(30, 18, 30, 18)
        v.setSpacing(10)

        cab = QHBoxLayout()
        cab.setSpacing(10)
        titulo = QLabel("⚙️ MECANIA 4ESO")
        titulo.setObjectName("titulo")
        aplicar_sombra(titulo, blur=30, offset_y=3, alpha=150)
        cab.addWidget(titulo)
        cab.addStretch()

        self.btn_logout = QPushButton("⎋")
        self.btn_logout.setObjectName("esquina")
        self.btn_logout.setFixedSize(36, 36)
        self.btn_logout.setToolTip("Cerrar sesión")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.clicked.connect(self._cerrar_sesion)
        cab.addWidget(self.btn_logout)

        self.btn_fullscreen = QPushButton("⛶")
        self.btn_fullscreen.setObjectName("esquina")
        self.btn_fullscreen.setFixedSize(36, 36)
        self.btn_fullscreen.setToolTip("Pantalla completa (F11)")
        self.btn_fullscreen.setCursor(Qt.PointingHandCursor)
        self.btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        cab.addWidget(self.btn_fullscreen)
        v.addLayout(cab)

        sub = QLabel("Domina las 100 preguntas de Máquinas y Mecanismos")
        sub.setObjectName("subtitulo")
        sub.setAlignment(Qt.AlignCenter)
        v.addWidget(sub)

        # Carta de jugador (estilo carta coleccionable)
        carta = QFrame()
        carta.setObjectName("cartaJugador")
        cv = QHBoxLayout(carta)
        cv.setContentsMargins(20, 14, 20, 14)
        cv.setSpacing(16)

        self.avatar_widget = AvatarWidget("🍎", diametro=76)
        self.avatar_widget.setCursor(Qt.PointingHandCursor)
        self.avatar_widget.setToolTip("Clic para cambiar avatar")
        self.avatar_widget.mousePressEvent = lambda e: self._ir_a(1)
        cv.addWidget(self.avatar_widget)

        col_info = QVBoxLayout()
        col_info.setSpacing(2)
        self.lbl_jugador = QLabel()
        self.lbl_jugador.setObjectName("infoJugador")
        self.lbl_jugador.setWordWrap(True)
        col_info.addWidget(self.lbl_jugador)
        cv.addLayout(col_info, 1)

        # Sello nivel (círculo a la derecha)
        self.lbl_sello = QLabel()
        self.lbl_sello.setObjectName("selloNivel")
        self.lbl_sello.setAlignment(Qt.AlignCenter)
        self.lbl_sello.setFixedSize(72, 72)
        cv.addWidget(self.lbl_sello)

        aplicar_sombra(carta, blur=26, offset_y=6, alpha=140)
        v.addWidget(carta)

        self.barra_xp = BarraXPAnimada()
        self.barra_xp.setMinimumHeight(22)
        aplicar_sombra(self.barra_xp, blur=16, offset_y=3, alpha=100)
        v.addWidget(self.barra_xp)

        # Grid de modos
        grid = QGridLayout()
        grid.setSpacing(8)
        botones = [
            ("📖", "Estudio", "Sin vidas, feedback", "estudio"),
            ("📝", "Examen", "50 preguntas", "examen"),
            ("⚡", "Contrarreloj", "Rápido", "contrarreloj"),
            ("💀", "Supervivencia", "3 vidas", "supervivencia"),
            ("🔁", "Repasar falladas", "Hasta dominarlas", "falladas"),
            ("🗓️", "Desafío diario", "10 preguntas, bonus", "diario"),
        ]
        for i, (emoji, nombre, desc, modo) in enumerate(botones):
            b = self._boton_modo(emoji, nombre, desc, modo)
            grid.addWidget(b, i // 3, i % 3)
        v.addLayout(grid)

        # Accesos secundarios
        grid2 = QGridLayout()
        grid2.setSpacing(8)
        secundarios = [
            ("🎨  Avatares", 1),
            ("🛒  Tienda", 3),
            ("🏆  Logros", 4),
            ("📊  Estadísticas", 5),
            ("⚙️  Ajustes", 6),
        ]
        for i, (texto, idx) in enumerate(secundarios):
            b = QPushButton(texto)
            b.setObjectName("botonSecundario")
            b.setMinimumHeight(42)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, j=idx: self._ir_a(j))
            aplicar_sombra(b, blur=14, offset_y=3, alpha=100)
            grid2.addWidget(b, 0, i)
        v.addLayout(grid2)

        grid3 = QGridLayout()
        grid3.setSpacing(8)
        destacados = [
            ("🏅  Ranking Global", 7),
            ("⚔️  Duelo local", 8),
            ("🌐  Duelo ONLINE (LAN)", 9),
        ]
        for i, (texto, idx) in enumerate(destacados):
            b = QPushButton(texto)
            b.setObjectName("botonDestacado")
            b.setMinimumHeight(48)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, j=idx: self._ir_a(j))
            aplicar_sombra(b, blur=18, offset_y=4, alpha=120)
            grid3.addWidget(b, 0, i)
        v.addLayout(grid3)

        v.addStretch()
        self.stack.addWidget(w)

    def _boton_modo(self, emoji, nombre, desc, modo):
        b = QPushButton()
        b.setObjectName(f"botonModo_{modo}")   # ← el color lo pone el QSS
        b.setMinimumHeight(66)
        b.setCursor(Qt.PointingHandCursor)
        b.setText(f"{emoji}  {nombre}\n     {desc}")
        b.clicked.connect(lambda _=False, m=modo: self.iniciar_sesion(m))
        aplicar_sombra(b, blur=18, offset_y=4, alpha=110)
        return b


    def _aplicar_avatar_en_widget(self, avatar_id):
        """Aplica el avatar al widget (emoji o imagen custom)."""
        if es_ruta_custom(avatar_id):
            ruta = obtener_ruta_custom(avatar_id)
            self.avatar_widget.set_contenido(ruta, es_ruta=True)
            return next((a for a in self.avatares if a["id"] == "A1"), self.avatares[0])
        av = next((a for a in self.avatares if a["id"] == avatar_id), self.avatares[0])
        self.avatar_widget.set_contenido(av["emoji"], es_ruta=False)
        return av

    def actualizar_inicio(self):
        j = self.db.jugador()
        if not j:
            return
        dominadas = self.db.contar_dominadas()
        total = self.banco.total()
        avatar = self._aplicar_avatar_en_widget(j.get("avatar", "A1"))
        import datetime as _dt
        _h = _dt.datetime.now().hour
        if _h < 6: saludo = '🌙 Trasnochando'
        elif _h < 13: saludo = '☀️ Buenos días'
        elif _h < 20: saludo = '🌤️ Buenas tardes'
        else: saludo = '🌆 Buenas noches'
        self.lbl_jugador.setText(
            f"<span style='font-size:17px; font-weight:800;'>{j['nombre']}</span>"
            f"  <span style='font-size:13px; opacity:0.7;'>·  {avatar['nombre']}</span><br>"
            f"<span style='font-size:13px;'>Rango: <b>{j['rango']}</b></span><br>"
            f"<span style='font-size:13px;'>⭐ {j['xp']} XP  ·  💰 {j['monedas']} monedas"
            f"  ·  📚 {dominadas}/{total} dominadas</span>"
        )
        self.lbl_sello.setText(f"<b style='font-size:22px;'>{j['nivel']}</b><br>"
                               f"<span style='font-size:10px;'>NIVEL</span>")
        from logic.gamificacion import xp_para_nivel
        na = xp_para_nivel(j["nivel"])
        ns = xp_para_nivel(j["nivel"] + 1)
        prog = int(100 * (j["xp"] - na) / (ns - na)) if ns > na else 0
        self.barra_xp.setFormat(f"Nivel {j['nivel']} → {j['nivel']+1}   ({prog}%)")
        self.barra_xp.animar_a(max(0, min(100, prog)))
        from logic.gamificacion import consejo_aleatorio
        self.lbl_jugador.setToolTip(consejo_aleatorio())

    # ==================== AVATARES ====================
    def _construir_avatares(self):
        w = WidgetConFondo()
        v = QVBoxLayout(w)
        v.setContentsMargins(30, 15, 30, 15)
        v.setSpacing(10)

        cab = QHBoxLayout()
        btn = QPushButton("← Volver")
        btn.setObjectName("botonSecundario")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._ir_a(0))
        cab.addWidget(btn)
        cab.addStretch()
        tit = QLabel("🎨  Elige tu avatar")
        tit.setObjectName("titulo")
        cab.addWidget(tit)
        cab.addStretch()
        v.addLayout(cab)

        self.lbl_monedas_av = QLabel()
        self.lbl_monedas_av.setObjectName("hud")
        self.lbl_monedas_av.setAlignment(Qt.AlignCenter)
        v.addWidget(self.lbl_monedas_av)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        cont = QWidget()
        cont.setStyleSheet("background: transparent;")
        self.av_grid = QGridLayout(cont)
        self.av_grid.setSpacing(10)
        scroll.setWidget(cont)
        v.addWidget(scroll, 1)
        self.stack.addWidget(w)

    def actualizar_avatares(self):
        j = self.db.jugador()
        if not j:
            return
        self.lbl_monedas_av.setText(f"💰 {j['monedas']} monedas disponibles")
        while self.av_grid.count():
            it = self.av_grid.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        fila = col = 0
        for a in self.avatares:
            tiene = a["precio"] == 0 or self.db.tiene_compra("av_" + a["id"])
            es_actual = j.get("avatar") == a["id"]
            card = self._card_avatar(a, tiene, es_actual)
            self.av_grid.addWidget(card, fila, col)
            col += 1
            if col >= 5:
                col = 0
                fila += 1
        # Tarjeta especial para subir imagen propia
        card_custom = QFrame()
        card_custom.setObjectName("cardAvatarActual")
        card_custom.setMinimumHeight(180)
        ccv = QVBoxLayout(card_custom)
        ccv.setContentsMargins(10, 10, 10, 10)
        ccv.setSpacing(4)
        lbl_icono = QLabel("🖼️")
        from PySide6.QtGui import QFont as _QFont
        lbl_icono.setFont(_QFont("Noto Color Emoji", 32))
        lbl_icono.setAlignment(Qt.AlignCenter)
        ccv.addWidget(lbl_icono)
        lbl_nom = QLabel("Imagen propia")
        lbl_nom.setObjectName("nombreAvatar")
        lbl_nom.setAlignment(Qt.AlignCenter)
        ccv.addWidget(lbl_nom)
        btn_subir = QPushButton("📂  Subir imagen")
        btn_subir.setObjectName("botonCard")
        btn_subir.setCursor(Qt.PointingHandCursor)
        btn_subir.clicked.connect(self._subir_avatar_custom)
        ccv.addWidget(btn_subir)
        aplicar_sombra(card_custom, blur=14, offset_y=3, alpha=110)
        self.av_grid.addWidget(card_custom, fila, col)

    def _card_avatar(self, a, tiene, es_actual):
        card = QFrame()
        if es_actual:
            card.setObjectName("cardAvatarActual")
        elif tiene:
            card.setObjectName("cardAvatarTiene")
        else:
            card.setObjectName("cardAvatarBloqueado")
        card.setMinimumHeight(180)
        cv = QVBoxLayout(card)
        cv.setContentsMargins(10, 10, 10, 10)
        cv.setSpacing(4)
        av = AvatarCircular(a["emoji"], diametro=56)
        cv.addWidget(av, alignment=Qt.AlignCenter)
        nombre = QLabel(a["nombre"])
        nombre.setObjectName("nombreAvatar")
        nombre.setAlignment(Qt.AlignCenter)
        cv.addWidget(nombre)
        estado = QLabel("✓ EN USO" if es_actual else ("🔓 Desbloqueado" if tiene else f"💰 {a['precio']}"))
        estado.setObjectName("estadoAvatarActual" if es_actual else ("estadoAvatarTiene" if tiene else "estadoAvatarBloqueado"))
        estado.setAlignment(Qt.AlignCenter)
        cv.addWidget(estado)
        btn = QPushButton("En uso" if es_actual else ("Seleccionar" if tiene else "Comprar"))
        btn.setObjectName("botonCard")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setEnabled(not es_actual)
        btn.clicked.connect(lambda _=False, av=a: self._elegir_avatar(av))
        cv.addWidget(btn)
        aplicar_sombra(card, blur=14, offset_y=3, alpha=110)
        return card

    def _elegir_avatar(self, a):
        tiene = a["precio"] == 0 or self.db.tiene_compra("av_" + a["id"])
        if not tiene:
            if not self.gam.gastar_monedas(a["precio"]):
                mostrar_toast(self, "❌ Monedas insuficientes", "error")
                return
            self.db.registrar_compra("av_" + a["id"])
            mostrar_toast(self, f"✅ Compraste a {a['nombre']}", "exito")
        self.db.actualizar_jugador(avatar=a["id"])
        mostrar_toast(self, f"🎨 Avatar: {a['nombre']}", "exito")
        self.actualizar_avatares()
        self.actualizar_inicio()

    # ==================== JUEGO ====================
    def _construir_juego(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(20, 12, 20, 12)
        v.setSpacing(8)

        cab = QHBoxLayout()
        self.lbl_vidas = QLabel("❤️❤️❤️"); self.lbl_vidas.setObjectName("hud")
        self.lbl_racha = QLabel("🔥 0"); self.lbl_racha.setObjectName("hud")
        self.lbl_xp = QLabel("⭐ 0"); self.lbl_xp.setObjectName("hud")
        self.lbl_progreso = QLabel("1/10"); self.lbl_progreso.setObjectName("hud")
        for h in (self.lbl_vidas, self.lbl_racha, self.lbl_xp, self.lbl_progreso):
            aplicar_sombra(h, blur=12, offset_y=2, alpha=90)
        cab.addWidget(self.lbl_vidas)
        cab.addWidget(self.lbl_racha)
        cab.addWidget(self.lbl_xp)
        cab.addStretch()
        cab.addWidget(self.lbl_progreso)
        v.addLayout(cab)

        self.tarjeta = TarjetaPregunta(self)
        v.addWidget(self.tarjeta, 1)

        btn_volver = QPushButton("← Salir")
        btn_volver.setObjectName("botonSecundario")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.clicked.connect(lambda: self._ir_a(0))
        v.addWidget(btn_volver, alignment=Qt.AlignLeft)
        self.stack.addWidget(w)

    def iniciar_sesion(self, modo):
        self.sesion_modo = modo
        n = 50 if modo == "examen" else (10 if modo == "diario" else 15)
        if modo == "falladas":
            ids = self.leitner.preguntas_para_repaso_hoy() or self.db.listar_falladas()
            if not ids:
                mostrar_toast(self, "🎉 ¡No tienes falladas pendientes!", "exito")
                return
            self.sesion_ids = ids[:n]
        else:
            self.sesion_ids = self.leitner.seleccionar_sesion(self.banco.todas_ids(), n=n)
        self.sesion_idx = 0
        self.sesion_aciertos = 0
        self.sesion_fallos = 0
        self.sesion_racha = 0
        self.sesion_xp = 0
        self.sesion_monedas = 0
        self.vidas = 3
        self.falladas_sesion = []
        self._ir_a(2)
        self._cargar_pregunta_actual()

    def _cargar_pregunta_actual(self):
        if self.sesion_idx >= len(self.sesion_ids):
            self._terminar_sesion()
            return
        pid = self.sesion_ids[self.sesion_idx]
        p = self.banco.obtener(pid)
        self.lbl_progreso.setText(f"{self.sesion_idx+1}/{len(self.sesion_ids)}")
        self.lbl_vidas.setText("❤️" * self.vidas + "🖤" * (3 - self.vidas))
        self.lbl_racha.setText(f"🔥 {self.sesion_racha}")
        self.lbl_xp.setText(f"⭐ {self.sesion_xp}")
        self.tarjeta.mostrar(p, self._responder)

    def _responder(self, idx, confianza):
        pid = self.sesion_ids[self.sesion_idx]
        p = self.banco.obtener(pid)
        acierto = (idx == p["c"])
        self.leitner.registrar_respuesta(pid, acierto, confianza)
        if acierto:
            self.sesion_aciertos += 1
            self.sesion_racha += 1
            base = {"facil": 10, "media": 20, "dificil": 30}.get(p["d"], 10)
            res = self.gam.otorgar_xp(base, self.sesion_racha)
            self.sesion_xp += res["xp_ganada"]
            self.sesion_monedas += 5
            self.gam.otorgar_monedas(5)
            if res["subio_nivel"]:
                QTimer.singleShot(300, lambda: mostrar_toast(
                    self, f"🎉 ¡Nivel {res['nivel']}!", "exito", 2200))
        else:
            self.sesion_fallos += 1
            self.sesion_racha = 0
            self.falladas_sesion.append(pid)
            if self.sesion_modo in ("examen", "supervivencia", "contrarreloj"):
                self.vidas -= 1
                if self.vidas <= 0:
                    self.tarjeta.mostrar_feedback(acierto, p)
                    QTimer.singleShot(1800, self._terminar_sesion)
                    return
        self.tarjeta.mostrar_feedback(acierto, p)
        QTimer.singleShot(2000, self._siguiente)

    def _siguiente(self):
        self.sesion_idx += 1
        self._cargar_pregunta_actual()

    def _terminar_sesion(self):
        self.db.registrar_sesion(self.sesion_modo, self.sesion_aciertos,
                                 self.sesion_fallos, self.sesion_xp, self.sesion_monedas)
        dominadas = self.db.contar_dominadas()
        bloques = self.db.estadisticas_por_bloque(self.banco.mapa_bloques)
        b5 = bloques.get("B5", (0, 1))
        ctx = {
            "racha": self.sesion_racha,
            "sin_fallos": self.sesion_fallos == 0 and self.sesion_aciertos > 0,
            "dominadas_total": dominadas,
            "modo": self.sesion_modo,
            "aciertos": self.sesion_aciertos,
            "bloque_B5_dominado": b5[1] > 0 and b5[0] / b5[1] > 0.8,
        }
        nuevos = self.gam.comprobar_logros(ctx)
        texto = (f"<h2>Sesión terminada</h2>"
                 f"<p>Aciertos: <b>{self.sesion_aciertos}</b><br>"
                 f"Fallos: <b>{self.sesion_fallos}</b><br>"
                 f"XP ganada: <b>{self.sesion_xp}</b><br>"
                 f"Monedas: <b>{self.sesion_monedas}</b><br>"
                 f"Dominadas: <b>{dominadas}/{self.banco.total()}</b></p>")
        if nuevos:
            nombres = [l["nombre"] for l in self.logros if l["id"] in nuevos]
            texto += f"<p>🏆 ¡Nuevos logros!: {', '.join(nombres)}</p>"
        if self.falladas_sesion:
            texto += f"<p>⚠️ {len(self.falladas_sesion)} falladas se repetirán.</p>"
        QMessageBox.information(self, "Resultado", texto)
        self.actualizar_inicio()
        self._ir_a(0)

    # ==================== TIENDA (con mercader) ====================
    def _construir_tienda(self):
        w = WidgetConFondo()
        v = QVBoxLayout(w)
        v.setContentsMargins(30, 15, 30, 15)
        v.setSpacing(10)

        cab = QHBoxLayout()
        btn = QPushButton("← Volver")
        btn.setObjectName("botonSecundario")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._ir_a(0))
        cab.addWidget(btn)
        cab.addStretch()
        tit = QLabel("🛒  La Tienda del Ferroviario")
        tit.setObjectName("titulo")
        cab.addWidget(tit)
        cab.addStretch()
        v.addLayout(cab)

        # Mercader arriba
        self.mercader = Mercader()
        v.addWidget(self.mercader)

        self.lbl_monedas_t = QLabel()
        self.lbl_monedas_t.setObjectName("hud")
        self.lbl_monedas_t.setAlignment(Qt.AlignCenter)
        v.addWidget(self.lbl_monedas_t)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        cont = QWidget()
        cont.setStyleSheet("background: transparent;")
        self.tienda_grid = QGridLayout(cont)
        self.tienda_grid.setSpacing(12)
        scroll.setWidget(cont)
        v.addWidget(scroll, 1)
        self.stack.addWidget(w)

    def actualizar_tienda(self):
        j = self.db.jugador()
        if not j:
            return
        self.lbl_monedas_t.setText(f"💰 Tienes {j['monedas']} monedas")
        # Frase aleatoria del mercader según monedas
        if j["monedas"] < 100:
            self.mercader.decir("¡Vaya, viajero! Traes los bolsillos vacíos. Acierta más preguntas y vuelve.")
        elif j["monedas"] < 500:
            self.mercader.decir("Veo brillo en tus bolsillos... ¿Qué te tienta hoy, joven mecánico?")
        else:
            self.mercader.decir("¡Oooh! ¡Un cliente de categoría! Tengo maravillas para ti.")

        while self.tienda_grid.count():
            it = self.tienda_grid.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        fila = col = 0
        for it in self.tienda_items:
            tiene = it["precio"] == 0 or self.db.tiene_compra(it["id"])
            card = self._card_tienda(it, tiene)
            self.tienda_grid.addWidget(card, fila, col)
            col += 1
            if col >= 3:
                col = 0
                fila += 1

    def _card_tienda(self, it, tiene):
        card = QFrame()
        card.setObjectName("cardTienda")
        cv = QVBoxLayout(card)
        cv.setContentsMargins(14, 14, 14, 14)
        cv.setSpacing(6)
        icono = {"tema": "🎨", "sonido": "🎵", "pista": "💡"}.get(it["tipo"], "📦")
        nom = QLabel(f"{icono}  {it['nombre']}")
        nom.setObjectName("tituloCard")
        cv.addWidget(nom)
        pr = QLabel(f"{it['precio']} 💰")
        pr.setObjectName("precioCard")
        cv.addWidget(pr)
        btn = QPushButton("✅ Ya lo tienes" if tiene else "💎 Comprar")
        btn.setObjectName("botonCard")
        btn.setEnabled(not tiene)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda _=False, item=it: self._comprar_item(item))
        cv.addWidget(btn)
        aplicar_sombra(card, blur=16, offset_y=4, alpha=110)
        return card

    def _comprar_item(self, it):
        if not self.gam.gastar_monedas(it["precio"]):
            mostrar_toast(self, "❌ Monedas insuficientes", "error")
            self.mercader.decir("¡No tienes suficientes monedas, amigo! Sigue estudiando.")
            return
        self.db.registrar_compra(it["id"])
        if it["tipo"] == "tema":
            self.db.actualizar_jugador(tema=it["valor"])
            self.aplicar_tema(it["valor"])
        mostrar_toast(self, f"✅ {it['nombre']} desbloqueado", "exito")
        self.mercader.decir(f"¡Excelente elección! Disfruta de {it['nombre']}.")
        self.actualizar_tienda()
        self.actualizar_inicio()

    # ==================== LOGROS ====================
    def _construir_logros(self):
        w = WidgetConFondo()
        v = QVBoxLayout(w)
        v.setContentsMargins(30, 15, 30, 15)
        v.setSpacing(10)
        tit = QLabel("🏆  Logros")
        tit.setObjectName("titulo")
        tit.setAlignment(Qt.AlignCenter)
        v.addWidget(tit)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        cont = QWidget()
        cont.setStyleSheet("background: transparent;")
        self.logros_grid = QGridLayout(cont)
        self.logros_grid.setSpacing(10)
        scroll.setWidget(cont)
        v.addWidget(scroll, 1)
        btn = QPushButton("← Volver")
        btn.setObjectName("botonSecundario")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._ir_a(0))
        v.addWidget(btn, alignment=Qt.AlignLeft)
        self.stack.addWidget(w)

    def actualizar_logros(self):
        while self.logros_grid.count():
            it = self.logros_grid.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        desb = self.db.listar_logros()
        fila = col = 0
        for l in self.logros:
            tiene = bool(desb.get(l["id"], {}).get("desbloqueado"))
            card = QFrame()
            card.setObjectName("cardLogroOK" if tiene else "cardLogroLock")
            card.setMinimumHeight(100)
            cv = QVBoxLayout(card)
            cv.setContentsMargins(12, 10, 12, 10)
            emoji = "🔓" if tiene else "🔒"
            nom = QLabel(f"{emoji}  {l['emoji']}  {l['nombre']}")
            nom.setObjectName("tituloCard")
            cv.addWidget(nom)
            desc = QLabel(l["descripcion"])
            desc.setObjectName("descCard")
            desc.setWordWrap(True)
            cv.addWidget(desc)
            aplicar_sombra(card, blur=14, offset_y=3, alpha=100)
            self.logros_grid.addWidget(card, fila, col)
            col += 1
            if col >= 3:
                col = 0
                fila += 1

    # ==================== ESTADÍSTICAS ====================
    def _construir_estadisticas(self):
        w = WidgetConFondo()
        v = QVBoxLayout(w)
        v.setContentsMargins(30, 15, 30, 15)
        v.setSpacing(10)
        tit = QLabel("📊  Estadísticas")
        tit.setObjectName("titulo")
        tit.setAlignment(Qt.AlignCenter)
        v.addWidget(tit)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        cont = QWidget()
        cont.setStyleSheet("background: transparent;")
        self.stats_grid = QGridLayout(cont)
        self.stats_grid.setSpacing(8)
        scroll.setWidget(cont)
        v.addWidget(scroll, 1)
        btn = QPushButton("← Volver")
        btn.setObjectName("botonSecundario")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._ir_a(0))
        v.addWidget(btn, alignment=Qt.AlignLeft)
        self.stack.addWidget(w)

    def actualizar_estadisticas(self):
        while self.stats_grid.count():
            it = self.stats_grid.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        prog = self.db.estadisticas_por_bloque(self.banco.mapa_bloques)
        titulos = {
            "B1": "Fuerza, masa y peso", "B2": "Conceptos generales",
            "B3": "Tipos de movimiento", "B4": "Máquinas simples",
            "B5": "Palancas", "B6": "Poleas y polipastos",
            "B7": "Ruedas y correas", "B8": "Engranajes",
            "B9": "Tornillo sinfín", "B10": "Piñón-cremallera",
            "B11": "Tornillo-tuerca", "B12": "Levas y excéntricas",
            "B13": "Biela-manivela y cigüeñal", "B14": "Transmisión",
        }
        fila = 0
        for b in sorted(prog.keys()):
            a, t = prog[b]
            pct = int(100 * a / t) if t else 0
            if pct < 40:
                card = QFrame(); card.setObjectName("cardStatBajo")
            elif pct < 70:
                card = QFrame(); card.setObjectName("cardStatMedio")
            else:
                card = QFrame(); card.setObjectName("cardStatAlto")
            cv = QVBoxLayout(card)
            cv.setContentsMargins(14, 8, 14, 8)
            cv.setSpacing(4)
            nombre = QLabel(f"<b>{b}</b>  —  {titulos.get(b, b)}")
            nombre.setObjectName("tituloCard")
            cv.addWidget(nombre)
            barra = BarraXPAnimada()
            barra.setValue(pct)
            barra.setFormat(f"{a}/{t}  ({pct}%)")
            barra.setMinimumHeight(20)
            cv.addWidget(barra)
            aplicar_sombra(card, blur=12, offset_y=3, alpha=100)
            self.stats_grid.addWidget(card, fila, 0)
            fila += 1

    # ==================== AJUSTES ====================
    def _construir_ajustes(self):
        w = WidgetConFondo()
        v = QVBoxLayout(w)
        v.setContentsMargins(40, 20, 40, 20)
        v.setSpacing(12)
        tit = QLabel("⚙️  Ajustes")
        tit.setObjectName("titulo")
        tit.setAlignment(Qt.AlignCenter)
        v.addWidget(tit)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        cont = QWidget()
        cont.setStyleSheet("background: transparent;")
        form = QVBoxLayout(cont)
        form.setSpacing(10)

        # Nombre
        form.addWidget(self._label_form("Nombre de usuario"))
        self.input_nombre = QLineEdit()
        self.input_nombre.setReadOnly(True)
        form.addWidget(self.input_nombre)

        # Tema
        form.addWidget(self._label_form("🎨 Tema visual"))
        temas_grid = QGridLayout()
        temas_grid.setSpacing(8)
        self.botones_tema = {}
        for i, t in enumerate(TEMAS_DISPONIBLES):
            b = QPushButton(f"{t['emoji']}  {t['nombre']}")
            b.setObjectName("botonTema")
            b.setCheckable(True)
            b.setMinimumHeight(52)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, tid=t["id"]: self._cambiar_tema_boton(tid))
            temas_grid.addWidget(b, i // 3, i % 3)
            self.botones_tema[t["id"]] = b
        form.addLayout(temas_grid)

        # Calidad gráfica
        form.addWidget(self._label_form("⚡ Calidad gráfica"))
        calidad_grid = QGridLayout()
        calidad_grid.setSpacing(8)
        self.botones_calidad = {}
        for i, c in enumerate(listar_calidades()):
            b = QPushButton(f"{c['emoji']}  {c['nombre']}\n{c['descripcion']}")
            b.setObjectName("botonCalidad")
            b.setCheckable(True)
            b.setMinimumHeight(60)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, cid=c["id"]: self._cambiar_calidad_boton(cid))
            calidad_grid.addWidget(b, 0, i)
            self.botones_calidad[c["id"]] = b
        form.addLayout(calidad_grid)

        # Fuente
        form.addWidget(self._label_form("🔤 Tamaño de fuente"))
        self.spin_fuente = QSpinBox()
        self.spin_fuente.setRange(10, 22)
        self.spin_fuente.valueChanged.connect(self._cambiar_fuente)
        form.addWidget(self.spin_fuente)

        # Sonido
        self.chk_sonido = QCheckBox("🔊 Sonidos activados")
        form.addWidget(self.chk_sonido)

        # Cambio contraseña
        form.addWidget(self._label_form("🔐 Cambiar contraseña"))
        self.pass_actual = QLineEdit()
        self.pass_actual.setPlaceholderText("Contraseña actual")
        self.pass_actual.setEchoMode(QLineEdit.Password)
        form.addWidget(self.pass_actual)
        self.pass_nueva = QLineEdit()
        self.pass_nueva.setPlaceholderText("Nueva contraseña")
        self.pass_nueva.setEchoMode(QLineEdit.Password)
        form.addWidget(self.pass_nueva)
        btn_pass = QPushButton("Actualizar contraseña")
        btn_pass.setObjectName("botonSecundario")
        btn_pass.setCursor(Qt.PointingHandCursor)
        btn_pass.clicked.connect(self._cambiar_password)
        form.addWidget(btn_pass)

        # Botones de sistema
        form.addWidget(self._label_form("🖥 Sistema"))
        btn_fs = QPushButton("⛶  Pantalla completa (F11)")
        btn_fs.setObjectName("botonSecundario")
        btn_fs.setCursor(Qt.PointingHandCursor)
        btn_fs.clicked.connect(self._toggle_fullscreen)
        form.addWidget(btn_fs)

        btn_reset = QPushButton("🗑️  Reiniciar progreso")
        btn_reset.setObjectName("botonPeligro")
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.clicked.connect(self._reset)
        form.addWidget(btn_reset)

        scroll.setWidget(cont)
        v.addWidget(scroll, 1)

        btn = QPushButton("← Volver")
        btn.setObjectName("botonSecundario")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._ir_a(0))
        v.addWidget(btn, alignment=Qt.AlignLeft)
        self.stack.addWidget(w)

    def _label_form(self, texto):
        l = QLabel(texto)
        l.setObjectName("labelForm")
        return l

    def actualizar_ajustes(self):
        j = self.db.jugador()
        if not j:
            return
        self.input_nombre.setText(j["nombre"])
        tema = j.get("tema", "oscuro")
        for tid, b in self.botones_tema.items():
            b.setChecked(tid == tema)
        calidad = j.get("calidad", "medio")
        for cid, b in self.botones_calidad.items():
            b.setChecked(cid == calidad)
        self.spin_fuente.blockSignals(True)
        self.spin_fuente.setValue(j.get("tamano_fuente", 14))
        self.spin_fuente.blockSignals(False)
        self.chk_sonido.setChecked(bool(j.get("sonido", 1)))

    def _cambiar_tema_boton(self, tema_id):
        self.aplicar_tema(tema_id)
        self.db.actualizar_jugador(tema=tema_id)
        self.actualizar_ajustes()
        mostrar_toast(self, f"🎨 Tema: {tema_id}", "exito", 1200)

    def _cambiar_calidad_boton(self, calidad_id):
        self.aplicar_calidad(calidad_id)
        self.db.actualizar_jugador(calidad=calidad_id)
        self.actualizar_ajustes()
        mostrar_toast(self, f"⚡ Calidad: {calidad_id}", "exito", 1200)

    def _cambiar_fuente(self, val):
        self.db.actualizar_jugador(tamano_fuente=val)
        f = self.font()
        f.setPointSize(val)
        self.setFont(f)

    def _cambiar_password(self):
        actual = self.pass_actual.text()
        nueva = self.pass_nueva.text()
        if not actual or not nueva:
            mostrar_toast(self, "❌ Rellena los dos campos", "error"); return
        ok, msg = self.db.cambiar_password(actual, nueva)
        if ok:
            mostrar_toast(self, "✅ Contraseña cambiada", "exito")
            self.pass_actual.clear()
            self.pass_nueva.clear()
        else:
            mostrar_toast(self, f"❌ {msg}", "error")

    def _reset(self):
        r = QMessageBox.question(self, "Reiniciar", "¿Borrar todo tu progreso?")
        if r == QMessageBox.Yes:
            self.db.resetear_progreso()
            self.actualizar_inicio()
            mostrar_toast(self, "🗑️ Progreso reiniciado", "aviso")

    def _cerrar_sesion(self):
        r = QMessageBox.question(self, "Cerrar sesión", "¿Seguro que quieres cerrar tu sesión?")
        if r == QMessageBox.Yes:
            self.db.logout()
            self.close()
    def _subir_avatar_custom(self):
        dlg = DialogoAvatarCustom(self.db, self)
        if dlg.exec() and dlg.ruta_importada:
            self.db.agregar_avatar_custom(dlg.ruta_importada)
            avatar_id = f"custom:{dlg.ruta_importada}"
            self.db.actualizar_jugador(avatar=avatar_id)
            mostrar_toast(self, "✅ Avatar personalizado aplicado", "exito")
            self.actualizar_avatares()
            self.actualizar_inicio()

    # ==================== TEMA Y CALIDAD ====================
    def aplicar_tema(self, nombre):
        if nombre not in [t["id"] for t in TEMAS_DISPONIBLES]:
            nombre = "oscuro"
        ruta = ruta_recurso(f"assets/qss/{nombre}.qss")
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            with open(ruta_recurso("assets/qss/oscuro.qss"), encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        # Aplicar tema a todos los fondos animados
        for w in self.findChildren(WidgetConFondo):
            if hasattr(w, "set_tema"):
                w.set_tema(nombre)

    def aplicar_calidad(self, calidad):
        """Aplica el nivel de calidad a todos los WidgetConFondo."""
        for widget in self.findChildren(WidgetConFondo):
            if hasattr(widget, "set_calidad"):
                widget.set_calidad(calidad)

    # ==================== UTIL ====================
    def _ir_a(self, indice):
        self.stack.setCurrentIndex(indice)
        if indice == 0: self.actualizar_inicio()
        elif indice == 1: self.actualizar_avatares()
        elif indice == 3: self.actualizar_tienda()
        elif indice == 4: self.actualizar_logros()
        elif indice == 5: self.actualizar_estadisticas()
        elif indice == 6: self.actualizar_ajustes()
        elif indice == 7: self.pantalla_ranking.recargar()
        elif indice == 8: self.pantalla_duelo._pantalla_configuracion()
        elif indice == 9: self.pantalla_duelo_online._pantalla_inicio()

    def showEvent(self, e):
        super().showEvent(e)
        self.actualizar_inicio()
