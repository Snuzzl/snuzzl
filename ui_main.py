import flet as ft
from ui_login import Account, MainScreen


def main(page: ft.Page):
    page.title = "Snuzzl"
    page.window.width = 360
    page.window.height = 640
    page.vertical_alignment = 'center'
    page.horizontal_alignment = 'center'
    page.bgcolor = 'white'

    acc = Account()

    MainScreen(page, acc).show()


ft.run(main)
