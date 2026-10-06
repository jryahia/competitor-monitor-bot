import flet as ft
from ui.theme import Theme
from ui.widgets.status_badge import StatusBadge

class ProductsView:
    def __init__(self, content_area: ft.Container, bot_modules: dict):
        self._content_area = content_area
        self._bot = bot_modules
        self._search_input = ft.TextField(
            hint_text="Cerca prodotto per nome...",
            prefix_icon=ft.Icons.SEARCH,
            border_color=Theme.BORDER,
            color=Theme.TEXT_PRIMARY,
            hint_style=ft.TextStyle(color=Theme.TEXT_MUTED),
            on_submit=self._on_search,
            width=400,
        )
        self._table = None
        self._products_data = {}

    def build(self):
        header = ft.Text(" Prodotti Tracciati", size=22, weight=ft.FontWeight.BOLD, color=Theme.TEXT_PRIMARY)

        self._table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nome Prodotto", color=Theme.TEXT_SECONDARY, weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Prezzo", color=Theme.TEXT_SECONDARY, weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Disponibilità", color=Theme.TEXT_SECONDARY, weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Sconto", color=Theme.TEXT_SECONDARY, weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Stato", color=Theme.TEXT_SECONDARY, weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Ultimo Rilevamento", color=Theme.TEXT_SECONDARY, weight=ft.FontWeight.W_600)),
            ],
            rows=[],
            heading_row_color=Theme.BG_INPUT,
            heading_row_height=44,
            data_row_color={"": Theme.BG_CARD},
            border=ft.Border.all(1, Theme.BORDER),
            border_radius=8,
            horizontal_lines=ft.BorderSide(0.5, Theme.BORDER),
        )

        table_container = ft.Container(
            content=ft.Column([
                self._search_input,
                ft.Container(height=12),
                ft.ResponsiveRow([ft.Container(content=self._table, col={"xs": 12})]),
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
                ft.Text("Tutti i prodotti rilevati dai competitor monitorati", size=13, color=Theme.TEXT_MUTED),
                ft.Container(height=16),
                table_container,
            ], scroll=ft.ScrollMode.AUTO),
            padding=20,
        )

    def load_products(self, products: dict):
        self._products_data = products
        self._refresh_table()

    def _on_search(self, e):
        self._refresh_table(self._search_input.value.strip().lower())

    def _refresh_table(self, query: str = ""):
        self._table.rows.clear()
        count = 0
        for url, prods in self._products_data.items():
            for name, p in prods.items():
                if query and query not in name.lower():
                    continue
                count += 1
                price = f"€{p.get('price', '?')}" if p.get('price') else "—"
                availability = "Sì" if p.get("availability") in (True, "in stock") else "No"
                discount = f"-{p['discount_percentage']}%" if p.get("discount_percentage") else "—"
                badge = StatusBadge.from_product(p)
                last_seen = p.get("last_seen", p.get("timestamp", "—"))[:10] if p.get("last_seen") else "—"

                self._table.rows.append(
                    ft.DataRow([
                        ft.DataCell(ft.Text(name[:50], size=13, color=Theme.TEXT_PRIMARY)),
                        ft.DataCell(ft.Text(price, size=13, color=Theme.ACCENT_GREEN, weight=ft.FontWeight.W_600)),
                        ft.DataCell(ft.Text(availability, size=14)),
                        ft.DataCell(ft.Text(discount, size=13, color=Theme.ACCENT_AMBER if discount != "—" else Theme.TEXT_MUTED)),
                        ft.DataCell(badge),
                        ft.DataCell(ft.Text(last_seen, size=12, color=Theme.TEXT_MUTED)),
                    ])
                )

        if count == 0:
            self._table.rows.append(
                ft.DataRow([ft.DataCell(ft.Text("Nessun prodotto trovato", color=Theme.TEXT_MUTED, italic=True)) for _ in range(6)])
            )
        self._table.update()
