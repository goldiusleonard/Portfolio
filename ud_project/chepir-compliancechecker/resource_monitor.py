import json
import psutil
import requests
import time
import os

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, Tuple
from utils import setup_logging

# Initialize logger
logger = setup_logging("resource_monitor")


def get_system_usage() -> Tuple[float, float]:
    """Get current memory and CPU usage"""
    memory = psutil.Process().memory_info().rss / (1024 * 1024)  # Convert to MB
    cpu = psutil.cpu_percent()
    return memory, cpu


def make_api_request(endpoint: str, payload: Dict) -> Dict:
    """Make a single API request"""
    try:
        response = requests.post(
            f"http://localhost:8050/{endpoint}", json=payload, timeout=30
        )
        response.raise_for_status()
        return {
            "status_code": response.status_code,
            "processing_time": response.elapsed.total_seconds(),
            "violations_found": response.json().get("violations_found", False),
        }
    except Exception as e:
        logger.error(f"API request failed: {str(e)}")
        return {"status_code": getattr(e.response, "status_code", 500), "error": str(e)}


def make_concurrent_requests(num_users: int, endpoint: str = "direct_analysis"):
    """Make concurrent API requests"""
    sample_texts = [
        "He is a racist",
        "She stole money",
        "They are planning violence",
        "This is normal content",
        "Weather is nice today",
    ]

    payloads = [{"text": text} for text in sample_texts] * (
        num_users // len(sample_texts) + 1
    )
    payloads = payloads[:num_users]  # Trim to exact number needed

    results = []
    with ThreadPoolExecutor(max_workers=num_users) as executor:
        future_to_payload = {
            executor.submit(make_api_request, endpoint, payload): payload
            for payload in payloads
        }

        for future in future_to_payload:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                results.append({"error": str(e)})

    return results


def run_load_test(num_users: int = 5, duration: int = 60):
    """Run load test for specified duration"""
    logger.info(
        f"Starting load test with {num_users} concurrent users for {duration} seconds"
    )

    # Initial resource usage
    initial_memory, initial_cpu = get_system_usage()
    logger.info(f"Initial Memory: {initial_memory:.2f}MB, CPU: {initial_cpu}%")

    start_time = time.time()
    results = []

    try:
        while time.time() - start_time < duration:
            batch_results = make_concurrent_requests(num_users)
            results.extend(batch_results)
            time.sleep(1)  # Prevent overwhelming the server

    except KeyboardInterrupt:
        logger.info("Test interrupted by user")

    # Final resource usage
    final_memory, final_cpu = get_system_usage()
    elapsed_time = time.time() - start_time

    # Calculate statistics
    successful_requests = sum(1 for r in results if r.get("status_code") == 200)
    avg_processing_time = (
        sum(r.get("processing_time", 0) for r in results if r.get("processing_time"))
        / successful_requests
        if successful_requests
        else 0
    )

    # Generate report
    report = {
        "test_summary": {
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "duration": f"{elapsed_time:.2f}s",
            "concurrent_users": num_users,
            "total_requests": len(results),
            "successful_requests": successful_requests,
            "average_processing_time": f"{avg_processing_time:.2f}s",
        },
        "resource_usage": {
            "initial_memory_mb": f"{initial_memory:.2f}",
            "final_memory_mb": f"{final_memory:.2f}",
            "memory_difference_mb": f"{final_memory - initial_memory:.2f}",
            "initial_cpu_percent": f"{initial_cpu:.2f}",
            "final_cpu_percent": f"{final_cpu:.2f}",
            "cpu_difference_percent": f"{final_cpu - initial_cpu:.2f}",
        },
        "request_results": results,
    }

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"output/load_test_report_{timestamp}.json"
    os.makedirs("output", exist_ok=True)

    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Load test report saved to: {report_file}")
    return report


def run_concurrency_tests():
    """Run multiple concurrency tests and generate combined report"""
    scenarios = [
        {"users": 1, "duration": 120, "name": "Single User"},  # 2 minutes
        {"users": 10, "duration": 300, "name": "Medium Load"},  # 5 minutes
        {"users": 50, "duration": 600, "name": "High Load"},  # 10 minutes
    ]

    all_results = {}

    for scenario in scenarios:
        print(f"\nStarting {scenario['name']} Test")
        print(f"Concurrent Users: {scenario['users']}")
        print(f"Duration: {scenario['duration']} seconds")
        print("-" * 50)

        # Run test
        report = run_load_test(
            num_users=scenario["users"], duration=scenario["duration"]
        )

        all_results[scenario["name"]] = report

        # Print scenario summary
        print(f"\n{scenario['name']} Results:")
        print(f"Successful Requests: {report['test_summary']['successful_requests']}")
        print(
            f"Average Processing Time: {report['test_summary']['average_processing_time']}"
        )
        print(f"Memory Usage: {report['resource_usage']['memory_difference_mb']} MB")
        print(f"CPU Usage: {report['resource_usage']['cpu_difference_percent']}%")

        # Brief pause between tests
        if scenario != scenarios[-1]:
            print("\nWaiting 10 seconds before next test...")
            time.sleep(10)

    # Save combined report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    combined_report_file = f"output/concurrency_test_report_{timestamp}.json"

    with open(combined_report_file, "w") as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Combined test report saved to: {combined_report_file}")
    return all_results


if __name__ == "__main__":
    # Run concurrency tests instead of single test
    results = run_concurrency_tests()
