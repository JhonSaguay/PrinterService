import socket
import threading
from printing.print_queue import print_queue
from core.logger import log


def start_tcp_server(port, printer):

    def run():

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("0.0.0.0", port))
        server.listen()

        log(f"TCP server {port} -> {printer}")

        while True:

            conn, addr = server.accept()
            data = conn.recv(4096)

            if data:

                print_queue.put({
                    "printer": printer,
                    "data": data
                })

                log(f"TCP print from {addr}")

            conn.close()

    threading.Thread(target=run, daemon=True).start()