# Install & Run
!!! note
    All commands must be run from a terminal with the current working directory set to the /snuzzl folder.

## Installation
Install depenencies using pip:
```console
pip install -r docs/requirements.txt
```

## Running the App
This app uses a client-server architecture.  
There is currently no server being hosted so we have provided a way to run the server locally.

### Run using start.py
This runs both the server and client, allowing the app to run from one command.
```console
python start.py
```

### Run manually
To run the app manually you have to use two terminals.  
Terminal 1 - start server:
```console
uvicorn server:app
```

Terminal 2 - start client:
```console
python client.py
```