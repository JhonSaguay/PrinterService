from playwright.async_api import async_playwright
import os
import sys

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.getcwd()

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(
    base_path, "ms-playwright"
)

class Renderer:

    def __init__(self):
        self.browser = None
        self.page = None

    async def start(self):
        self.p = await async_playwright().start()

        self.browser = await self.p.chromium.launch(headless=True)

        self.page = await self.browser.new_page(
            viewport={"width": 576, "height": 400},
            device_scale_factor=2
        )

    async def render(self, html):

        html = f"""
        <html>
        <head>
        <style>
            body {{
                font-family: monospace;
                zoom: 3;
            }}
        </style>
        </head>
        <body>
        {html}
        </body>
        </html>
        """

        await self.page.set_content(html)

        # ⚡ rápido
        await self.page.wait_for_timeout(50)

        return await self.page.screenshot(full_page=True)