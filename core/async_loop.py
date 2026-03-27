import asyncio
import threading

loop = asyncio.new_event_loop()

def start_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()

def init_async_loop():
    t = threading.Thread(target=start_loop, daemon=True)
    t.start()