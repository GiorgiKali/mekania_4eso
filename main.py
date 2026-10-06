"""MECANIA 4ESO — Punto de entrada con login."""
import sys, os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QFontDatabase
from PySide6.QtCore import Qt, QTimer


def ruta_recurso(rel):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel)


from database.db_manager import Database
from logic.leitner import Leitner
from logic.gamificacion import Gamificacion
from ui.ventana_principal import VentanaPrincipal
from ui.splash import SplashScreen
from ui.pantalla_login import PantallaLogin


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName("Mecania 4ESO")

    carpeta = ruta_recurso("assets/fonts")
    if os.path.isdir(carpeta):
        for f in os.listdir(carpeta):
            if f.lower().endswith((".ttf", ".otf")):
                QFontDatabase.addApplicationFont(os.path.join(carpeta, f))

    icono = ruta_recurso("assets/icons/app.svg")
    if os.path.exists(icono):
        app.setWindowIcon(QIcon(icono))

    # Splash
    pantalla = app.primaryScreen().availableGeometry()
    es_pequena = pantalla.width() < 1200 or pantalla.height() < 700
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    db = Database()

    # Cerrar splash y mostrar login o ventana principal
    def continuar():
        splash.terminar()
        # Si hay sesión guardada y el usuario quiere, autologuear
        if db.retomar_sesion():
            abrir_ventana()
        else:
            abrir_login()

    def abrir_login():
        login = PantallaLogin(db)
        resultado = login.exec()
        if resultado == PantallaLogin.Accepted and db.usuario_id:
            abrir_ventana()
        else:
            app.quit()

    def abrir_ventana():
        leitner = Leitner(db)
        gam = Gamificacion(db)
        ventana = VentanaPrincipal(db, leitner, gam)
        ventana.ajustar_a_pantalla(pantalla)
        ventana.show()
        app._ventana = ventana  # mantener referencia

    QTimer.singleShot(1200 if es_pequena else 2000, continuar)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
