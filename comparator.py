"""
comparator.py — Detects changes between old and new product snapshots.

Change types: price_drop, price_increase, stockout, restock, new_product,
              discount_added, discount_removed, new_arrival_flag.
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Change:
    url: str
    change_type: str          # e.g. "price_drop"
    severity: str             # "high" | "medium" | "low"
    description: str
    old_value: Optional[str]
    new_value: Optional[str]


def _fmt_price(price: Optional[float], currency: Optional[str]) -> str:
    if price is None:
        return "N/A"
    sym = currency or "€"
    return f"{sym}{price:.2f}"


def compare_snapshots(
    old_state: dict,
    new_snapshots: list,
    price_drop_threshold: float = 0.10,
) -> list[Change]:
    """
    Compare each new ProductSnapshot against the previously saved state.

    Args:
        old_state: mapping of url → dict (from state_manager)
        new_snapshots: list of ProductSnapshot objects
        price_drop_threshold: fractional drop that triggers 'high' severity (default 10%)

    Returns:
        List of Change objects describing every detected difference.
    """
    changes: list[Change] = []

    for snap in new_snapshots:
        url = snap.url

        if url not in old_state:
            # Brand-new URL we've never seen before
            changes.append(
                Change(
                    url=url,
                    change_type="new_product",
                    severity="medium",
                    description=f"Nuovo prodotto rilevato: {snap.name or url}",
                    old_value=None,
                    new_value=snap.name,
                )
            )
            continue

        old = old_state[url]

        # ── Price changes ────────────────────────────────────────────────────
        old_price: Optional[float] = old.get("price")
        new_price: Optional[float] = snap.price

        if old_price is not None and new_price is not None and old_price != new_price:
            delta = (new_price - old_price) / old_price
            old_fmt = _fmt_price(old_price, old.get("currency"))
            new_fmt = _fmt_price(new_price, snap.currency)

            if new_price < old_price:
                severity = "high" if abs(delta) >= price_drop_threshold else "medium"
                changes.append(
                    Change(
                        url=url,
                        change_type="price_drop",
                        severity=severity,
                        description=(
                            f"Prezzo diminuito del {abs(delta)*100:.1f}%: "
                            f"{old_fmt} → {new_fmt}"
                        ),
                        old_value=old_fmt,
                        new_value=new_fmt,
                    )
                )
            else:
                severity = "high" if delta >= price_drop_threshold else "low"
                changes.append(
                    Change(
                        url=url,
                        change_type="price_increase",
                        severity=severity,
                        description=(
                            f"Prezzo aumentato del {delta*100:.1f}%: "
                            f"{old_fmt} → {new_fmt}"
                        ),
                        old_value=old_fmt,
                        new_value=new_fmt,
                    )
                )

        # ── Availability changes ─────────────────────────────────────────────
        old_avail: Optional[bool] = old.get("available")
        new_avail: Optional[bool] = snap.available

        if old_avail is not None and new_avail is not None and old_avail != new_avail:
            if not new_avail:
                changes.append(
                    Change(
                        url=url,
                        change_type="stockout",
                        severity="high",
                        description=f"Prodotto esaurito: {snap.name or url}",
                        old_value="disponibile",
                        new_value="esaurito",
                    )
                )
            else:
                changes.append(
                    Change(
                        url=url,
                        change_type="restock",
                        severity="medium",
                        description=f"Prodotto tornato disponibile: {snap.name or url}",
                        old_value="esaurito",
                        new_value="disponibile",
                    )
                )

        # ── Discount changes ─────────────────────────────────────────────────
        old_discount: Optional[str] = old.get("discount")
        new_discount: Optional[str] = snap.discount

        if old_discount != new_discount:
            if new_discount and not old_discount:
                changes.append(
                    Change(
                        url=url,
                        change_type="discount_added",
                        severity="high",
                        description=f"Sconto rilevato: {new_discount}",
                        old_value=None,
                        new_value=new_discount,
                    )
                )
            elif old_discount and not new_discount:
                changes.append(
                    Change(
                        url=url,
                        change_type="discount_removed",
                        severity="low",
                        description=f"Sconto rimosso (era: {old_discount})",
                        old_value=old_discount,
                        new_value=None,
                    )
                )

        # ── New arrival flag ─────────────────────────────────────────────────
        if snap.new_arrival and not old.get("new_arrival", False):
            changes.append(
                Change(
                    url=url,
                    change_type="new_arrival_flag",
                    severity="medium",
                    description=f"Prodotto marcato come novità: {snap.name or url}",
                    old_value=None,
                    new_value="new_arrival",
                )
            )

    if not changes:
        logger.info("No changes detected across %d URLs.", len(new_snapshots))
    else:
        logger.info("Detected %d change(s).", len(changes))

    return changes
