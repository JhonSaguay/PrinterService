import threading
from printing.print_queue import print_queue
from printing.printer_manager import send_to_printer
from core.logger import log

def worker():

    while True:
        job = print_queue.get()
        print("JOB RECEIVED:", job["printer"])
        try:
            send_to_printer(job["printer"], job["data"])
            log(f"Printed → {job['printer']}")
        except Exception as e:
            log(f"Error printing {e}")

        print_queue.task_done()


def start_workers(n=2):

    for _ in range(n):
        t = threading.Thread(target=worker, daemon=True)
        t.start()