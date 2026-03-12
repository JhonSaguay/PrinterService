from PySide6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QLabel,
    QLineEdit, QListWidget, QHBoxLayout,
    QCheckBox, QComboBox, QSpinBox, QMessageBox
)

from printing.printer_manager import list_printers
import threading


class MainWindow(QWidget):

    def __init__(self, server, config):

        super().__init__()

        self.server = server
        self.config = config

        self.setWindowTitle("POS Print Server")

        layout = QVBoxLayout()

        # IP

        layout.addWidget(QLabel("IP servidor"))

        self.txt_ip = QLineEdit()
        self.txt_ip.setText(config.get_server()["host"])

        layout.addWidget(self.txt_ip)

        # Server Port

        layout.addWidget(QLabel("Port servidor"))
        
        self.txt_server_port = QSpinBox()
        self.txt_server_port.setRange(1, 65535)
        self.txt_server_port.setValue(config.get_server()["http_port"])

        layout.addWidget(self.txt_server_port)

        # HTTPS

        self.chk_https = QCheckBox("Activar HTTPS")
        self.chk_https.setChecked(config.get_server()["https"])

        layout.addWidget(self.chk_https)

        # Lista impresoras

        layout.addWidget(QLabel("Impresoras"))

        self.list_printers = QListWidget()

        layout.addWidget(self.list_printers)

        # Selector impresora

        row = QHBoxLayout()

        self.cmb_printers = QComboBox()

        printers = list_printers()
        self.cmb_printers.addItems(printers)

        row.addWidget(self.cmb_printers)

        # puerto

        self.port_box = QSpinBox()
        self.port_box.setRange(1, 65535)
        self.port_box.setValue(9100)

        row.addWidget(self.port_box)

        # paper size
        self.paper_size = QComboBox()
        self.paper_size.addItem("80 mm", 80)
        self.paper_size.addItem("58 mm", 58)

        row.addWidget(self.paper_size)

        # boton agregar

        btn_add = QPushButton("Agregar")

        btn_add.clicked.connect(self.add_printer)

        row.addWidget(btn_add)

        layout.addLayout(row)

        # boton eliminar

        btn_remove = QPushButton("Eliminar impresora")
        btn_remove.clicked.connect(self.remove_printer)

        layout.addWidget(btn_remove)

        # botones

        btn_save = QPushButton("Guardar Configuración")
        btn_save.clicked.connect(self.save_config)

        layout.addWidget(btn_save)

        btn_start = QPushButton("Iniciar Servidor")
        btn_start.clicked.connect(self.start_server)

        layout.addWidget(btn_start)

        self.status = QLabel("Servidor detenido")

        layout.addWidget(self.status)

        self.setLayout(layout)

        self.load_printers()

    def load_printers(self):

        self.list_printers.clear()

        for p in self.config.get_tcp_ports():

            text = f"{p['printer']}  ->  {p['port']} ->  {p['paper']}mm"
            self.list_printers.addItem(text)

    def add_printer(self):

        printer = self.cmb_printers.currentText()
        port = self.port_box.value()
        paper_size = self.paper_size.currentData()

        self.config.add_printer(printer, port, paper_size)

        self.load_printers()
    
    def remove_printer(self):

        item = self.list_printers.currentItem()

        if not item:
            return

        text = item.text()

        port = int(text.split("->")[1].strip())

        self.config.remove_printer(port)

        self.load_printers()

    def save_config(self):

        host = self.txt_ip.text()
        https = self.chk_https.isChecked()
        server_port = self.txt_server_port.value()

        self.config.set_host(host)
        self.config.set_https(https)
        self.config.set_server_port(server_port)

        self.config.save()

        self.status.setText("Configuración guardada")

    def start_server(self):

        self.status.setText("Servidor activo")

        t = threading.Thread(target=self.server.start, daemon=True)
        t.start()