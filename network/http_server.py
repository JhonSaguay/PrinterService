from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from printing.print_queue import print_queue
from printing.printer_manager import get_printer_by_port, get_all_printers
from bs4 import BeautifulSoup
from PIL import Image
import io
import math
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

def get_max_width(paper):
    return 576 if paper == 80 else 384

def convert_image_to_escpos(image_bytes, printer):
    MAX_WIDTH = get_max_width(printer["paper"])
    img = Image.open(io.BytesIO(image_bytes))

    # if img.width > MAX_WIDTH:

    ratio = MAX_WIDTH / img.width

    img = img.resize(
        (MAX_WIDTH, int(img.height * ratio)),
        Image.LANCZOS
    )
    
    img = img.convert("1", dither=Image.FLOYDSTEINBERG)
    
    width, height = img.size

    width_bytes = math.ceil(width / 8)

    block_height = 256

    raster = bytearray()
    pixels = img.load()
    for y_start in range(0, height, block_height):

        h = min(block_height, height - y_start)

        # cabecera ESC/POS
        raster.extend(b'\x1d\x76\x30\x00')
        raster.extend(width_bytes.to_bytes(2, 'little'))
        raster.extend(h.to_bytes(2, 'little'))

        for y in range(y_start, y_start + h):

            for x in range(width_bytes):

                byte = 0

                for bit in range(8):

                    px = x * 8 + bit

                    if px < width and pixels[px, y] == 0:
                        byte |= 1 << (7 - bit)

                raster.append(byte)
    return bytes(raster)

# obtener data html

def html_to_escpos(html):

    soup = BeautifulSoup(html, "html.parser")

    root = soup.select_one(".pos-receipt")

    lines = []

    for div in root.find_all("div", recursive=False):

        text = div.get_text(" ", strip=True)

        if text:
            lines.append(text)

    receipt = "\n".join(lines) + "\n\n"

    return receipt.encode("cp437", errors="replace")


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
                receipt_data = html_to_escpos(receipt_data)
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

            # receipt_data = data.get('receipt',False)
            print_data = process_print_data(data, printer)
            if not print_data:
                print("No data received")
                result = False
            else:
                print(f"Printing to port {port}")
                # print_data = base64.b64decode(receipt_data.get('data',''))

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