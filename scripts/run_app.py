"""Локальний запуск API та вебінтерфейсу FactCheck."""

from __future__ import annotations

import argparse
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_DIRECTORY = PROJECT_ROOT / "apps" / "api"


def _wait_and_open(url: str, timeout_seconds: float = 30.0) -> None:
    """Відкрити інтерфейс, щойно локальний сервер почне відповідати."""
    deadline = time.monotonic() + timeout_seconds
    health_url = f"{url}/api/health"

    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=1.0) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.25)

    print("Не вдалося автоматично відкрити сторінку. Відкрийте її у браузері:")
    print(url)


def _parse_arguments() -> argparse.Namespace:
    """Отримати параметри локального запуску."""
    parser = argparse.ArgumentParser(
        description="Запуск україномовного інтерфейсу FactCheck.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Не відкривати браузер автоматично.",
    )
    return parser.parse_args()


def main() -> None:
    """Запустити сервер і, за потреби, відкрити вебінтерфейс."""
    arguments = _parse_arguments()
    page_host = "127.0.0.1" if arguments.host == "0.0.0.0" else arguments.host
    page_url = f"http://{page_host}:{arguments.port}"

    if not arguments.no_browser:
        opener = threading.Thread(
            target=_wait_and_open,
            args=(page_url,),
            daemon=True,
        )
        opener.start()

    print(f"FactCheck запускається: {page_url}")
    print("Щоб зупинити застосунок, натисніть Ctrl+C.")
    uvicorn.run(
        "app.main:app",
        app_dir=str(API_DIRECTORY),
        host=arguments.host,
        port=arguments.port,
    )


if __name__ == "__main__":
    main()
