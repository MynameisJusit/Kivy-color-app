import re
import requests
from functools import partial
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle


def hex_to_rgb_fraction(hex_color):
    """Convierte un color HEX (#RRGGBB) a RGB normalizado (0–1)."""
    hex_color = hex_color.strip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return r, g, b


class ColorWidget(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=15, padding=[20, 20, 20, 20], **kwargs)

        # --- Campo de texto moderno ---
        self.input = MDTextField(
            hint_text="Ingresa un color (ej: ff0000 o 00ffcc)",
            mode="round",
            size_hint=(0.5, None),
            height="48dp",
            font_size=16,
            text_color_focus=(1, 1, 1, 1),
            hint_text_color_focus=(0.7, 0.7, 0.7, 1),
            pos_hint={"center_y": 0.5}
        )

        # --- Botón de búsqueda ---
        self.search_btn = MDRaisedButton(
            text="Buscar color",
            size_hint=(0.2, None),
            height="48dp",
            on_release=self.get_color_info
        )

        # --- Menú desplegable de modos ---
        self.palette_mode = "analogic"
        self.mode_map = {
            "Análogico": "analogic",
            "Monocromático": "monochrome",
            "Complementario": "complement",
            "Tríada": "triad",
            "Cuarteto": "quad"
        }

        self.mode_btn = MDRaisedButton(
            text="Modo: Análogico",
            size_hint=(0.3, None),
            height="48dp"
        )

        # FIX: usar partial para evitar cierres
        menu_items = []
        for label in self.mode_map.keys():
            item = {
                "viewclass": "OneLineListItem",
                "text": label,
                "on_release": partial(self.select_mode, label)
            }
            menu_items.append(item)

        self.menu = MDDropdownMenu(caller=self.mode_btn, items=menu_items, width_mult=4)
        self.mode_btn.bind(on_release=lambda instance: self.menu.open())

        # --- Fila superior (alineada y centrada) ---
        top_layout = MDBoxLayout(
            orientation="horizontal",
            spacing=20,
            size_hint=(1, None),
            height="70dp",
            pos_hint={"center_y": 0.5},
            adaptive_height=False
        )

        for btn in [self.search_btn, self.mode_btn]:
            btn.md_bg_color = self.theme_cls.primary_color
            btn.size_hint_y = None
            btn.height = "48dp"
            btn.radius = [12]
            btn.pos_hint = {"center_y": 0.5}

        self.input.pos_hint = {"center_y": 0.5}
        self.input.size_hint_y = None
        self.input.height = "48dp"

        top_layout.add_widget(self.input)
        top_layout.add_widget(self.search_btn)
        top_layout.add_widget(self.mode_btn)
        self.add_widget(top_layout)

        # --- Área principal del color ---
        self.color_card = MDCard(size_hint=(1, 0.3), radius=[20], md_bg_color=(0.15, 0.15, 0.16, 1))
        self.color_box = Widget()
        with self.color_box.canvas.before:
            Color(0.15, 0.15, 0.16, 1)
            self.rect = RoundedRectangle(radius=[20], pos=self.color_box.pos, size=self.color_box.size)
        self.color_box.bind(pos=self.update_rect, size=self.update_rect)
        self.color_card.add_widget(self.color_box)
        self.add_widget(self.color_card)

        # --- Etiqueta de información ---
        self.info = MDLabel(text="", halign="center", font_style="H6", size_hint=(1, None), height="40dp")
        self.add_widget(self.info)

        # --- Paleta de colores ---
        self.palette_title = MDLabel(
            text="Paleta relacionada:",
            halign="center",
            size_hint=(1, None),
            height="40dp",
            theme_text_color="Secondary"
        )
        self.add_widget(self.palette_title)

        self.palette_layout = MDGridLayout(cols=5, spacing=10, padding=[10, 10], adaptive_height=True)
        self.palette_scroll = MDScrollView(size_hint=(1, 0.3))
        self.palette_scroll.add_widget(self.palette_layout)
        self.add_widget(self.palette_scroll)

    # -----------------------------
    # Métodos gráficos
    # -----------------------------
    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    # -----------------------------
    # Selección de modo
    # -----------------------------
    def select_mode(self, mode_label, *args):
        self.palette_mode = self.mode_map.get(mode_label, "analogic")
        self.mode_btn.text = f"Modo: {mode_label}"
        self.menu.dismiss()

    # -----------------------------
    # Consulta principal a la API
    # -----------------------------
    def get_color_info(self, instance):
        color_input = self.input.text.strip().lstrip("#")
        if not re.fullmatch(r"[0-9a-fA-F]{6}", color_input):
            self.info.text = "Ingresa un color HEX válido \n6 dígitos combinación de A-F y 0-9."
            return

        url = f"https://www.thecolorapi.com/id?hex={color_input}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
        except Exception:
            self.info.text = "Error al conectar con la API."
            return

        hex_value = data.get("hex", {}).get("value", "#FFFFFF")
        name = data.get("name", {}).get("value", "Desconocido")
        self.info.text = f"{name} ({hex_value})"

        r, g, b = hex_to_rgb_fraction(hex_value)
        self.color_box.canvas.before.clear()
        with self.color_box.canvas.before:
            Color(r, g, b, 1)
            self.rect = RoundedRectangle(radius=[20], pos=self.color_box.pos, size=self.color_box.size)
        self.color_box.bind(pos=self.update_rect, size=self.update_rect)

        self.get_palette(color_input)

    # -----------------------------
    # Paleta relacionada
    # -----------------------------
    def get_palette(self, hex_color):
        url = f"https://www.thecolorapi.com/scheme?hex={hex_color}&mode={self.palette_mode}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
        except Exception:
            self.info.text = "Error al obtener la paleta."
            return

        colors = data.get("colors", [])
        self.palette_layout.clear_widgets()
        for color in colors:
            hex_value = color["hex"]["value"]
            self.draw_color_rect(hex_value)

    # -----------------------------
    # Dibujar cuadros de paleta con etiqueta HEX
    # -----------------------------
    def draw_color_rect(self, hex_color):
        color_box = MDBoxLayout(orientation="vertical", size_hint=(1, None), height="100dp", spacing=5)

        color_widget = Widget(size_hint=(1, None), height=70)
        r, g, b = hex_to_rgb_fraction(hex_color)
        with color_widget.canvas.before:
            Color(r, g, b, 1)
            rect = Rectangle(pos=color_widget.pos, size=color_widget.size)
        color_widget.bind(
            pos=lambda instance, value: setattr(rect, "pos", instance.pos),
            size=lambda instance, value: setattr(rect, "size", instance.size)
        )

        label = MDLabel(
            text=hex_color,
            halign="center",
            theme_text_color="Primary",
            size_hint=(1, None),
            height="20dp",
            font_style="Caption"
        )

        color_box.add_widget(color_widget)
        color_box.add_widget(label)
        self.palette_layout.add_widget(color_box)


class ColorApp(MDApp):
    def build(self):
        self.title = "Colormatic"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        return ColorWidget()


if __name__ == "__main__":
    ColorApp().run()
