import re
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.dropdown import DropDown
from kivy.graphics import Color, Rectangle
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window

# Configuración de ventana
Window.size = (600, 600)
Window.minimum_width = 600
Window.minimum_height = 500
Window.clearcolor = (0.95, 0.95, 0.95, 1)
Window.title = "Color Viewer - Paleta dinámica"


# Conversión de HEX a RGB fracción (0–1)
def hex_to_rgb_fraction(hex_color):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return r, g, b

# Clase principal
class ColorWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=15, spacing=10, **kwargs)

        # --- Barra superior: entrada + menú + botón ---
        top_bar = BoxLayout(orientation="horizontal", size_hint=(1, 0.1), spacing=10)
        
        self.input = TextInput(
            hint_text="Ingresa un color (ej: ff0000 o 00ffcc)",
            multiline=False,
            size_hint=(0.5, 1),
            halign="center",
            font_size=16,
            foreground_color=(0, 0, 0, 1),
            background_color=(0, 0, 0, 0)  # Fondo transparente (para usar canvas)
        )
        
        # Dibujar fondo redondeado personalizado
        with self.input.canvas.before:
            Color(0.95, 0.95, 0.95, 1)  # color gris muy claro
            self.bg_rect = RoundedRectangle(radius=[15], pos=self.input.pos, size=self.input.size)

        # Actualizar fondo al cambiar tamaño o posición
        self.input.bind(pos=self.update_input_bg, size=self.update_input_bg)

        def update_input_bg(self, instance, value):
            self.bg_rect.pos = instance.pos
            self.bg_rect.size = instance.size    
            
        # --- Menú desplegable de modos ---
        self.palette_mode = "analogic"

        # Diccionario: lo que se muestra → lo que se envía a la API
        self.mode_map = {
            "Análogico": "analogic",
            "Monocromático": "monochrome",
            "Complementario": "complement",
            "Tríada": "triad",
            "Cuarteto": "quad"
        }

        self.dropdown = DropDown()

        # Crear los botones (texto en español)
        for mode_label in self.mode_map.keys():
            btn = Button(text=mode_label, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn: self.select_mode(btn.text))
            self.dropdown.add_widget(btn)

        self.mode_btn = Button(
            text="Modo: Análogico",
            size_hint=(0.3, 1),
            background_normal='',
            background_color=(0.2, 0.6, 0.9, 1),  # azul suave
            color=(1, 1, 1, 1),
            font_size=16,
            bold=True
        )
        self.mode_btn.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: setattr(self.mode_btn, "text", f"Modo: {x}"))

        # --- Botón de acción ---
        self.btn = Button(text="Mostrar color", size_hint=(0.2, 1))
        self.btn.bind(on_press=self.get_color_info)

        top_bar.add_widget(self.input)
        top_bar.add_widget(self.mode_btn)
        top_bar.add_widget(self.btn)

        # --- Color principal ---
        self.color_box = Widget(size_hint=(1, 0.35))
        with self.color_box.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(pos=self.color_box.pos, size=self.color_box.size)
        self.color_box.bind(pos=self.update_rect, size=self.update_rect)

        # --- Información del color ---
        self.info = Label(
            text="Aquí aparecerá la información del color.",
            halign="center",
            valign="middle",
            size_hint=(1, 0.25)
        )
        self.info.bind(size=self.info.setter("text_size"))

        # --- Título de la paleta ---
        self.palette_title = Label(
            text="Paleta relacionada:",
            bold=True,
            size_hint=(1, 0.05)
        )

        # --- Paleta de colores (responsiva) ---
        self.palette_layout = GridLayout(
            cols=5,                # 5 colores por fila
            spacing=10,            # espacio entre cuadros
            size_hint=(1, 1),
            padding=[10, 10]
        )

        # --- ScrollView contenedor de la paleta ---
        self.palette_scroll = ScrollView(size_hint=(1, 0.25))  # un poco más alto
        self.palette_scroll.add_widget(self.palette_layout)

        # --- Mantener los cuadros cuadrados (proporcionales) ---
        def on_resize(instance, value):
            cell_width = self.palette_layout.width / self.palette_layout.cols
            self.palette_layout.row_default_height = cell_width
            self.palette_layout.row_force_default = True

        self.palette_layout.bind(width=on_resize)

        # --- Estructura general ---
        self.add_widget(top_bar)
        self.add_widget(self.color_box)
        self.add_widget(self.info)
        self.add_widget(self.palette_title)
        self.add_widget(self.palette_scroll)

    # Selección de modo
    def select_mode(self, mode_label):
        # Convertir el texto mostrado (español) al valor que la API entiende (inglés)
        self.palette_mode = self.mode_map.get(mode_label, "analogic")
        self.dropdown.select(mode_label)

    # Dibuja rectángulos de colores
    def draw_color_rect(self, layout, hex_color):
        color_widget = Widget(size_hint=(1, 1))
        r, g, b = hex_to_rgb_fraction(hex_color)

        with color_widget.canvas.before:
            Color(r, g, b, 1)
            rect = Rectangle(pos=color_widget.pos, size=color_widget.size)

        color_widget.bind(
            pos=lambda instance, value: setattr(rect, "pos", instance.pos),
            size=lambda instance, value: setattr(rect, "size", instance.size)
        )

        layout.add_widget(color_widget)

    # Actualiza fondo principal
    def update_rect(self, *args):
        self.rect.pos = self.color_box.pos
        self.rect.size = self.color_box.size

    # Obtiene la información del color
    def get_color_info(self, instance):
        color_code = self.input.text.strip().lstrip("#")
        if not color_code:
            self.info.text = "Ingresa un color válido."
            return
        # Solo aceptar valores HEX válidos (3 o 6 caracteres [0-9a-fA-F])
        if not re.fullmatch(r"[0-9a-fA-F]{3}|[0-9a-fA-F]{6}", color_code):
            self.info.text = (
                "Formato inválido.\n"
                "Usa un código hexadecimal como:\n"
                "ff0000 (rojo) o 00ffcc (turquesa)."
            )
            return
        
        # --- Color principal ---
        url = f"https://www.thecolorapi.com/id?hex={color_code}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            hex_color = data["hex"]["value"]
            name = data["name"]["value"]
            rgb = data["rgb"]
            hsl = data["hsl"]

            self.info.text = (
                f"[b]{name}[/b]\n"
                f"HEX: {hex_color}\n"
                f"RGB: ({rgb['r']}, {rgb['g']}, {rgb['b']})\n"
                f"HSL: ({int(hsl['h'])}, {int(hsl['s']*100)}%, {int(hsl['l']*100)}%)"
            )
            self.info.markup = True

            # Actualiza color principal
            r, g, b = hex_to_rgb_fraction(hex_color)
            with self.color_box.canvas.before:
                Color(r, g, b, 1)
                self.rect = Rectangle(pos=self.color_box.pos, size=self.color_box.size)

            # --- Paleta ---
            scheme_url = f"https://www.thecolorapi.com/scheme?hex={color_code}&mode={self.palette_mode}"
            palette_resp = requests.get(scheme_url)
            self.palette_layout.clear_widgets()

            if palette_resp.status_code == 200:
                scheme_data = palette_resp.json()
                colors = [c["hex"]["value"] for c in scheme_data["colors"]]
                self.palette_title.text = f"Paleta relacionada (modo: {self.palette_mode.capitalize()}):"
                for c in colors:
                    self.draw_color_rect(self.palette_layout, c)
        else:
            self.info.text = "No se pudo obtener el color. Verifica el formato o conexión."


class ColorApp(App):
    def build(self):
        return ColorWidget()


if __name__ == "__main__":
    ColorApp().run()