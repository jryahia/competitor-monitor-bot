import flet as ft
from ui.theme import Theme

_STATUS_STYLES = {
    "available": {"bg": "#00FF8815", "text": "#00FF88", "label": "🟢 Disponibile"},
    "out_of_stock": {"bg": "#FF444415", "text": "#FF4444", "label": "🔴 Esaurito"},
    "new": {"bg": "#58A6FF15", "text": "#58A6FF", "label": "🆕 Nuovo"},
    "discount": {"bg": "#FFB34715", "text": "#FFB347", "label": "🔥 Sconto"},
    "unknown": {"bg": "#484F5815", "text": "#484F58", "label": "⚪ Sconosciuto"},
}

class StatusBadge(ft.Container):
    def __init__(self, status: str = "unknown"):
        style = _STATUS_STYLES.get(status, _STATUS_STYLES["unknown"])
        super().__init__(
            content=ft.Text(style["label"], size=11, weight=ft.FontWeight.W_500, color=style["text"]),
            bgcolor=style["bg"],
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
        )

    @staticmethod
    def from_product(product: dict):
        if product.get("is_new_arrival"):
            return StatusBadge("new")
        if product.get("discount_percentage") and product["discount_percentage"] > 0:
            return StatusBadge("discount")
        if product.get("availability") in (True, "in stock", "disponibile"):
            return StatusBadge("available")
        if product.get("availability") in (False, "out of stock", "esaurito"):
            return StatusBadge("out_of_stock")
        return StatusBadge("unknown")
