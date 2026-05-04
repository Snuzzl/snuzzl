import flet as ft
from app.ui.ui_login import Account
from app.ui.ui_rewards import RewardsChallenges


def main(page: ft.Page):
    page.title = "Snuzzl App"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE

    acc = Account()
    RewardsChallenges(page, acc).show()


ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550)
