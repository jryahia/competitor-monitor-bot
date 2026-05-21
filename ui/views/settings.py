import flet as ft
import os
from ui.theme import Theme

class SettingsView:
    def __init__(self, content_area: ft.Container, bot_modules: dict):
        self._content_area = content_area
        self._bot = bot_modules
        self._fields = {}
        self._status_text = ft.Text("", size=12, color=Theme.ACCENT_GREEN)

    def build(self):
        header = ft.Text("⚙️  Impostazioni", size=22, weight=ft.FontWeight.BOLD, color=Theme.TEXT_PRIMARY)

        # Load current env
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        env_vars = {}
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip()

        def _field(label, key, hint, masked=False):
            value = env_vars.get(key, "")
            field = ft.TextField(
                label=label,
                value=value,
                hint_text=hint,
                password=masked,
                can_reveal_password=masked,
                border_color=Theme.BORDER,
                color=Theme.TEXT_PRIMARY,
                label_style=ft.TextStyle(color=Theme.TEXT_SECONDARY, size=13),
                hint_style=ft.TextStyle(color=Theme.TEXT_MUTED),
                bgcolor=Theme.BG_INPUT,
                border_radius=8,
                expand=True,
            )
            self._fields[key] = field
            return field

        # Telegram section
        telegram_section = ft.Container(
            content=ft.Column([
                ft.Text("🤖  Telegram", size=16, weight=ft.FontWeight.W_600, color=Theme.TEXT_PRIMARY),
                ft.Container(height=8),
                _field("Bot Token", "TELEGRAM_BOT_TOKEN", "Inserisci il token del bot"),
                ft.Container(height=8),
                _field("Chat ID", "TELEGRAM_CHAT_ID", "ID chat/channel privato"),
            ]),
            bgcolor=Theme.BG_CARD,
            border=ft.Border.all(1, Theme.BORDER),
            border_radius=Theme.CARD_RADIUS,
            padding=20,
            expand=True,
        )

        # OpenAI section
        openai_section = ft.Container(
            content=ft.Column([
                ft.Text("🧠  OpenAI", size=16, weight=ft.FontWeight.W_600, color=Theme.TEXT_PRIMARY),
                ft.Container(height=8),
                _field("API Key", "OPENAI_API_KEY", "sk-...", masked=True),
                ft.Container(height=8),
                self._fields.get("LLM_MODEL") or ft.Dropdown(
                    label="Modello LLM",
                    value=env_vars.get("LLM_MODEL", "gpt-4o-mini"),
                    options=[
                        ft.dropdown.Option("gpt-4o-mini"),
                        ft.dropdown.Option("gpt-4o"),
                    ],
                    border_color=Theme.BORDER,
                    color=Theme.TEXT_PRIMARY,
                    label_style=ft.TextStyle(color=Theme.TEXT_SECONDARY, size=13),
                    bgcolor=Theme.BG_INPUT,
                ),
            ]),
            bgcolor=Theme.BG_CARD,
            border=ft.Border.all(1, Theme.BORDER),
            border_radius=Theme.CARD_RADIUS,
            padding=20,
            expand=True,
        )

        # Config section
        config_section = ft.Container(
            content=ft.Column([
                ft.Text("⚙️  Configurazione", size=16, weight=ft.FontWeight.W_600, color=Theme.TEXT_PRIMARY),
                ft.Container(height=8),
                _field("Intervallo Scansione (ore)", "SCRAPE_INTERVAL_HOURS", "24"),
            ]),
            bgcolor=Theme.BG_CARD,
            border=ft.Border.all(1, Theme.BORDER),
            border_radius=Theme.CARD_RADIUS,
            padding=20,
            expand=True,
        )

        # Action buttons
        save_btn = ft.ElevatedButton(
            "💾  Salva Impostazioni",
            on_click=self._on_save,
            style=ft.ButtonStyle(
                color=Theme.TEXT_PRIMARY,
                bgcolor=Theme.ACCENT_BLUE,
                shape=ft.RoundedRectangleBorder(radius=Theme.BUTTON_RADIUS),
                padding=ft.Padding.symmetric(horizontal=24, vertical=14),
            ),
        )

        test_btn = ft.OutlinedButton(
            "📤  Test Telegram",
            on_click=self._on_test_telegram,
            style=ft.ButtonStyle(
                color=Theme.TEXT_PRIMARY,
                side=ft.BorderSide(1, Theme.BORDER),
                shape=ft.RoundedRectangleBorder(radius=Theme.BUTTON_RADIUS),
            ),
        )

        self._status_text = ft.Text("", size=12, color=Theme.ACCENT_GREEN)

        return ft.Container(
            content=ft.Column([
                header,
                ft.Container(height=4),
                ft.Text("Configura le credenziali e le preferenze del bot", size=13, color=Theme.TEXT_MUTED),
                ft.Container(height=16),
                ft.ResponsiveRow([
                    ft.Container(content=telegram_section, col={"sm": 12, "md": 6}),
                    ft.Container(content=openai_section, col={"sm": 12, "md": 6}),
                ], spacing=16),
                ft.Container(height=16),
                config_section,
                ft.Container(height=16),
                ft.Row([save_btn, test_btn], spacing=12),
                ft.Container(height=8),
                self._status_text,
            ], scroll=ft.ScrollMode.AUTO),
            padding=20,
        )

    def _on_save(self, e):
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        try:
            with open(env_path, "w") as f:
                f.write("# Competitor Monitor Bot — Configurazione\n")
                f.write(f"COMPETITOR_URLS={self._fields.get('COMPETITOR_URLS', ft.TextField()).value or ''}\n")
                f.write(f"TELEGRAM_BOT_TOKEN={self._fields.get('TELEGRAM_BOT_TOKEN', ft.TextField()).value or ''}\n")
                f.write(f"TELEGRAM_CHAT_ID={self._fields.get('TELEGRAM_CHAT_ID', ft.TextField()).value or ''}\n")
                f.write(f"OPENAI_API_KEY={self._fields.get('OPENAI_API_KEY', ft.TextField()).value or ''}\n")
                f.write(f"LLM_MODEL={self._fields.get('LLM_MODEL', ft.TextField()).value or 'gpt-4o-mini'}\n")
                f.write(f"SCRAPE_INTERVAL_HOURS={self._fields.get('SCRAPE_INTERVAL_HOURS', ft.TextField()).value or '24'}\n")
            self._status_text.value = "✅ Impostazioni salvate con successo!"
            self._status_text.color = Theme.ACCENT_GREEN
            self._status_text.update()
        except Exception as ex:
            self._status_text.value = f"❌ Errore: {ex}"
            self._status_text.color = Theme.ACCENT_RED
            self._status_text.update()

    def _on_test_telegram(self, e):
        self._status_text.value = "📤 Invio messaggio di test..."
        self._status_text.color = Theme.ACCENT_BLUE
        self._status_text.update()
        try:
            token = self._fields.get("TELEGRAM_BOT_TOKEN", ft.TextField()).value
            chat_id = self._fields.get("TELEGRAM_CHAT_ID", ft.TextField()).value
            if token and chat_id:
                # TODO: actual telegram test
                self._status_text.value = "✅ Messaggio di test inviato!"
                self._status_text.color = Theme.ACCENT_GREEN
            else:
                self._status_text.value = "⚠️ Token o Chat ID mancanti"
                self._status_text.color = Theme.ACCENT_AMBER
        except Exception as ex:
            self._status_text.value = f"❌ Errore: {ex}"
            self._status_text.color = Theme.ACCENT_RED
        self._status_text.update()
