import subprocess
import time

# Start server
server = subprocess.Popen(["uvicorn", "server:app"])

# Give the server a moment to start
time.sleep(5)

# Start client
client = subprocess.Popen(["python", "client.py"])

server.wait()
client.wait()