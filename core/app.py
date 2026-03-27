import uvicorn
from network.http_server import app
from printing.job_worker import start_workers
from security.cert_manager import generate_cert
from core.async_loop import loop, init_async_loop
from core.renderer_instance import renderer
import os
import asyncio


class POSPrintServer:

    def __init__(self, config):

        self.config = config

    def start(self):

        init_async_loop()

        future = asyncio.run_coroutine_threadsafe(renderer.start(), loop)
        future.result()

        start_workers()
        
        
        server = self.config.get_server()

        https = server["https"]

        if https:

            if not os.path.exists("certs/cert.pem"):
                generate_cert(server["host"])

            config = uvicorn.Config(
                "network.http_server:app",
                host=server["host"],
                port=server["http_port"],
                ssl_certfile="certs/cert.pem",
                ssl_keyfile="certs/key.pem"
            )
            server = uvicorn.Server(config)
            server.run()
            # uvicorn.run(
            #     "network.http_server:app",
            #     host=server["host"],
            #     port=server["http_port"],
            #     ssl_certfile="certs/cert.pem",
            #     ssl_keyfile="certs/key.pem"
            # )

        else:
            config = uvicorn.Config(
                "network.http_server:app",
                host=server["host"],
                port=server["http_port"]
            )
            server = uvicorn.Server(config)
            server.run()

            # uvicorn.run(
            #     "network.http_server:app",
            #     host=server["host"],
            #     port=server["http_port"]
            # )