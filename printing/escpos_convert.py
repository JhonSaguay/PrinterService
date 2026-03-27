from bs4 import BeautifulSoup
from PIL import Image
from playwright.async_api import async_playwright
import io
import math

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


async def html_to_image(html, width=576):

    async with async_playwright() as p:
        browser = await p.chromium.launch()

        page = await browser.new_page(viewport={
            "width": width,
            "height": 400
        }, device_scale_factor=2)

        await page.set_content(html)
        await page.wait_for_timeout(50)
        await page.add_style_tag(content="""
            body {
                zoom:3;
            }
        """)

        image_bytes = await page.screenshot(full_page=True)
        await browser.close()

        return image_bytes