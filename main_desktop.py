#!/usr/bin/env python3
"""Competitor Monitor Bot — Desktop App Entry Point
Avvia l'interfaccia grafica desktop (Flet) per il monitoraggio competitor.
"""

import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def main():
    # Check for .env
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        logger.info("⚠️  File .env non trovato!")
        logger.info("   Copia .env.example in .env e configura le tue credenziali:")
        logger.info(f"   cp {os.path.join(os.path.dirname(__file__), '.env.example')} {env_path}")
        sys.exit(1)

    # Install playwright if needed
    try:
        import playwright
    except ImportError:
        logger.info("📦  Installazione Playwright...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

    # Launch Flet desktop app
    logger.info("🚀  Avvio Competitor Monitor Bot Desktop...")
    from ui.app import main as app_main
    import flet as ft
    ft.app(target=app_main)


if __name__ == "__main__":
    main()
