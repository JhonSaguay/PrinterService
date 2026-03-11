import logging
import os

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/server.log",
    level=logging.INFO,
    format="%(asctime)s %(message)s"
)

def log(msg):
    logging.info(msg)