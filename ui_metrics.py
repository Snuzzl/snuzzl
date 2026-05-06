import flet as ft
from metric_manager import MetricManager

class Metrics:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc
        self.metric_manager = MetricManager()

    def show(self):
        self.page.clean()
        metrics = [
            "Productivity",
            "Fun",
            "Rest",
            "Emotional Health",
            "Physical Health",
            "Sleep Length",
            "Sleep Quality"
        ]

        rows = []
        for m in metrics:
            rows.append(
                ft.Row(
                    [
                        ft.Container(
                            ft.Text(m, color='black', size=15, weight="bold"),
                            alignment=ft.alignment.Alignment(-1, 0),
                            width=150
                        ),
                        ft.Container(
                            ft.Text("Score", color='black', size=15),
                            alignment=ft.alignment.Alignment(0, 0),
                            width=80
                        ),
                        ft.Container(
                            ft.Row(
                                [
                                    ft.Button("Update"),
                                    ft.Button("Details")
                                ],
                                spacing=10
                            ),
                            alignment=ft.alignment.Alignment(1, 0),
                            width=200
                        )
                    ],
                    width=430,
                    alignment="spaceBetween"
                )
        )
        self.page.add(
            ft.Text("Your Metrics",
                    color='black', size=25, weight='bold'),
            *rows
        )