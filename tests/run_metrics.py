"""Free-tier friendly RAG vs full-schema benchmark for the deployed API."""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
ALLOWED_TABLES = {"customers", "products", "orders", "order_items"}


