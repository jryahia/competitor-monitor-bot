"""
notifier.py — Delivers the report to a private Telegram channel.

Splits messages longer than 4096 characters automatically.
"""

import logging

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

_MAX_MSG_LEN = 4096
_SPLIT_MARKER = "\n\n"


def _split_message(text: str) -> list[str]:
    """
    Split text into chunks ≤ _MAX_MSG_LEN, breaking on double-newlines where possible.
    """
    if len(text) <= _MAX_MSG_LEN:
        return [text]

    chunks: list[str] = []
    while len(text) > _MAX_MSG_LEN:
        split_at = text.rfind(_SPLIT_MARKER, 0, _MAX_MSG_LEN)
        if split_at == -1:
            split_at = text.rfind("\n", 0, _MAX_MSG_LEN)
        if split_at == -1:
            split_at = _MAX_MSG_LEN
        chunks.append(text[:split_at].rstrip())
        text = text[split_at:].lstrip()

    if text:
        chunks.append(text)

    return chunks


async def send_report(bot_token: str, chat_id: str, message: str) -> bool:
    """
    Send message to the Telegram chat, splitting if necessary.

    Args:
        bot_token: Telegram Bot API token.
        chat_id: Target channel or chat ID.
        message: Formatted report text (may include Markdown).

    Returns:
        True if all parts were delivered successfully, False otherwise.
    """
    bot = Bot(token=bot_token)
    parts = _split_message(message)
    success = True

    for i, part in enumerate(parts, start=1):
        label = f"(parte {i}/{len(parts)}) " if len(parts) > 1 else ""
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=f"{label}{part}",
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
            logger.info("Telegram part %d/%d delivered.", i, len(parts))
        except TelegramError as exc:
            logger.error("Telegram delivery failed for part %d: %s", i, exc)
            # Retry without Markdown in case of parse errors
            try:
                plain = part.replace("*", "").replace("_", "").replace("`", "")
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"{label}{plain}",
                    disable_web_page_preview=True,
                )
                logger.info("Telegram part %d/%d delivered (plain fallback).", i, len(parts))
            except TelegramError as exc2:
                logger.error("Plain fallback also failed for part %d: %s", i, exc2)
                success = False

    return success
