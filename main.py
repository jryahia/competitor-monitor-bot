"""
main.py — Orchestrator for the competitor monitoring bot.

Usage:
    python main.py --once        # Run a single check and exit
    python main.py --daemon      # Run on a recurring schedule (CHECK_INTERVAL_HOURS)
"""

import argparse
import asyncio
import logging
import signal
import sys
from datetime import datetime

from config import Config
from scraper import scrape_all, ProductSnapshot
from comparator import compare_snapshots
from summarizer import generate_summary
from notifier import send_report
from state_manager import load_state, save_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_shutdown = asyncio.Event()


def _register_signals() -> None:
    """Register SIGINT / SIGTERM handlers for graceful shutdown."""
    loop = asyncio.get_event_loop()

    def _handle(sig_name: str):
        logger.info("Received %s — shutting down gracefully.", sig_name)
        _shutdown.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle, sig.name)


async def run_once(cfg: Config) -> None:
    """Execute a single monitoring cycle: scrape → compare → save → summarise → notify."""
    date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    logger.info("=== Monitoring cycle started — %s ===", date_str)

    # 1. Scrape
    logger.info("Scraping %d URL(s)…", len(cfg.competitor_urls))
    try:
        snapshots: list[ProductSnapshot] = await scrape_all(cfg.competitor_urls)
    except Exception as exc:
        logger.error("Scraping failed entirely: %s", exc)
        return

    # 2. Load previous state and compare
    old_state = load_state(cfg.state_file)
    changes = compare_snapshots(old_state, snapshots, cfg.price_drop_threshold)

    # 3. Persist new state (even if unchanged, to update timestamps)
    new_state = {snap.url: snap.to_dict() for snap in snapshots}
    try:
        save_state(new_state, cfg.state_file)
        logger.info("State saved to %s.", cfg.state_file)
    except OSError as exc:
        logger.error("Could not save state: %s", exc)

    # 4. Generate Italian summary
    summary = generate_summary(changes, cfg.openai_api_key, date_str)

    # 5. Send to Telegram
    ok = await send_report(cfg.telegram_bot_token, cfg.telegram_chat_id, summary)
    if ok:
        logger.info("Report delivered to Telegram.")
    else:
        logger.error("One or more Telegram delivery parts failed.")

    logger.info("=== Monitoring cycle complete ===")


async def run_daemon(cfg: Config) -> None:
    """Run the monitoring cycle on a recurring schedule until shutdown signal."""
    interval_seconds = cfg.check_interval_hours * 3600
    logger.info(
        "Daemon mode — interval: %.1f hours (%.0fs). Press Ctrl+C to stop.",
        cfg.check_interval_hours,
        interval_seconds,
    )

    _register_signals()

    while not _shutdown.is_set():
        await run_once(cfg)

        logger.info("Next check in %.1f hours.", cfg.check_interval_hours)
        try:
            await asyncio.wait_for(_shutdown.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            pass  # Normal — interval elapsed, run again

    logger.info("Daemon stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Competitor Monitor Bot — scrapes e-commerce pages and reports changes via Telegram."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--once",
        action="store_true",
        help="Run a single monitoring cycle and exit.",
    )
    group.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously on the configured schedule.",
    )
    args = parser.parse_args()

    try:
        cfg = Config.from_env()
    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        sys.exit(1)

    if args.once:
        asyncio.run(run_once(cfg))
    else:
        asyncio.run(run_daemon(cfg))


if __name__ == "__main__":
    main()
