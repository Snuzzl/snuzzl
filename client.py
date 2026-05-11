import inspect
import flet as ft
from app.ui.ui_metrics import MetricManagerApp
from app.ui.ui_social import SocialManagerApp
from app.ui.ui_task_manager import SnuzzlTaskApp
from app.ui.ui_login import MainScreen
from app.ui.ui_account import Summary
from app.ui.ui_challenges import RewardsChallengesScreen
from app.ui.ui_notifications import NotificationManagerApp


class ID:
    def __init__(self):
        self.user_id = None


class Menu(ft.Column):
    def __init__(self, task_menu, metric_menu, social_menu, account_menu, notification_menu, rewards_challenges_menu):
        super().__init__()
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self.controls = [
            ft.Text("Main Menu", size=30, weight=ft.FontWeight.BOLD),
            ft.Button("Open Account Summary", on_click=account_menu),
            ft.Button("Open Tasks", on_click=task_menu),
            ft.Button("Open Metrics", on_click=metric_menu),
            ft.Button("Open Social", on_click=social_menu),
            ft.Button("Open Notifications", on_click=notification_menu),
            ft.Button("Open Rewards and Challenges", on_click=rewards_challenges_menu),
        ]


async def main(page: ft.Page):
    page.title = "Snuzzl App"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE

    id = ID()

    async def menu(e=None):
        page.controls.clear()
        page.add(Menu(task_menu, metric_menu, social_menu, account_menu, notification_menu, rewards_challenges_menu))
        page.update()

    menu_button = ft.Button("← Back to Menu", on_click=menu)
    async def login_menu():
        page.controls.clear()
        screen = MainScreen(id, page, on_login_success=menu)
        page.add(screen)
        page.update()
        screen.show_menu()

    async def account_menu(e=None):
        page.controls.clear()
        app = Summary(id, page, on_logout=login_menu)
        page.add(ft.Column([menu_button, app]))
        page.update()
        # Load account info when page loads
        await app.load_account()

    async def task_menu(e=None):
        page.controls.clear()
        app = SnuzzlTaskApp(id.user_id)
        page.add(ft.Column([menu_button, app]))
        page.update()
        # Load existing tasks when page loads.
        catalog_tile = app.controls[4]  # CatalogBrowser is after title, divider, form, divider.
        load_catalog = getattr(catalog_tile, "load_catalog", None)
        if callable(load_catalog):
            maybe_result = load_catalog()
            if inspect.isawaitable(maybe_result):
                await maybe_result
        await app.my_tasks.load_tasks()

    async def metric_menu(e=None):
        page.controls.clear()
        app = MetricManagerApp(id.user_id)
        page.add(ft.Column([menu_button, app]))
        page.update()
        # Load existing metrics when page loads
        await app.load_metrics()

    async def social_menu(e=None):
        page.controls.clear()
        app = SocialManagerApp(id.user_id)
        page.add(ft.Column([menu_button, app]))
        page.update()
        # Load friends when page loads
        await app.load_friends()

    async def notification_menu(e=None):
        page.controls.clear()
        app = NotificationManagerApp(id.user_id)
        page.add(ft.Column([menu_button, app]))
        page.update()

    async def rewards_challenges_menu(e=None):
        page.controls.clear()
        app = RewardsChallengesScreen(
            id.user_id,
            on_back=menu,
            on_open_tasks=lambda chall_id=None: page.run_task(task_menu),
        )
        page.add(ft.Column([menu_button, app]))
        page.update()
        await app.load_all_data()

    # Load login menu on app start
    await login_menu()

if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550)
