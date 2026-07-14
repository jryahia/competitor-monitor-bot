import flet as ft
from ui.theme import Theme

class ScrapersView:
    def __init__(self, content_area: ft.Container, bot_modules: dict):
        self._content_area = content_area
        self._bot = bot_modules
        self._urls_list = ft.Column(spacing=8)
        self._new_url_input = ft.TextField(
            hint_text="Inserisci URL e-commerce...",
            border_color=Theme.BORDER,
            color=Theme.TEXT_PRIMARY,
            hint_style=ft.TextStyle(color=Theme.TEXT_MUTED),
            expand=True,
        )

    def build(self):
        header = ft.Text("⚡  Gestione Scraper", size=22, weight=ft.FontWeight.BOLD, color=Theme.TEXT_PRIMARY)

        # Add URL row
        add_row = ft.Row([
            self._new_url_input,
            ft.ElevatedButton(
                "➕ Aggiungi",
                on_click=self._on_add_url,
                style=ft.ButtonStyle(
                    color=Theme.TEXT_PRIMARY,
                    bgcolor=Theme.ACCENT_BLUE,
                    shape=ft.RoundedRectangleBorder(radius=Theme.BUTTON_RADIUS),
                ),
            ),
        ], spacing=12)

        # URL list card
        url_list_header = ft.Text("URL Configurati", size=16, weight=ft.FontWeight.W_600, color=Theme.TEXT_PRIMARY)
        self._urls_list = ft.Column(spacing=8)

        # Load URLs from config
        try:
            config = self._bot["config"].Config.from_env()
            for url in config.competitor_urls:
                self._urls_list.controls.append(self._build_url_item(url))
        except Exception:
            self._urls_list.controls.append(
                ft.Text("Configura le URL nel file .env", size=13, color=Theme.TEXT_MUTED, italic=True)
            )

        url_list_card = ft.Container(
            content=ft.Column([
                url_list_header,
                ft.Divider(color=Theme.BORDER, height=16),
                self._urls_list,
            ]),
            bgcolor=Theme.BG_CARD,
            border=ft.Border.all(1, Theme.BORDER),
            border_radius=Theme.CARD_RADIUS,
            padding=20,
        )

        return ft.Container(
            content=ft.Column([
                header,
                ft.Container(height=4),
                ft.Text("Aggiungi o rimuovi URL competitor da monitorare", size=13, color=Theme.TEXT_MUTED),
                ft.Container(height=16),
                add_row,
                ft.Container(height=16),
                url_list_card,
            ], scroll=ft.ScrollMode.AUTO),
            padding=20,
        )

    def _build_url_item(self, url: str):
        short_url = url[:50] + "..." if len(url) > 50 else url
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text("🟢", size=14),
                    margin=ft.margin.only(right=8),
                ),
                ft.Text(short_url, size=13, color=Theme.TEXT_PRIMARY, expand=True),
                ft.Container(
                    content=ft.Text("⚪ Attivo", size=11, color=Theme.ACCENT_GREEN),
                    bgcolor="#00FF8815",
                    border_radius=12,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                ),
                ft.IconButton(ft.icons.DELETE_OUTLINE, icon_size=18, icon_color=Theme.ACCENT_RED, on_click=lambda _, u=url: self._on_remove_url(u)),
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=Theme.BG_INPUT,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        )

    def _on_add_url(self, e):
        url = self._new_url_input.value.strip()
        if not url:
            return
        self._urls_list.controls.append(self._build_url_item(url))
        self._new_url_input.value = ""
        self._new_url_input.update()
        self._urls_list.update()

    def _on_remove_url(self, url):
        for ctrl in self._urls_list.controls[:]:
            if isinstance(ctrl, ft.Container):
                content_row = ctrl.content
                if isinstance(content_row, ft.Row):
                    for cell in content_row.controls:
                        if isinstance(cell, ft.Text) and url[:50] in cell.value:
                            self._urls_list.controls.remove(ctrl)
                            break
        self._urls_list.update()
