"""Pantalla de login / registro con inputs blancos y texto negro."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QCheckBox, QStackedWidget, QWidget
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve
from PySide6.QtGui import QFont

from logic.auth import validar_nombre, validar_password, validar_confirmacion
from ui.widgets.fondo_animado import WidgetConFondo
from ui.widgets.animaciones import aplicar_sombra


ESTILO_INPUT = """
QLineEdit {
    background-color: #FFFFFF;
    color: #000000;
    border: 2px solid #334155;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 15px;
    font-weight: 700;
    selection-background-color: #22D3EE;
    selection-color: #000000;
}
QLineEdit:focus {
    border: 2px solid #22D3EE;
    background-color: #F0FDFF;
    color: #000000;
}
"""

ESTILO_ETIQUETA = """
color: #22D3EE;
font-size: 11px;
font-weight: 800;
letter-spacing: 2px;
background: transparent;
padding-left: 2px;
"""


class PantallaLogin(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("MECANIA 4ESO — Acceso")
        self.setMinimumSize(560, 700)
        self.setModal(True)

        # Fondo animado
        self.fondo = WidgetConFondo(self)
        self.fondo.lower()
        self.fondo.setGeometry(0, 0, self.width(), self.height())

        self._construir_ui()
        self._centrar()
        self._pos_original = None

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "fondo"):
            self.fondo.setGeometry(0, 0, self.width(), self.height())

    def _centrar(self):
        from PySide6.QtWidgets import QApplication
        g = QApplication.primaryScreen().availableGeometry()
        w = min(self.width(), g.width() - 40)
        h = min(self.height(), g.height() - 40)
        self.resize(w, h)
        self.move((g.width() - w) // 2, (g.height() - h) // 2)

    def _construir_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(45, 25, 45, 25)
        v.setSpacing(10)

        # Logo
        logo = QLabel("⚙️")
        logo.setFont(QFont("Noto Color Emoji", 44))
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("background: transparent;")
        v.addWidget(logo)

        # Título
        titulo = QLabel("MECANIA 4ESO")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("""
            color: #22D3EE;
            font-size: 30px;
            font-weight: 900;
            letter-spacing: 3px;
            background: transparent;
        """)
        aplicar_sombra(titulo, blur=25, offset_y=3, alpha=150)
        v.addWidget(titulo)

        sub = QLabel("Accede para guardar tu progreso")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #94A3B8; font-size: 13px; background: transparent;")
        v.addWidget(sub)

        v.addSpacing(6)

        # Pestañas
        tabs = QHBoxLayout()
        tabs.setSpacing(6)
        self.btn_tab_login = QPushButton("INICIAR SESIÓN")
        self.btn_tab_reg = QPushButton("CREAR CUENTA")
        for b in (self.btn_tab_login, self.btn_tab_reg):
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(42)
            b.setStyleSheet("""
                QPushButton {
                    background-color: rgba(15, 24, 42, 220);
                    border: 1px solid #1F2E47;
                    border-radius: 10px;
                    color: #7C8CA3;
                    font-weight: 800;
                    font-size: 12px;
                    letter-spacing: 1px;
                    padding: 8px 16px;
                }
                QPushButton:checked {
                    background-color: #22D3EE;
                    color: #0B1220;
                    border: 2px solid #22D3EE;
                }
                QPushButton:hover:!checked {
                    border: 1px solid #22D3EE;
                    color: #22D3EE;
                }
            """)
            tabs.addWidget(b)
        self.btn_tab_login.setChecked(True)
        self.btn_tab_login.clicked.connect(lambda: self._cambiar_tab(0))
        self.btn_tab_reg.clicked.connect(lambda: self._cambiar_tab(1))
        v.addLayout(tabs)

        # Formularios
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        self.stack.addWidget(self._form_login())
        self.stack.addWidget(self._form_registro())
        v.addWidget(self.stack)

        # Recordar
        self.chk_recordar = QCheckBox("Mantener sesión iniciada")
        self.chk_recordar.setChecked(True)
        self.chk_recordar.setStyleSheet("""
            QCheckBox {
                color: #94A3B8;
                font-size: 12px;
                background: transparent;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px; height: 16px; border-radius: 4px;
                border: 2px solid #334155; background-color: #0F182A;
            }
            QCheckBox::indicator:checked {
                background-color: #22D3EE; border-color: #22D3EE;
            }
        """)
        v.addWidget(self.chk_recordar)

        v.addStretch()

        # Estado (errores / éxito)
        self.lbl_estado = QLabel("")
        self.lbl_estado.setAlignment(Qt.AlignCenter)
        self.lbl_estado.setWordWrap(True)
        self.lbl_estado.setMinimumHeight(38)
        self.lbl_estado.setStyleSheet("background: transparent; font-size: 13px;")
        v.addWidget(self.lbl_estado)

        # Salir
        btn_salir = QPushButton("Salir sin cuenta")
        btn_salir.setCursor(Qt.PointingHandCursor)
        btn_salir.setMinimumHeight(36)
        btn_salir.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 41, 59, 220);
                border: 1px solid #334155;
                border-radius: 10px;
                color: #94A3B8;
                font-weight: 700;
                font-size: 12px;
                padding: 8px 14px;
            }
            QPushButton:hover { color: #F1F5F9; border: 1px solid #EF4444; }
        """)
        btn_salir.clicked.connect(self.reject)
        v.addWidget(btn_salir)

    # ---------- Helpers ----------
    def _etiqueta(self, texto):
        l = QLabel(texto)
        l.setStyleSheet(ESTILO_ETIQUETA)
        return l

    def _input(self, placeholder="", es_password=False):
        w = QLineEdit()
        w.setMinimumHeight(46)
        w.setStyleSheet(ESTILO_INPUT)
        w.setPlaceholderText(placeholder)
        if es_password:
            w.setEchoMode(QLineEdit.Password)
        return w

    def _boton_primario(self, texto):
        b = QPushButton(texto)
        b.setMinimumHeight(50)
        b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #22D3EE, stop:1 #A78BFA);
                color: #0B1220;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 900;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #06B6D4, stop:1 #8B5CF6);
            }
            QPushButton:pressed { padding-top: 2px; }
        """)
        aplicar_sombra(b, blur=20, offset_y=4, alpha=140)
        return b

    # ---------- Formularios ----------
    def _form_login(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 10, 0, 10)
        v.setSpacing(6)

        v.addWidget(self._etiqueta("USUARIO"))
        self.input_login_user = self._input("Escribe tu nombre")
        self.input_login_user.returnPressed.connect(self._hacer_login)
        v.addWidget(self.input_login_user)

        v.addSpacing(4)
        v.addWidget(self._etiqueta("CONTRASEÑA"))
        self.input_login_pass = self._input("Escribe tu contraseña", es_password=True)
        self.input_login_pass.returnPressed.connect(self._hacer_login)
        v.addWidget(self.input_login_pass)

        v.addSpacing(8)
        btn = self._boton_primario("🔓   INICIAR SESIÓN")
        btn.clicked.connect(self._hacer_login)
        v.addWidget(btn)
        return w

    def _form_registro(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 10, 0, 10)
        v.setSpacing(6)

        v.addWidget(self._etiqueta("USUARIO  ·  3-20 caracteres"))
        self.input_reg_user = self._input("Elige un nombre")
        v.addWidget(self.input_reg_user)

        v.addSpacing(4)
        v.addWidget(self._etiqueta("CONTRASEÑA  ·  mínimo 4"))
        self.input_reg_pass = self._input("Elige contraseña", es_password=True)
        v.addWidget(self.input_reg_pass)

        v.addSpacing(4)
        v.addWidget(self._etiqueta("CONFIRMAR CONTRASEÑA"))
        self.input_reg_pass2 = self._input("Repite la contraseña", es_password=True)
        self.input_reg_pass2.returnPressed.connect(self._hacer_registro)
        v.addWidget(self.input_reg_pass2)

        v.addSpacing(8)
        btn = self._boton_primario("✨   CREAR CUENTA")
        btn.clicked.connect(self._hacer_registro)
        v.addWidget(btn)
        return w

    # ---------- Lógica ----------
    def _cambiar_tab(self, idx):
        self.btn_tab_login.setChecked(idx == 0)
        self.btn_tab_reg.setChecked(idx == 1)
        self.stack.setCurrentIndex(idx)
        self.lbl_estado.setText("")

    def _mostrar_error(self, texto):
        self.lbl_estado.setText(f"❌   {texto}")
        self.lbl_estado.setStyleSheet(
            "color: #EF4444; font-weight: 800; font-size: 13px; background: transparent;")
        self._shake()

    def _mostrar_exito(self, texto):
        self.lbl_estado.setText(f"✅   {texto}")
        self.lbl_estado.setStyleSheet(
            "color: #22C55E; font-weight: 800; font-size: 13px; background: transparent;")

    def _shake(self):
        if self._pos_original is None:
            self._pos_original = self.pos()
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(320)
        ox, oy = self._pos_original.x(), self._pos_original.y()
        anim.setKeyValueAt(0.0, QPoint(ox, oy))
        anim.setKeyValueAt(0.2, QPoint(ox - 12, oy))
        anim.setKeyValueAt(0.4, QPoint(ox + 12, oy))
        anim.setKeyValueAt(0.6, QPoint(ox - 8, oy))
        anim.setKeyValueAt(0.8, QPoint(ox + 8, oy))
        anim.setKeyValueAt(1.0, QPoint(ox, oy))
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._shake_anim = anim

    def _hacer_login(self):
        nombre = self.input_login_user.text().strip()
        password = self.input_login_pass.text()
        if not nombre:
            self._mostrar_error("Introduce tu usuario.")
            return
        if not password:
            self._mostrar_error("Introduce tu contraseña.")
            return
        ok, msg = self.db.login(nombre, password)
        if ok:
            self._mostrar_exito(msg)
            QTimer.singleShot(600, self.accept)
        else:
            self._mostrar_error(msg)

    def _hacer_registro(self):
        nombre = self.input_reg_user.text().strip()
        p1 = self.input_reg_pass.text()
        p2 = self.input_reg_pass2.text()

        # Validaciones con feedback específico
        ok, msg = validar_nombre(nombre)
        if not ok:
            self._mostrar_error(msg); return
        ok, msg = validar_password(p1)
        if not ok:
            self._mostrar_error(msg); return
        ok, msg = validar_confirmacion(p1, p2)
        if not ok:
            self._mostrar_error(msg); return

        ok, msg = self.db.registrar(nombre, p1)
        if ok:
            self._mostrar_exito(msg)
            QTimer.singleShot(600, self.accept)
        else:
            self._mostrar_error(msg)
    def closeEvent(self, e):
        """Bloquea el cierre sin cuenta salvo que el usuario confirme."""
        from PySide6.QtWidgets import QMessageBox
        r = QMessageBox.question(
            self, "Salir sin cuenta",
            "Sin una cuenta no podrás guardar tu progreso.\n\n¿Seguro que quieres salir?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if r == QMessageBox.Yes:
            e.accept()
        else:
            e.ignore()
