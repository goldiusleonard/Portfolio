import requests

# Define the Florence2 server URL
florence2_url = "http://<florence2-server-ip>:<port>/api-endpoint"

# Send a request
try:
    response = requests.get(florence2_url)
    if response.status_code == 200:
        print("Connection successful!")
        print("Response:", response.json())
    else:
        print(f"Failed to connect. Status code: {response.status_code}")
        print("Error message:", response.text)
except Exception as e:
    print(f"Error occurred: {e}")
