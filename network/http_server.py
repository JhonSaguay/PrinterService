from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from printing.print_queue import print_queue
from printing.printer_manager import get_printer_by_port
import base64

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # o ["http://localhost:8069"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            receipt_data = data.get('receipt',False)
            if not receipt_data:
                print("No data received")
                result = False
            else:
                print(f"Printing to port {port}")
                print_data = base64.b64decode(receipt_data.get('data',''))

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

        print("Printer action error:", e)

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