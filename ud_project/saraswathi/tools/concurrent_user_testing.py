import time
from multiprocessing.pool import Pool

import requests

# Define the API endpoint
api_url = "http://localhost:8000/streaming/GraphUpsSummary/d3"


# Define a function to hit the API and record execution time
def hit_api(user_id):
    start_time = time.time()
    try:
        response = requests.post(
            api_url,
            json=[
                "ada_banks_data_asset.report_cross_selling_performance_product_type_new",
                "label1",
                " The user's primary intent is to analyze the product penetration rate based on the 'Income Level' dimension of the 'Customer Financial Product Usage Analysis' table. They have implicitly requested to view or examine the data grouped by income levels. The user is currently awaiting the delivery of a customized data asset visualization that focuses on the specified income range to gain insights into the product usage trends among different income groups.",
                {},
                ["income_level"],
                '"starhub_001"',
                '"goldius.leo@userdata.tech"',
                '"6cacaafc-c85c-4dd0-b9f3-c323f458b60a"',
            ],
            stream=True,
            verify=False,
        )
        for chunk in response.iter_content(10000000000):
            pass
        execution_time = time.time() - start_time
        return (execution_time, f"User {user_id}: {response.status_code}")
    except requests.exceptions.RequestException as e:
        execution_time = time.time() - start_time
        return (execution_time, f"User {user_id}: Request failed - {e}")


#  Main function to run concurrent API calls
def run_concurrent_users(user_count):
    total_execution_time = 0

    callbacks = []

    with Pool() as mp_pool:
        for runner_id in range(user_count):
            callbacks.append(
                mp_pool.apply_async(
                    hit_api,
                    [runner_id],
                ),
            )

        for cb in callbacks:
            cb_result = cb.get()
            execution_time, result = cb_result
            total_execution_time += execution_time
            print(result)

        # Calculate and print the average execution time
        average_execution_time = total_execution_time / user_count
        print(
            f"Average execution time per request: {average_execution_time:.2f} seconds",
        )


if __name__ == "__main__":
    start_time = time.time()

    for concurrent_user in range(1, 11):
        # Run the test with n concurrent users
        print(f"Running {concurrent_user} concurrent users")
        run_concurrent_users(concurrent_user)

        end_time = time.time()
        print(f"Total execution time: {end_time - start_time:.2f} seconds")
