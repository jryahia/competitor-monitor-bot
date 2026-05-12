"""
summarizer.py — Italian-language LLM summary via OpenAI GPT-4o-mini.

Falls back to a template-based summary if the API call fails.
"""

import logging
from typing import Optional

from openai import OpenAI, OpenAIError

from comparator import Change

logger = logging.getLogger(__name__)

_EMOJI_MAP = {
    "price_drop": "📉",
    "price_increase": "📈",
    "stockout": "🚫",
    "restock": "✅",
    "new_product": "🆕",
    "new_arrival_flag": "🆕",
    "discount_added": "🔥",
    "discount_removed": "💥",
}

_SEVERITY_EMOJI = {
    "high": "❗",
    "medium": "⚠️",
    "low": "ℹ️",
}

_SYSTEM_PROMPT = """Sei un analista di e-commerce esperto che monitora i concorrenti per conto di un'azienda italiana.
Il tuo compito è generare un report quotidiano conciso e professionale sui cambiamenti rilevati nei negozi dei concorrenti.

Regole:
- Scrivi SEMPRE in italiano
- Usa emoji pertinenti per ogni tipo di cambiamento (📉 calo prezzo, 📈 aumento prezzo, 🚫 esaurito, ✅ di nuovo disponibile, 🆕 nuovo prodotto, 🔥 sconto aggiunto, 💥 sconto rimosso)
- Sii diretto e informativo, senza fronzoli
- Evidenzia i cambiamenti più critici (alta severità) per primi
- Concludi con una breve analisi strategica di 1-2 frasi
- Massimo 550 token di output"""


def _build_changes_text(changes: list[Change]) -> str:
    """Format changes into a structured text for the LLM prompt."""
    lines = []
    for c in changes:
        emoji = _EMOJI_MAP.get(c.change_type, "🔄")
        sev = _SEVERITY_EMOJI.get(c.severity, "")
        line = f"{emoji}{sev} [{c.change_type.upper()}] {c.description} (URL: {c.url})"
        if c.old_value and c.new_value:
            line += f" | Prima: {c.old_value} → Ora: {c.new_value}"
        lines.append(line)
    return "\n".join(lines)


def _fallback_summary(changes: list[Change], date_str: str) -> str:
    """Template-based Italian summary used when the OpenAI API is unavailable."""
    high = [c for c in changes if c.severity == "high"]
    medium = [c for c in changes if c.severity == "medium"]
    low = [c for c in changes if c.severity == "low"]

    lines = [
        f"📊 *Report Concorrenti — {date_str}*",
        "",
        f"Rilevati {len(changes)} cambiamenti totali:",
        f"  ❗ Alta priorità: {len(high)}",
        f"  ⚠️ Media priorità: {len(medium)}",
        f"  ℹ️ Bassa priorità: {len(low)}",
        "",
        "*Dettagli:*",
    ]

    for c in sorted(changes, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x.severity]):
        emoji = _EMOJI_MAP.get(c.change_type, "🔄")
        lines.append(f"{emoji} {c.description}")

    lines.append("")
    lines.append("_(Riepilogo generato automaticamente — servizio AI temporaneamente non disponibile)_")
    return "\n".join(lines)


def generate_summary(
    changes: list[Change],
    api_key: str,
    date_str: str,
) -> str:
    """
    Generate an Italian summary of competitor changes.

    Uses GPT-4o-mini if the API is reachable; falls back to a template otherwise.

    Args:
        changes: List of Change objects from comparator.
        api_key: OpenAI API key.
        date_str: Human-readable date string for the report header.

    Returns:
        Formatted Italian summary string ready for Telegram delivery.
    """
    if not changes:
        return (
            f"📊 *Report Concorrenti — {date_str}*\n\n"
            "✅ Nessun cambiamento rilevato oggi nei negozi monitorati."
        )

    changes_text = _build_changes_text(changes)

    try:
        client = OpenAI(api_key=api_key)
        user_message = (
            f"Data del report: {date_str}\n\n"
            f"Cambiamenti rilevati:\n{changes_text}\n\n"
            "Genera il report quotidiano in italiano con emoji."
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=600,
        )

        summary = response.choices[0].message.content or ""
        logger.info("LLM summary generated (%d chars).", len(summary))
        # Prepend header so the message always starts with the date
        header = f"📊 *Report Concorrenti — {date_str}*\n\n"
        return header + summary

    except OpenAIError as exc:
        logger.warning("OpenAI API failed (%s); using fallback summary.", exc)
        return _fallback_summary(changes, date_str)
    except Exception as exc:
        logger.error("Unexpected error in summarizer: %s", exc)
        return _fallback_summary(changes, date_str)
