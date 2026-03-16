from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.concurrency import run_in_threadpool
# To run ths file:
    # First run 'pip install "fastapi[standard]" ' in powershell
    # In your VSCode terminal navigate to the folder containing this file (../snuzzl)
    # Run 'uvicorn server_example:example_app' in the terminal, this runs the app on localhost

# asyncontextmanager is a decorator used to create the 'on entry' and 'on exit' conditions for an async block within a single function
@asynccontextmanager
# lifespan is required for a FastAPI app, it defines what happens during its lifespan, when it is entered and exited.
async def lifespan(example_app: FastAPI):
    # Code that executes when the app is entered
    print("App Started.")
    # Yield provides the resource used in 'async with', required as it also splits the 'on enter' and 'on exit' blocks
    yield 
    # Code that executes when the app is exited
    print("App Exited.")

# Creating a fastAPI instance and giving it the lifespan function we defined
example_app = FastAPI(lifespan=lifespan)

def get_message(user_id):
    return f"Hi {user_id}!" 

# This is how we define an endpoint for http requests coming from the client
# When client_example.py runs 'client.get(url)' on line 25, this defines what happens on the server
@example_app.get("/test/{user_id}")
async def test_message(user_id):
    # run_in_threadpool lets us run functions without the async keyword in a seperate thread, freeing test_message up to be used again
    message = await run_in_threadpool(get_message, user_id)
    # return the data in dictionary format so it can be treated as json
    return {"message": message}

# To reach this endpoint visit http://127.0.0.1:8000/hello
@example_app.get("/hello")
def hello():
    return "Hello!"