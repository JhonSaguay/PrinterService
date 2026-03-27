from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from printing.print_queue import print_queue
from printing.printer_manager import get_printer_by_port, get_all_printers
from printing.escpos_convert import convert_image_to_escpos
from printing.renderer_bridge import render_html_sync
from core.logger import log
import base64

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # o ["http://localhost:8069"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.options("/{full_path:path}")
async def options_handler(request: Request):
    return {}

@app.get("/")
def printers():

    printers = get_all_printers()
    if not printers:
        return {"error": "printer not found"}

    return {
        "jsonrpc": "2.0",
        "result": printers
    }

@app.get("/{port}/hw_proxy/hello", response_class=PlainTextResponse)
def hello(port: int):
    return "ping"

@app.post("/{port}/hw_proxy/handshake")
def handshake(port: int, body: dict = None):

    request_id = None

    if body and "id" in body:
        request_id = body["id"]

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": True
    }

@app.post("/{port}/hw_proxy/status_json")
def status(port: int):

    printer = get_printer_by_port(port)

    if not printer:
        return {"error": "printer not found"}

    return {
        "jsonrpc": "2.0",
        "id": "",
        "result": {
            "printer": {
                "status": "connected",
                "messages": [f"Connected to {printer['printer']}"]
            },
            "scanner": {
                "status": "disconnected",
                "messages": ["Scanner connected"]
            },
            "scale": {
                "status": "disconnected",
                "messages": ["RS-232 device found"]
            }
        }
    }

# Base64
def detect_format(data):

    if data.startswith(b'%PDF'):
        return "pdf"

    if data.startswith(b'\x89PNG'):
        return "png"

    if data.startswith(b'\xff\xd8'):
        return "jpg"

    if data.startswith(b'\x1b'):
        return "escpos"

    return "unknown"


def process_print_data(data, printer):
    action = data.get('action',False)
    receipt = data.get('receipt',False)
    receipt_data = False
    init = b'\x1b@'
    cut =  b'\n\n\n\x1dV\x00'
    FEED = b'\x1b\x64\x05'
    # JPEG header
    if action == 'print_receipt':
        if isinstance(receipt, str):
            receipt_data = base64.b64decode(receipt)
            if receipt_data.startswith(b'\xff\xd8') or receipt_data.startswith(b'\x89PNG'):
                receipt_data = convert_image_to_escpos(receipt_data, printer)
                receipt_data = init + receipt_data + FEED + cut
        else:
            if receipt.get('isBase64', False):
                receipt_data = base64.b64decode(receipt.get('data',''))
                if receipt_data.startswith(b'\xff\xd8') or receipt_data.startswith(b'\x89PNG'):
                    receipt_data = convert_image_to_escpos(receipt_data, printer)
                    receipt_data = init + receipt_data + FEED + cut
            else:
                receipt_data = receipt.get('data','')
                # receipt_data = html_to_escpos(receipt_data)
                # image_bytes = await html_to_image(receipt_data)
                image_bytes = render_html_sync(receipt_data)
                receipt_data = convert_image_to_escpos(image_bytes, printer)
                receipt_data = init + receipt_data + FEED + cut

    elif action == 'cashbox':
        receipt_data = b'\x1b\x70\x00\x19\xfa'
        print('Abrir cajon')
    else:
        print('No validado') 

    # ya es ESC/POS
    return receipt_data



@app.post("/{port}/hw_proxy/default_printer_action")
async def default_printer_action(port: int, payload: dict):

    try:

        request_id = payload.get("id")
        params = payload.get("params", {})
        data = params.get("data")
        printer = get_printer_by_port(port)
        if not data:
            print("No data received")
            result = False
        else:
            # action type
            print_data = process_print_data(data, printer)
            if not print_data:
                print("No data received")
                result = False
            else:
                print(f"Printing to port {port}")
                print_queue.put({
                    "printer": printer['printer'],
                    "data": print_data
                })
                result = True

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    except Exception as e:

        log(f"Printer action error: {e}")

        return {
            "jsonrpc": "2.0",
            "id": None,
            "result": False
        }

@app.post("/{port}/hw_proxy/open_cashbox")
def open_cashbox(port: int):

    printer = get_printer_by_port(port)
    cmd = b'\x1b\x70\x00\x19\xfa'
    print_queue.put({
        "printer": printer,
        "data": cmd
    })

    return {"jsonrpc": "2.0", "result": True, "id": ""}