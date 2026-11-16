"""Налаштування імпортів для тестів API."""

import sys
from pathlib import Path

API_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIRECTORY))
