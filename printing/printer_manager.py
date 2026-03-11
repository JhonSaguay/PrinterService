import win32print
import json

with open("config.json") as f:
    config = json.load(f)

printers_list = {p["port"]: p for p in config["tcp_ports"]}

def list_printers():

    printers = win32print.EnumPrinters(2)
    return [p[2] for p in printers]

def get_printer_by_port(port):
    return printers_list.get(port)


def send_to_printer(printer, data):
    print(printer)
    print(type(data))
    printer_handle = win32print.OpenPrinter(printer)

    try:

        job = win32print.StartDocPrinter(
            printer_handle, 1, ("POS Job", None, "RAW")
        )

        win32print.StartPagePrinter(printer_handle)

        init = b'\x1b@'
        print(data[:20])
        win32print.WritePrinter(printer_handle, data)

        win32print.EndPagePrinter(printer_handle)
        win32print.EndDocPrinter(printer_handle)

    finally:

        win32print.ClosePrinter(printer_handle)