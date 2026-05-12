import flet as ft
import sys
import os
from ui.theme import Theme
from ui.widgets.sidebar import Sidebar
from ui.views.dashboard import DashboardView
from ui.views.products import ProductsView
from ui.views.scrapers import ScrapersView
from ui.views.settings import SettingsView

# Add parent dir to path so we can import bot modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

class App:
    def __init__(self, page: ft.Page):
        self.page = page
        page.title = "Competitor Monitor Bot"
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 0
        page.window.width = 1280
        page.window.height = 780
        page.window.min_width = 900
        page.window.min_height = 600
        page.bgcolor = Theme.BG_DARK

        # Bot modules dict
        self._bot_modules = {}
        self._import_bot_modules()

        # Content area
        self._content_area = ft.Container(expand=True, padding=0)

        # Sidebar
        self._sidebar = Sidebar(on_navigate=self._navigate)

        # Assemble layout
        page.add(ft.Row([self._sidebar, self._content_area], expand=True, spacing=0))

        # Navigate to dashboard by default
        self._navigate("dashboard")

    def _import_bot_modules(self):
        try:
            import config
            import scraper
            import comparator
            import summarizer
            import notifier
            import state_manager
            self._bot_modules = {
                "config": config,
                "scraper": scraper,
                "comparator": comparator,
                "summarizer": summarizer,
                "notifier": notifier,
                "state_manager": state_manager,
            }
        except ImportError as ex:
            print(f"Warning: bot modules not available: {ex}")

    def _navigate(self, view_name: str):
        view = self._get_view(view_name)
        if view:
            self._content_area.content = view.build()
            self._content_area.update()

    def _get_view(self, name: str):
        views = {
            "dashboard": DashboardView(self._content_area, self._bot_modules),
            "products": ProductsView(self._content_area, self._bot_modules),
            "scrapers": ScrapersView(self._content_area, self._bot_modules),
            "settings": SettingsView(self._content_area, self._bot_modules),
        }
        return views.get(name)

    def shutdown(self, e=None):
        print("Shutting down Competitor Monitor Bot UI...")


def main(page: ft.Page):
    App(page)


if __name__ == "__main__":
    ft.app(target=main)
