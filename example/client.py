import flet as ft
import socket

class UI(ft.Column):
    def __init__(self):
        super().__init__()
        self.b = ft.Button(content = "Click Me!", on_click=self.changeText)
        # ft.TextField(label = "Submit")
        self.t = ft.Text(value = "HI")
        self.controls = [self.b, self.t]

    def changeText(self):
        self.t.value = "Hello"

def main(page):
    page.title = "Smart Home App"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.add(UI())

ft.app(main)