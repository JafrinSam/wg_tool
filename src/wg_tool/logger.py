import logging
import os

def setup_logging():
    level = os.getenv("WGTOOL_LOGLEVEL", "INFO").upper()
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
