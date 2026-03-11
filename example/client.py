import flet as ft
import httpx
# To run this file first run 'pip install flet httpx' in powershell

# This example constructs a flet page with text and a button which calls the fetch_message function.

# fetch_message uses the httpx library to send an http get request to the specified url, it converts the response to json and updates the text.
# The async and await keywords function the same as javascript, letting the rest of the client run while the response is being fetched.
# httpx.AsyncClient() creates an async http client that can be shared between tasks (mutliple buttons can use the same client).

# The url used in this example is a server being run on localhost, look at server.py for details.
url = "http://127.0.0.1:8000/message"

async def main(page: ft.Page):
    page.title = "Client Example"

    message_text = ft.Text("Press button to fetch message")

    async def fetch_message(e):
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            data = response.json()
            message_text.value = data["message"]
            page.update()

    fetch_button = ft.Button("Fetch from Server", on_click=fetch_message)

    page.add(ft.Column([message_text, fetch_button]))

ft.run(main)