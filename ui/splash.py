"""Splash screen animado con logo girando y barra de carga."""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QProgressBar, QApplication
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QPainter, QLinearGradient, QColor, QBrush, QPen


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SplashScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(520, 340)

        # Centrar
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2,
                  (screen.height() - self.height()) // 2)

        v = QVBoxLayout(self)
        v.setContentsMargins(40, 40, 40, 40)

        # Logo (emoji grande)
        self.lbl_logo = QLabel("⚙️")
        self.lbl_logo.setAlignment(Qt.AlignCenter)
        f = QFont("Noto Color Emoji", 72)
        self.lbl_logo.setFont(f)
        self.lbl_logo.setStyleSheet("background: transparent; color: white;")
        v.addWidget(self.lbl_logo)

        # Título
        self.lbl_titulo = QLabel("MECANIA 4ESO")
        self.lbl_titulo.setAlignment(Qt.AlignCenter)
        self.lbl_titulo.setStyleSheet("""
            color: #22D3EE;
            font-size: 42px;
            font-weight: 900;
            letter-spacing: 4px;
            background: transparent;
        """)
        v.addWidget(self.lbl_titulo)

        self.lbl_sub = QLabel("Máquinas y Mecanismos")
        self.lbl_sub.setAlignment(Qt.AlignCenter)
        self.lbl_sub.setStyleSheet("""
            color: #94A3B8; font-size: 15px; letter-spacing: 2px;
            background: transparent;
        """)
        v.addWidget(self.lbl_sub)

        v.addStretch()

        # Barra
        self.barra = QProgressBar()
        self.barra.setRange(0, 100)
        self.barra.setValue(0)
        self.barra.setTextVisible(False)
        self.barra.setFixedHeight(8)
        self.barra.setStyleSheet("""
            QProgressBar {
                background-color: rgba(30, 41, 59, 0.6);
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #22D3EE, stop:0.5 #A78BFA, stop:1 #F472B6);
                border-radius: 4px;
            }
        """)
        v.addWidget(self.barra)

        # Animación del logo (rotación continua)
        self.angulo = 0
        self.timer_rot = QTimer(self)
        self.timer_rot.timeout.connect(self._rotar)
        self.timer_rot.start(60)

        # Barra de progreso animada
        self.timer_prog = QTimer(self)
        self.timer_prog.timeout.connect(self._avanzar)
        self.timer_prog.start(50)
        self.progreso = 0

    def _rotar(self):
        self.angulo = (self.angulo + 15) % 360
        self.lbl_logo.setStyleSheet(f"background: transparent; color: white;")

    def _avanzar(self):
        if self.progreso < 95:
            self.progreso += 3
            self.barra.setValue(self.progreso)

    def terminar(self):
        self.progreso = 100
        self.barra.setValue(100)
        self.timer_rot.stop()
        self.timer_prog.stop()
        QTimer.singleShot(280, self.close)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, QColor("#0B1220"))
        grad.setColorAt(0.5, QColor("#111C33"))
        grad.setColorAt(1, QColor("#0B1220"))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor("#22D3EE"), 2))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 24, 24)
