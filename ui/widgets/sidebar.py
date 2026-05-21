import flet as ft
from ui.theme import Theme

class Sidebar(ft.Container):
    def __init__(self, on_navigate):
        self._on_navigate = on_navigate
        self._items = {}

        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("products", "📦  Prodotti"),
            ("scrapers", "⚡  Scraper"),
            ("settings", "⚙️  Impostazioni"),
        ]

        content_items = []

        # App title
        title = ft.Container(
            content=ft.Column([
                ft.Text("🤖", size=28, text_align=ft.TextAlign.CENTER),
                ft.Text("Competitor Monitor", size=16, weight=ft.FontWeight.BOLD, color=Theme.TEXT_PRIMARY, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            padding=ft.Padding.only(bottom=24, top=12),
        )
        content_items.append(title)

        for name, label in nav_items:
            container = ft.Container(
                content=ft.Row([
                    ft.Text(label, size=14, color=Theme.TEXT_SECONDARY),
                ]),
                padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                border_radius=8,
                ink=True,
                on_click=lambda _, n=name: self._on_item_click(n),
                margin=ft.margin.symmetric(horizontal=8, vertical=2),
            )
            self._items[name] = container
            content_items.append(container)

        # Version at bottom
        version = ft.Container(
            content=ft.Text("v1.0.0 — €49-199/mo", size=11, color=Theme.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
            padding=ft.Padding.only(top=24),
        )

        content = ft.Column(content_items + [version], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        super().__init__(
            content=content,
            width=220,
            bgcolor=Theme.BG_SIDEBAR,
            padding=ft.Padding.only(top=20),
            border=ft.Border.only(right=ft.BorderSide(1, Theme.BORDER)),
        )

    def _on_item_click(self, name):
        for n, c in self._items.items():
            c.bgcolor = Theme.BG_SIDEBAR_HOVER if n == name else None
            c.content.controls[0].color = Theme.TEXT_PRIMARY if n == name else Theme.TEXT_SECONDARY
            c.update()
        self._on_navigate(name)

    def set_active(self, name):
        self._on_item_click(name)
