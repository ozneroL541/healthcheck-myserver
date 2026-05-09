#!/bin/python3

import logging
import requests

logging.basicConfig(level=logging.INFO)

try:
    requests.get("https://hc-ping.com/your-uuid-here", timeout=10)
except requests.RequestException as e:
    logging.error("Ping failed: %s" % e)
