import uvicorn
from network.tcp_server import start_tcp_server
from network.http_server import app
from printing.job_worker import start_workers
from security.cert_manager import generate_cert
import os


class POSPrintServer:

    def __init__(self, config):

        self.config = config

    def start(self):
        start_workers()

        for p in self.config.get_tcp_ports():
            start_tcp_server(p["port"], p["printer"])

        server = self.config.get_server()

        https = server["https"]

        if https:

            if not os.path.exists("certs/cert.pem"):
                generate_cert()

            uvicorn.run(
                "network.http_server:app",
                host=server["host"],
                port=server["http_port"],
                ssl_certfile="certs/cert.pem",
                ssl_keyfile="certs/key.pem"
            )

        else:

            uvicorn.run(
                "network.http_server:app",
                host=server["host"],
                port=server["http_port"]
            )