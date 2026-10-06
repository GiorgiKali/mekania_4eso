"""Diálogo para importar imagen como avatar personalizado."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor

from logic.avatares_custom import importar_avatar, FORMATOS_PERMITIDOS


class DialogoAvatarCustom(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.ruta_seleccionada = None
        self.ruta_importada = None

        self.setWindowTitle("Avatar personalizado")
        self.setMinimumSize(420, 440)
        self.setModal(True)

        v = QVBoxLayout(self)
        v.setContentsMargins(30, 25, 30, 25)
        v.setSpacing(14)

        tit = QLabel("🖼️  Sube tu propia imagen")
        tit.setObjectName("titulo")
        tit.setAlignment(Qt.AlignCenter)
        v.addWidget(tit)

        sub = QLabel("Formatos permitidos: PNG, JPG, WEBP, GIF, BMP")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #94A3B8; font-size: 12px;")
        v.addWidget(sub)

        # Vista previa
        self.vista = QLabel()
        self.vista.setFixedSize(180, 180)
        self.vista.setAlignment(Qt.AlignCenter)
        self.vista.setStyleSheet("""
            QLabel {
                background-color: rgba(15, 24, 42, 200);
                border: 3px dashed #22D3EE;
                border-radius: 90px;
                color: #22D3EE;
                font-size: 14px;
            }
        """)
        self.vista.setText("Sin imagen\nseleccionada")
        v.addWidget(self.vista, alignment=Qt.AlignCenter)

        # Botón seleccionar
        btn_sel = QPushButton("📂  Seleccionar imagen")
        btn_sel.setObjectName("botonPrimario")
        btn_sel.setMinimumHeight(46)
        btn_sel.setCursor(Qt.PointingHandCursor)
        btn_sel.clicked.connect(self._seleccionar)
        v.addWidget(btn_sel)

        v.addStretch()

        # Botones inferiores
        abajo = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("botonSecundario")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)
        abajo.addWidget(btn_cancelar)
        abajo.addStretch()
        self.btn_ok = QPushButton("✅  Usar esta imagen")
        self.btn_ok.setObjectName("botonPrimario")
        self.btn_ok.setCursor(Qt.PointingHandCursor)
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self._aceptar)
        abajo.addWidget(self.btn_ok)
        v.addLayout(abajo)

    def _seleccionar(self):
        filtros = "Imágenes (*" + " *".join(FORMATOS_PERMITIDOS) + ")"
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Elige una imagen", "",
            filtros,
            options=QFileDialog.DontUseNativeDialog  # ← fix Linux Mint
        )
        if not ruta:
            return
        self.ruta_seleccionada = ruta
        # Vista previa circular
        pm = QPixmap(ruta)
        if pm.isNull():
            QMessageBox.warning(self, "Error", "No se pudo cargar la imagen.")
            return
        pm = pm.scaled(180, 180, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        resultado = QPixmap(180, 180)
        resultado.fill(Qt.transparent)
        p = QPainter(resultado)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, 180, 180)
        p.setClipPath(path)
        x = (pm.width() - 180) // 2
        y = (pm.height() - 180) // 2
        p.drawPixmap(-x, -y, pm)
        p.end()
        self.vista.setPixmap(resultado)
        self.vista.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: 3px solid #22D3EE;
                border-radius: 90px;
            }
        """)
        self.btn_ok.setEnabled(True)

    def _aceptar(self):
        if not self.ruta_seleccionada:
            return
        try:
            self.ruta_importada = importar_avatar(self.ruta_seleccionada)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo importar:\n{e}")
