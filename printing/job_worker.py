import threading
from printing.print_queue import print_queue
from printing.printer_manager import send_to_printer
from core.logger import log
from PIL import Image, ImageOps
import io
import math
MAX_WIDTH = 576 

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

def convert_image_to_escpos(image_bytes):

    img = Image.open(io.BytesIO(image_bytes))

    # img = img.convert("L")
    # img = img.point(lambda x: 0 if x < 128 else 255, '1')

    if img.width > MAX_WIDTH:

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
    print("finally")
    return bytes(raster)

def process_print_data(data):

    # JPEG header
    if data.startswith(b'\xff\xd8') or data.startswith(b'\x89PNG'):
        return convert_image_to_escpos(data)

    # ya es ESC/POS
    return data

def print_receipt(data):
    im = Image.open(io.BytesIO(data))

    # Convert to greyscale then to black and white
    im = im.convert("L")
    im = ImageOps.invert(im)
    im = im.convert("1")
    # receipt_protocol = 'escpos'
    # print_command = getattr(self, 'format_%s' % receipt_protocol)(im)
    # self.print_raw(print_command)
    return im

def worker():

    while True:
        job = print_queue.get()
        print("JOB RECEIVED:", job["printer"])
        im_data = process_print_data(job["data"])
        try:
            send_to_printer(job["printer"], im_data)
            log(f"Printed → {job['printer']}")
        except Exception as e:
            log(f"Error printing {e}")

        print_queue.task_done()


def start_workers(n=2):

    for _ in range(n):
        t = threading.Thread(target=worker, daemon=True)
        t.start()