import flet as ft
import httpx
# Run server_example.py before this file
# To run this file first run 'pip install flet httpx' in powershell

# This example constructs a flet page with text and a button which calls the fetch_message function to update the text.

# The url used in this example is a server being run on localhost, look at server.py for details.
# {user_id} lets us pass the current user to the server, this means we can use it for database queries.
user_id = 123
url = f"http://127.0.0.1:8000/test/{user_id}"

async def main(page: ft.Page):
    page.title = "Client Example"

    example_text = ft.Text("Press button to fetch message")
    response2_text = ft.Text("Response2 shows here.")

    # fetch_message uses the httpx library to send an http get request to the specified url
    # The async and await keywords function the same as javascript, letting the rest of the client run while the response is being fetched.
    async def fetch_message(e):
        # httpx.AsyncClient() creates an async http client that can be used to send multiple requests
        async with httpx.AsyncClient() as client:
            # The get request
            response = await client.get(url)
            # Showing the client can be used for multiple requests
            response2 = await client.get("http://127.0.0.1:8000/test/Hello")
            # The response is converted to json
            print(response, response2)
            data = response.json()
            data2 = response2.json()
            # The text is changed and the page is updated
            example_text.value = data["message"]
            response2_text.value = data2["message"]
            page.update()

    fetch_button = ft.Button("Fetch from Server", on_click=fetch_message)

    page.add(ft.Column([example_text, response2_text, fetch_button]))

ft.run(main)