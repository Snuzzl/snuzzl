import flet
from ui_login import Account, MainScreen


def main(page: flet.Page):
    page.title = "Snuzzl"
    page.window.width = 360
    page.window.height = 640
    page.vertical_alignment = 'center'
    page.horizontal_alignment = 'center'
    page.bgcolor = 'white'

    acc = Account()

    MainScreen(page, acc).show()


flet.run(main)
