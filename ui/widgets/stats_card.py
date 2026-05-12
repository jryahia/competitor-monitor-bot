import flet as ft
from ui.theme import Theme

class StatsCard(ft.Container):
    def __init__(self, label: str, value: str, subtitle: str = "", accent_color: str = Theme.ACCENT_BLUE):
        self._label = ft.Text(label, size=12, color=Theme.TEXT_SECONDARY)
        self._value = ft.Text(value, size=28, weight=ft.FontWeight.BOLD, color=accent_color)
        self._subtitle = ft.Text(subtitle, size=11, color=Theme.TEXT_MUTED)

        super().__init__(
            content=ft.Column([
                self._label,
                ft.Container(height=4),
                self._value,
                ft.Container(height=2),
                self._subtitle,
            ], spacing=0),
            bgcolor=Theme.BG_CARD,
            border=ft.border.all(1, Theme.BORDER),
            border_radius=Theme.CARD_RADIUS,
            padding=20,
            expand=True,
            ink=False,
        )

    def update_value(self, value: str):
        self._value.value = value
        self._value.update()

    def update_subtitle(self, subtitle: str):
        self._subtitle.value = subtitle
        self._subtitle.update()
