# import requests

# # Prompt the user to enter the task ID
# task_id = input("Please enter the task ID: ")

# # Correct URL formatting
# url = f"http://0.0.0.0:8001/yankechil_processor/task_status/{task_id}"

# # Sending the GET request
# response = requests.get(url)

# # Print the response in JSON format
# if response.status_code == 200:
#     print(response.json())
# else:
#     print(f"Error: Unable to fetch task status. Status code: {response.status_code}")



import requests

# Prompt the user to enter the task ID
task_id = input("Please enter the task ID: ")

# Correct URL formatting to match your FastAPI endpoint
url = f"http://0.0.0.0:8001/task/{task_id}/status"

# Sending the GET request
response = requests.get(url)

# Print the response in JSON format
if response.status_code == 200:
    data = response.json()
    if data['status'] == 'not found':
        print(f"Task with ID {task_id} not found.")
    else:
        print(f"Task ID: {data['task_id']}, Status: {data['status']}")
else:
    print(f"Error: Unable to fetch task status. Status code: {response.status_code}")

