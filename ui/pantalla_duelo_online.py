"""Duelo online por LAN: dos PCs en la misma red juegan 1v1 en tiempo real."""
import random, time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QLineEdit, QComboBox, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer, QTimer as _T
from PySide6.QtGui import QGuiApplication

from ui.widgets.animaciones import aplicar_sombra, mostrar_toast, AvatarWidget
from ui.widgets.fondo_animado import WidgetConFondo
from logic.duelo_online import (
    ServidorDuelo, ClienteDuelo, obtener_ip_local, PUERTO_DEFECTO
)
from logic.motor_preguntas import cargar_json


class PantallaDueloOnline(QWidget):
    def __init__(self, ventana, db, banco):
        super().__init__(ventana)
        self.ventana = ventana
        self.db = db
        self.banco = banco

        self.servidor = None
        self.cliente = None
        self.es_host = False
        self.jugador_local = None
        self.jugador_remoto = None
        self.marcador = {"yo": 0, "otro": 0}

        # Estado del juego
        self.preguntas_duelo = []
        self.pregunta_idx = 0
        self.mi_turno = False
        self.respuesta_pendiente = False

        self._construir()

    def _construir(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        fondo = WidgetConFondo()
        layout.addWidget(fondo)
        self.pila = QVBoxLayout(fondo)
        self.pila.setContentsMargins(30, 15, 30, 15)
        self.pila.setSpacing(10)
        self._pantalla_inicio()

    # ==================== INICIO ====================
    def _limpiar(self):
        while self.pila.count():
            it = self.pila.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

    def _pantalla_inicio(self):
        self._cerrar_conexiones()
        self._limpiar()

        tit = QLabel("🌐  Duelo ONLINE (LAN)")
        tit.setObjectName("titulo")
        tit.setAlignment(Qt.AlignCenter)
        self.pila.addWidget(tit)

        sub = QLabel("Dos PCs en la misma red WiFi compiten en directo")
        sub.setObjectName("subtitulo")
        sub.setAlignment(Qt.AlignCenter)
        self.pila.addWidget(sub)

        # Aviso sesión
        jugador = self.db.jugador()
        if not jugador:
            aviso = QLabel("⚠️  Debes iniciar sesión antes de jugar online.")
            aviso.setObjectName("tarjeta")
            aviso.setAlignment(Qt.AlignCenter)
            self.pila.addWidget(aviso)
            b = QPushButton("← Volver")
            b.setObjectName("botonSecundario")
            b.clicked.connect(lambda: self.ventana._ir_a(0))
            self.pila.addWidget(b)
            return

        self.jugador_local = jugador
        self.mi_nombre = jugador["nombre"]

        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta")
        tv = QVBoxLayout(tarjeta)
        tv.setContentsMargins(20, 20, 20, 20)
        tv.setSpacing(14)

        # Modo: host o cliente
        tv.addWidget(self._label("Modo de juego"))
        self.combo_modo = QComboBox()
        self.combo_modo.addItem("🏠  Ser Host (crear partida)", "host")
        self.combo_modo.addItem("🔌  Unirse (introducir IP del host)", "cliente")
        self.combo_modo.currentIndexChanged.connect(self._cambiar_modo)
        tv.addWidget(self.combo_modo)

        # IP del host (solo visible en modo cliente)
        self.lbl_ip_hint = QLabel("Mi IP local: " + obtener_ip_local())
        self.lbl_ip_hint.setObjectName("hud")
        self.lbl_ip_hint.setAlignment(Qt.AlignCenter)
        tv.addWidget(self.lbl_ip_hint)

        self.lbl_ip_input = self._label("IP del host (solo si te unes)")
        tv.addWidget(self.lbl_ip_input)
        self.input_ip = QLineEdit()
        self.input_ip.setPlaceholderText("Ej: 192.168.1.42")
        self.input_ip.setText("192.168.1.")
        tv.addWidget(self.input_ip)
        self.lbl_ip_input.hide()
        self.input_ip.hide()

        # Número de preguntas
        tv.addWidget(self._label("Número de preguntas"))
        self.combo_n = QComboBox()
        for n in (5, 10, 15, 20):
            self.combo_n.addItem(f"{n} preguntas", n)
        self.combo_n.setCurrentIndex(1)
        tv.addWidget(self.combo_n)

        aplicar_sombra(tarjeta, blur=20, offset_y=5, alpha=130)
        self.pila.addWidget(tarjeta)

        self.btn_conectar = QPushButton("▶  CREAR PARTIDA / CONECTAR")
        self.btn_conectar.setObjectName("botonPrimario")
        self.btn_conectar.setMinimumHeight(50)
        self.btn_conectar.setCursor(Qt.PointingHandCursor)
        self.btn_conectar.clicked.connect(self._iniciar_conexion)
        self.pila.addWidget(self.btn_conectar)

        self.lbl_estado = QLabel("")
        self.lbl_estado.setAlignment(Qt.AlignCenter)
        self.lbl_estado.setObjectName("hud")
        self.pila.addWidget(self.lbl_estado)

        self.pila.addStretch()

        b = QPushButton("← Volver")
        b.setObjectName("botonSecundario")
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(lambda: self.ventana._ir_a(0))
        self.pila.addWidget(b, alignment=Qt.AlignLeft)

    def _label(self, texto):
        l = QLabel(texto)
        l.setObjectName("labelForm")
        return l

    def _cambiar_modo(self):
        es_cliente = self.combo_modo.currentData() == "cliente"
        self.lbl_ip_input.setVisible(es_cliente)
        self.input_ip.setVisible(es_cliente)
        self.lbl_ip_hint.setVisible(not es_cliente)

    # ==================== CONEXIÓN ====================
    def _iniciar_conexion(self):
        if not self.jugador_local:
            mostrar_toast(self, "❌ Inicia sesión primero", "error")
            return

        modo = self.combo_modo.currentData()
        if modo == "host":
            self.es_host = True
            self.servidor = ServidorDuelo(self._on_evento_servidor)
            ok, msg = self.servidor.iniciar(PUERTO_DEFECTO)
            if not ok:
                mostrar_toast(self, f"❌ {msg}", "error")
                return
            ip = obtener_ip_local()
            self.lbl_estado.setText(
                f"🟢 Esperando rival...\nDile a tu compañero que se conecte a:\n{ip}:{PUERTO_DEFECTO}"
            )
            self.btn_conectar.setEnabled(False)
        else:
            self.es_host = False
            ip = self.input_ip.text().strip()
            if not ip:
                mostrar_toast(self, "❌ Introduce la IP del host", "error")
                return
            self.cliente = ClienteDuelo(self._on_evento_cliente)
            ok, msg = self.cliente.conectar(ip, PUERTO_DEFECTO, nombre=self.mi_nombre)
            if not ok:
                mostrar_toast(self, f"❌ {msg}", "error")
                self.cliente = None
                return
            self.lbl_estado.setText("🟢 Conectando...")
            self.btn_conectar.setEnabled(False)

    # ==================== EVENTOS ====================
    def _on_evento_servidor(self, ev):
        QTimer.singleShot(0, lambda: self._procesar_evento(ev, es_host=True))

    def _on_evento_cliente(self, ev):
        QTimer.singleShot(0, lambda: self._procesar_evento(ev, es_host=False))

    def _procesar_evento(self, ev, es_host):
        t = ev.get("tipo")
        if t == "cliente_conectado":
            self.jugador_remoto = {"nombre": ev.get("nombre", "Rival")}
            self.lbl_estado.setText(f"🟢 ¡{self.jugador_remoto['nombre']} se ha unido!")
            self._empezar_partida_como_host()
        elif t == "iniciar_partida":
            # Cliente recibe preguntas y orden
            seed = ev["seed"]
            n = ev["n"]
            self.jugador_remoto = {"nombre": ev["nombre_host"]}
            self._preparar_preguntas(seed, n)
            self._pantalla_juego()
        elif t == "respuesta_cliente":
            # Host recibe respuesta del cliente
            self._procesar_respuesta_remota(ev["idx"], ev["acierto"])
        elif t == "respuesta_host":
            # Cliente recibe respuesta del host
            self._procesar_respuesta_remota(ev["idx"], ev["acierto"])
        elif t == "turno_siguiente":
            self._avanzar_turno_forzado(ev["pregunta_idx"])
        elif t == "fin_partida":
            self._mostrar_resultado_final(ev["marcador"])
        elif t == "desconectado":
            self._mostrar_desconexion()
        elif t == "error":
            mostrar_toast(self, f"❌ {ev.get('msg')}", "error")

    # ==================== HOST ====================
    def _empezar_partida_como_host(self):
        """Cuando se conecta el cliente, el host elige la semilla y la envía."""
        n = self.combo_n.currentData()
        seed = random.randint(1, 999999)
        self._preparar_preguntas(seed, n)
        self.servidor.enviar({
            "tipo": "iniciar_partida",
            "seed": seed,
            "n": n,
            "nombre_host": self.mi_nombre,
        })
        self._pantalla_juego()
        # El host empieza
        self.mi_turno = True
        QTimer.singleShot(400, self._activar_turno)

    # ==================== PREGUNTAS ====================
    def _preparar_preguntas(self, seed, n):
        rng = random.Random(seed)
        ids = self.banco.todas_ids()
        rng.shuffle(ids)
        self.preguntas_duelo = ids[:n]

    # ==================== PANTALLA DE JUEGO ====================
    def _pantalla_juego(self):
        self._limpiar()
        self.pregunta_idx = 0
        self.marcador = {"yo": 0, "otro": 0}

        # Cabecera
        cab = QHBoxLayout()
        self.lbl_estado_turno = QLabel("Preparados...")
        self.lbl_estado_turno.setObjectName("titulo")
        cab.addWidget(self.lbl_estado_turno)
        cab.addStretch()
        self.lbl_progreso = QLabel(f"1/{len(self.preguntas_duelo)}")
        self.lbl_progreso.setObjectName("hud")
        cab.addWidget(self.lbl_progreso)
        self.pila.addLayout(cab)

        # Marcador
        marcador_row = QHBoxLayout()
        self.card_yo = self._marcador_card("TÚ", self.mi_nombre, "#22D3EE")
        self.card_otro = self._marcador_card("RIVAL", self.jugador_remoto["nombre"] if self.jugador_remoto else "?", "#F472B6")
        marcador_row.addWidget(self.card_yo["card"])
        marcador_row.addWidget(self.card_otro["card"])
        self.pila.addLayout(marcador_row)

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
            b.clicked.connect(lambda _=False, idx=i: self._yo_responder(idx))
            cp.addWidget(b)
            self.botones_opciones.append(b)

        self.lbl_feedback = QLabel()
        self.lbl_feedback.setObjectName("feedback")
        self.lbl_feedback.setWordWrap(True)
        self.lbl_feedback.hide()
        cp.addWidget(self.lbl_feedback)

        aplicar_sombra(self.card_pregunta, blur=24, offset_y=6, alpha=140)
        self.pila.addWidget(self.card_pregunta, 1)

        btn_volver = QPushButton("← Abandonar")
        btn_volver.setObjectName("botonSecundario")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.clicked.connect(self._abandonar)
        self.pila.addWidget(btn_volver, alignment=Qt.AlignLeft)

        # Cargar la primera pregunta (pero deshabilitar botones hasta que sea mi turno)
        self._cargar_pregunta_actual()
        self._bloquear_botones()

    def _marcador_card(self, etiqueta, nombre, color):
        card = QFrame()
        card.setObjectName("filaRanking")
        cv = QVBoxLayout(card)
        cv.setContentsMargins(12, 8, 12, 8)
        cv.setSpacing(0)
        e = QLabel(etiqueta)
        e.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 900; letter-spacing: 2px; background: transparent;")
        cv.addWidget(e)
        n = QLabel(nombre)
        n.setStyleSheet("font-size: 14px; font-weight: 800; background: transparent;")
        cv.addWidget(n)
        a = QLabel("0 aciertos")
        a.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 700; background: transparent;")
        cv.addWidget(a)
        aplicar_sombra(card, blur=14, offset_y=3, alpha=110)
        return {"card": card, "aciertos": a}

    def _cargar_pregunta_actual(self):
        if self.pregunta_idx >= len(self.preguntas_duelo):
            self._fin_partida()
            return
        pid = self.preguntas_duelo[self.pregunta_idx]
        p = self.banco.obtener(pid)
        self.pregunta_actual = p
        self.lbl_pregunta.setText(p["p"])
        self.lbl_progreso.setText(f"{self.pregunta_idx+1}/{len(self.preguntas_duelo)}")
        for i, b in enumerate(self.botones_opciones):
            b.setText(f"  {chr(65+i)}.   {p['o'][i]}")
            b.setProperty("estado", "")
            b.style().unpolish(b)
            b.style().polish(b)
        self.lbl_feedback.hide()

    def _activar_turno(self):
        self.mi_turno = True
        self.respuesta_pendiente = True
        self.lbl_estado_turno.setText("👉 ¡TU TURNO! Responde la pregunta")
        self.lbl_estado_turno.setStyleSheet("color: #22D3EE; font-size: 18px; font-weight: 900; background: transparent;")
        for b in self.botones_opciones:
            b.setEnabled(True)
        self.lbl_feedback.hide()

    def _bloquear_botones(self):
        for b in self.botones_opciones:
            b.setEnabled(False)

    def _yo_responder(self, idx):
        if not self.mi_turno or not self.respuesta_pendiente:
            return
        self.mi_turno = False
        self.respuesta_pendiente = False
        self._bloquear_botones()

        p = self.pregunta_actual
        acierto = (idx == p["c"])

        # Marcar visualmente
        for i, b in enumerate(self.botones_opciones):
            b.setProperty("estado", "correcto" if i == p["c"] else "incorrecto")
            b.style().unpolish(b)
            b.style().polish(b)

        if acierto:
            self.marcador["yo"] += 1
            self.lbl_feedback.setText(f"<b style='color:#22C55E;'>✅ ¡Correcto!</b>")
        else:
            self.lbl_feedback.setText(f"<b style='color:#EF4444;'>❌ Fallo</b> · Respuesta: <b>{chr(65+p['c'])}. {p['o'][p['c']]}</b>")
        self.lbl_feedback.show()
        self._actualizar_marcador()

        # Enviar respuesta al rival
        if self.es_host:
            self.servidor.enviar({"tipo": "respuesta_host", "idx": idx, "acierto": acierto})
        else:
            self.cliente.enviar({"tipo": "respuesta", "idx": idx, "acierto": acierto})

        # Cuando ambos han respondido, avanzar
        QTimer.singleShot(2400, self._avanzar_si_ambos_listos)

    def _procesar_respuesta_remota(self, idx, acierto):
        """Se llama cuando llega la respuesta del rival."""
        if acierto:
            self.marcador["otro"] += 1
        self._actualizar_marcador()
        # Si ambos respondieron, avanzar
        QTimer.singleShot(1800, self._avanzar_si_ambos_listos)

    def _actualizar_marcador(self):
        self.card_yo["aciertos"].setText(f"{self.marcador['yo']} aciertos")
        self.card_otro["aciertos"].setText(f"{self.marcador['otro']} aciertos")

    def _avanzar_si_ambos_listos(self):
        """Pasa al siguiente turno/pregunta."""
        if not self.respuesta_pendiente and not self.mi_turno:
            # Ambos han respondido
            if self.es_host:
                # El host decide avanzar
                self.pregunta_idx += 1
                self.servidor.enviar({"tipo": "turno_siguiente", "pregunta_idx": self.pregunta_idx})
                self._siguiente_pregunta_host()
            else:
                # El cliente espera la señal del host
                pass

    def _siguiente_pregunta_host(self):
        if self.pregunta_idx >= len(self.preguntas_duelo):
            self._terminar_host()
            return
        self._cargar_pregunta_actual()
        self.mi_turno = True
        QTimer.singleShot(300, self._activar_turno)

    def _avanzar_turno_forzado(self, idx):
        """El cliente recibe la señal de avanzar."""
        self.pregunta_idx = idx
        if self.pregunta_idx >= len(self.preguntas_duelo):
            return
        self._cargar_pregunta_actual()
        QTimer.singleShot(400, self._activar_turno)

    def _terminar_host(self):
        marcador = {"yo": self.marcador["yo"], "otro": self.marcador["otro"]}
        self.servidor.enviar({"tipo": "fin_partida", "marcador": marcador})
        self._mostrar_resultado_final(marcador)

    def _fin_partida(self):
        self._terminar_host()

    # ==================== RESULTADO ====================
    def _mostrar_resultado_final(self, marcador):
        self._limpiar()

        tit = QLabel("🏁  Fin del duelo online")
        tit.setObjectName("titulo")
        tit.setAlignment(Qt.AlignCenter)
        self.pila.addWidget(tit)

        yo = marcador.get("yo", self.marcador["yo"])
        otro = marcador.get("otro", self.marcador["otro"])

        if yo > otro:
            texto, color = "¡VICTORIA!", "#22C55E"
        elif otro > yo:
            texto, color = "DERROTA", "#EF4444"
        else:
            texto, color = "EMPATE", "#FACC15"

        lbl = QLabel(f"<b style='font-size:34px; color:{color};'>{texto}</b>")
        lbl.setAlignment(Qt.AlignCenter)
        self.pila.addWidget(lbl)

        tabla = QLabel(
            f"<div style='font-size:20px; text-align:center;'>"
            f"<b>{self.mi_nombre}:</b> {yo} aciertos<br>"
            f"<b>{self.jugador_remoto['nombre']}:</b> {otro} aciertos"
            f"</div>"
        )
        tabla.setObjectName("tarjeta")
        tabla.setAlignment(Qt.AlignCenter)
        self.pila.addWidget(tabla)

        # Registrar en ranking
        try:
            self.db.agregar_ranking_para(self.jugador_local["id"], yo)
        except Exception:
            pass

        self.pila.addStretch()

        b1 = QPushButton("🔄  Volver a jugar")
        b1.setObjectName("botonPrimario")
        b1.setMinimumHeight(46)
        b1.setCursor(Qt.PointingHandCursor)
        b1.clicked.connect(self._pantalla_inicio)
        self.pila.addWidget(b1)

        b2 = QPushButton("← Volver al inicio")
        b2.setObjectName("botonSecundario")
        b2.setCursor(Qt.PointingHandCursor)
        b2.clicked.connect(lambda: self.ventana._ir_a(0))
        self.pila.addWidget(b2)

    # ==================== UTIL ====================
    def _mostrar_desconexion(self):
        mostrar_toast(self, "⚠️  El rival se ha desconectado", "aviso", 3000)
        QTimer.singleShot(1500, self._pantalla_inicio)

    def _abandonar(self):
        r = QMessageBox.question(self, "Abandonar", "¿Seguro que quieres abandonar?")
        if r == QMessageBox.Yes:
            self._cerrar_conexiones()
            self.ventana._ir_a(0)

    def _cerrar_conexiones(self):
        try:
            if self.servidor:
                self.servidor.cerrar()
                self.servidor = None
            if self.cliente:
                self.cliente.cerrar()
                self.cliente = None
        except Exception:
            pass
