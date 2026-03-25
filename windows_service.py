import win32serviceutil
import win32service
import win32event
import servicemanager
import win32timezone

from core.app import POSPrintServer
from core.config_manager import ConfigManager
import threading
import time


class POSPrinterService(win32serviceutil.ServiceFramework):

    _svc_name_ = "POSPrinterService"
    _svc_display_name_ = "POS Printer Server"
    _svc_description_ = "Servicio de impresión POS en segundo plano"

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.server_thread = None
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.running = False
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):

        servicemanager.LogInfoMsg("POS Printer Service started")

        self.ReportServiceStatus(win32service.SERVICE_RUNNING)

        config = ConfigManager()
        server = POSPrintServer(config)

        def run_server():
            try:
                server.start()
            except Exception as e:
                servicemanager.LogErrorMsg(f"Server error: {e}")

        # correr en hilo
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.start()

        # loop del servicio
        while self.running:
            time.sleep(1)


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(POSPrinterService)