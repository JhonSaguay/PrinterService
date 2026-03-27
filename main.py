import sys
import subprocess
from PySide6.QtWidgets import QApplication

from core.config_manager import ConfigManager
from core.app import POSPrintServer
from ui.main_window import MainWindow


config = ConfigManager()

server = POSPrintServer(config)

def run_ui():

    app = QApplication(sys.argv)

    window = MainWindow(server, config)
    window.show()

    sys.exit(app.exec())


def run_service():

    # corre el servidor sin interfaz
    server.start()

if __name__ == "__main__":

    if "--service" in sys.argv:
        run_service()
    else:
        run_ui()