import flet as ft
import asyncio
from datetime import datetime
from ui.theme import Theme
from ui.widgets.stats_card import StatsCard
from ui.widgets.status_badge import StatusBadge

class DashboardView:
    def __init__(self, content_area: ft.Container, bot_modules: dict):
        self._content_area = content_area
        self._bot = bot_modules
        self._stats = {}
        self._changes_feed = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)
        self._scan_btn = None
        self._scanning = False

    def build(self):
        header = ft.Text(" Dashboard", size=22, weight=ft.FontWeight.BOLD, color=Theme.TEXT_PRIMARY)

        # Stat cards row
        self._stats = {
            "urls": StatsCard("URL Monitorati", "5", "Competitor configurati", Theme.ACCENT_BLUE),
            "products": StatsCard("Prodotti Tracciati", "0", "In tutte le vetrine", Theme.ACCENT_GREEN),
            "last_scan": StatsCard("Ultima Scansione", "Mai", "—", Theme.ACCENT_AMBER),
            "changes": StatsCard("Cambiamenti Oggi", "0", "Rilevati", Theme.ACCENT_RED),
        }
        stats_row = ft.Row(
            list(self._stats.values()),
            spacing=16,
        )

        # Scan button
        self._scan_btn = ft.ElevatedButton(
            "Scansiona Ora",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._on_scan,
            style=ft.ButtonStyle(
                color=Theme.TEXT_PRIMARY,
                bgcolor=Theme.ACCENT_GREEN,
                shape=ft.RoundedRectangleBorder(radius=Theme.BUTTON_RADIUS),
                padding=ft.Padding.symmetric(horizontal=24, vertical=14),
            ),
        )

        # Recent changes section
        changes_header = ft.Text(" Cambiamenti Recenti", size=16, weight=ft.FontWeight.W_600, color=Theme.TEXT_PRIMARY)
        self._changes_feed = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)
        self._changes_feed.controls.append(
            ft.Container(
                content=ft.Text("Nessun cambiamento nelle ultime 24 ore ", size=13, color=Theme.TEXT_MUTED),
                padding=20,
            )
        )

        changes_card = ft.Container(
            content=ft.Column([
                changes_header,
                ft.Divider(color=Theme.BORDER, height=16),
                ft.Container(content=self._changes_feed, height=250),
            ]),
            bgcolor=Theme.BG_CARD,
            border=ft.Border.all(1, Theme.BORDER),
            border_radius=Theme.CARD_RADIUS,
            padding=20,
        )

        return ft.Container(
            content=ft.Column([
                header,
                ft.Container(height=16),
                stats_row,
                ft.Container(height=16),
                ft.Row([self._scan_btn], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=16),
                changes_card,
            ], scroll=ft.ScrollMode.AUTO),
            padding=20,
        )

    async def _on_scan(self, e):
        if self._scanning:
            return
        self._scanning = True
        self._scan_btn.content = "Scansione in corso..."
        self._scan_btn.disabled = True
        self._scan_btn.update()

        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, self._run_scrape)
            self._update_stats(results)
        except Exception as ex:
            self._changes_feed.controls.insert(0, ft.Text(f"Errore: {ex}", size=12, color=Theme.ACCENT_RED))
            self._changes_feed.update()
        finally:
            self._scanning = False
            self._scan_btn.content = "Scansiona Ora"
            self._scan_btn.disabled = False
            self._scan_btn.update()

    def _run_scrape(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            config = self._bot["config"].Config.from_env()
            scraper = self._bot["scraper"]
            state_mgr = self._bot["state_manager"]
            comparator = self._bot["comparator"]

            new_data = {}
            for url in config.competitor_urls:
                products = scraper.scrape_url_sync(url)
                if products:
                    new_data[url] = {p["name"]: p for p in products}

            old_state = state_mgr.load_state(config.state_file_path)
            changes = comparator.compare(old_state, new_data)
            merged = {}
            for url, products in new_data.items():
                merged[url] = {**old_state.get(url, {}), **products}
            state_mgr.save_state(merged, config.state_file_path)

            summary = self._bot["summarizer"].generate_summary(changes, config)
            return {"changes": changes, "summary": summary, "products": new_data, "urls": len(new_data)}
        finally:
            loop.close()

    def _update_stats(self, results):
        now = datetime.now().strftime("%H:%M:%S")
        self._stats["urls"].update_value(str(results.get("urls", 0)))
        total_products = sum(len(prods) for prods in results.get("products", {}).values())
        self._stats["products"].update_value(str(total_products))
        self._stats["last_scan"].update_value(now)
        self._stats["last_scan"].update_subtitle(datetime.now().strftime("%d/%m/%Y"))
        total_changes = sum(len(c) for c in results.get("changes", {}).values())
        self._stats["changes"].update_value(str(total_changes))

        # Update changes feed
        self._changes_feed.controls.clear()
        changes = results.get("changes", {})
        if not changes or all(len(v) == 0 for v in changes.values()):
            self._changes_feed.controls.append(
                ft.Container(content=ft.Text("Nessuna variazione ", size=13, color=Theme.TEXT_MUTED), padding=20)
            )
        else:
            for url, url_changes in changes.items():
                for c in url_changes[:10]:
                    icon = {
                        "price_drop": ft.Icons.TRENDING_DOWN,
                        "price_increase": ft.Icons.TRENDING_UP,
                        "stockout": ft.Icons.REMOVE_SHOPPING_CART,
                        "restock": ft.Icons.INVENTORY_2,
                        "new_product": ft.Icons.FIBER_NEW,
                        "discount": ft.Icons.LOCAL_OFFER,
                    }.get(c.get("type", ""), ft.Icons.INFO_OUTLINE)
                    color = Theme.ACCENT_RED if c.get("severity") == "high" else Theme.ACCENT_AMBER if c.get("severity") == "medium" else Theme.TEXT_SECONDARY
                    self._changes_feed.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(icon, size=16, color=color),
                                ft.Text(c.get('product_name', '?'), size=13, color=color, expand=True),
                                ft.Text(f"{c.get('old_value', '')} → {c.get('new_value', '')}", size=11, color=Theme.TEXT_MUTED),
                            ]),
                            bgcolor=Theme.BG_INPUT,
                            border_radius=8,
                            padding=10,
                        )
                    )
        self._changes_feed.update()
