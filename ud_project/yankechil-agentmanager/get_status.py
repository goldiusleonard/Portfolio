import requests


def get_status():
    try:
        response = requests.get("http://localhost:8000/status")
        response.raise_for_status()  # Will raise an exception for 4xx/5xx status codes
        data = response.json()
        print("Current status: ", data["status"])
    except requests.exceptions.RequestException as e:
        print("Error fetching status: ", e)


# To fetch the status
get_status()
