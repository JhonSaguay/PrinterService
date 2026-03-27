import asyncio
from core.async_loop import loop
from core.renderer_instance import renderer

def render_html_sync(html):

    future = asyncio.run_coroutine_threadsafe(
        renderer.render(html),
        loop
    )

    return future.result()