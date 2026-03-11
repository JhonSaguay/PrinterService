import sys
from PySide6.QtWidgets import QApplication

from core.config_manager import ConfigManager
from core.app import POSPrintServer
from ui.main_window import MainWindow


config = ConfigManager()

server = POSPrintServer(config)

app = QApplication(sys.argv)

window = MainWindow(server, config)
window.show()

sys.exit(app.exec())