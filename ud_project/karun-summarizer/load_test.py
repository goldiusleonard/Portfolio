import aiohttp
import asyncio
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import psutil
import time
import uuid
from dotenv import load_dotenv

from datetime import datetime
from langfuse import Langfuse
from typing import Dict, List, Tuple

# Load environment variables
load_dotenv()

# Initialize Langfuse
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST"),
)


class ResourceMonitor:
    def __init__(self, interval: float = 0.1):
        self.interval = interval
        self.cpu_percentages = []
        self.ram_usages = []
        self.process = psutil.Process()
        self.baseline_cpu = 0
        self.baseline_ram = 0

    def measure_baseline(self, duration: float = 5.0):
        samples_cpu, samples_ram = [], []
        end_time = time.time() + duration

        while time.time() < end_time:
            samples_cpu.append(psutil.cpu_percent(interval=0.1))
            samples_ram.append(self.process.memory_info().rss / (1024 * 1024))
            time.sleep(0.1)

        self.baseline_cpu = np.mean(samples_cpu)
        self.baseline_ram = np.mean(samples_ram)
        return self.baseline_cpu, self.baseline_ram

    async def start_monitoring(self):
        self.cpu_percentages, self.ram_usages = [], []
        while True:
            self.cpu_percentages.append(psutil.cpu_percent(interval=0.1))
            self.ram_usages.append(self.process.memory_info().rss / (1024 * 1024))
            await asyncio.sleep(self.interval)

    def stop_monitoring(self) -> Dict[str, float]:
        peak_cpu = max(self.cpu_percentages)
        peak_ram = max(self.ram_usages)
        return {
            "baseline_cpu": round(self.baseline_cpu, 3),
            "baseline_ram": round(self.baseline_ram, 3),
            "peak_cpu": round(peak_cpu, 3),
            "peak_ram": round(peak_ram, 3),
            "delta_cpu": round(peak_cpu - self.baseline_cpu, 3),
            "delta_ram": round(peak_ram - self.baseline_ram, 3),
        }


class LoadTester:
    def __init__(self, base_url: str = "http://18.143.205.116:8003"):
        self.base_url = base_url
        self.monitor = ResourceMonitor()

    async def make_request(
        self, session: aiohttp.ClientSession, text: str
    ) -> Tuple[float, bool, int, int]:
        start_time = time.time()
        input_tokens = len(text.split())
        trace_id = str(uuid.uuid4())

        try:
            # Create Langfuse trace
            trace = langfuse.trace(
                id=trace_id,
                name="karun_summary_request",
                metadata={"input_tokens": input_tokens, "concurrency_test": True},
            )

            # Create generation span
            generation = trace.generation(
                name="summary_generation", model="karun-agent", input={"text": text}
            )

            async with session.post(
                f"{self.base_url}/summary", json={"text": text}, timeout=30
            ) as response:
                result = await response.json()
                duration = time.time() - start_time
                output_tokens = len(result.get("summary", "").split())
                is_successful = response.status == 200

                # Update generation with results
                generation.end(
                    output=result,
                    metadata={
                        "duration_seconds": duration,
                        "output_tokens": output_tokens,
                        "http_status": response.status,
                    },
                )

                # Score the request
                trace.score(
                    name="request_success",
                    value=1.0 if is_successful else 0.0,
                    metadata={"duration": duration, "status_code": response.status},
                )

                # Score latency
                trace.score(
                    name="latency", value=duration, metadata={"unit": "seconds"}
                )

                return duration, is_successful, input_tokens, output_tokens

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

            if "generation" in locals():
                generation.end(error=error_msg, metadata={"duration_seconds": duration})

            if "trace" in locals():
                trace.score(
                    name="request_success",
                    value=0.0,
                    metadata={"error": error_msg, "duration": duration},
                )

            print(f"Request error: {error_msg}")
            return duration, False, input_tokens, 0

    async def run_concurrent_requests(self, concurrency: int, sample_text: str) -> Dict:
        print("\nMeasuring baseline resource usage...")
        baseline_cpu, baseline_ram = self.monitor.measure_baseline()
        print(f"Baseline: CPU {baseline_cpu:.3f}%, RAM {baseline_ram:.3f}MB")

        # Create a Langfuse trace for the concurrent test batch
        batch_trace = langfuse.trace(
            name="concurrent_test_batch",
            metadata={
                "concurrency": concurrency,
                "baseline_cpu": baseline_cpu,
                "baseline_ram": baseline_ram,
            },
        )

        async with aiohttp.ClientSession() as session:
            monitor_task = asyncio.create_task(self.monitor.start_monitoring())
            tasks = [
                self.make_request(session, sample_text) for _ in range(concurrency)
            ]

            start_time = time.time()
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time

            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass

            durations, successful, input_tokens, output_tokens = zip(*results)

            stats = {
                "concurrency": concurrency,
                "total_requests": len(results),
                "successful_requests": sum(successful),
                "failed_requests": len(results) - sum(successful),
                "total_time_s": round(total_time, 3),
                "avg_response_time_s": round(np.mean(durations), 3),
                "min_response_time_s": round(min(durations), 3),
                "max_response_time_s": round(max(durations), 3),
                "requests_per_second": round(len(results) / total_time, 3),
                "input_tokens_min": min(input_tokens),
                "input_tokens_max": max(input_tokens),
                "input_tokens_avg": round(np.mean(input_tokens), 3),
                "output_tokens_min": min(output_tokens),
                "output_tokens_max": max(output_tokens),
                "output_tokens_avg": round(np.mean(output_tokens), 3),
            }
            stats.update(self.monitor.stop_monitoring())

            # Update batch trace with results
            batch_trace.update(
                metadata={"stats": stats, "completion_time": datetime.now().isoformat()}
            )

            # Score the batch
            batch_trace.score(
                name="batch_success_rate",
                value=stats["successful_requests"] / stats["total_requests"],
                metadata={"concurrency": concurrency},
            )

            return stats


def plot_results(results: List[Dict], output_dir: str = "output"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    df = pd.DataFrame(results)

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

    # Plot response times
    ax1.plot(df["concurrency"], df["avg_response_time_s"], "b-o", label="Average")
    ax1.plot(df["concurrency"], df["max_response_time_s"], "r-o", label="Max")
    ax1.set_xlabel("Concurrency"), ax1.set_ylabel("Response Time (seconds)")
    ax1.set_title("Response Times"), ax1.legend(), ax1.grid(True)

    # Plot throughput
    ax2.plot(df["concurrency"], df["requests_per_second"], "g-o")
    ax2.set_xlabel("Concurrency"), ax2.set_ylabel("Requests per Second (req/s)")
    ax2.set_title("Throughput"), ax2.grid(True)

    # Plot resource usage deltas
    ax3.plot(df["concurrency"], df["delta_cpu"], "b-o")
    ax3.set_xlabel("Concurrency"), ax3.set_ylabel("CPU Usage Increase (%)")
    ax3.set_title("CPU Usage Delta"), ax3.grid(True)

    ax4.plot(df["concurrency"], df["delta_ram"], "b-o")
    ax4.set_xlabel("Concurrency"), ax4.set_ylabel("Memory Usage Increase (MB)")
    ax4.set_title("Memory Usage Delta"), ax4.grid(True)

    plt.tight_layout()

    # Save results
    output_path = os.path.join(output_dir, f"load_test_results_{timestamp}.png")
    csv_path = os.path.join(output_dir, f"load_test_results_{timestamp}.csv")
    plt.savefig(output_path)
    df.to_csv(csv_path, index=False)
    print(f"\nPlot saved to: {output_path}")
    print(f"Raw data saved to: {csv_path}")
    plt.show()


async def main():
    sample_text = "Meta has unveiled its latest AI model called Llama 3, which can process both text and images."
    tester = LoadTester("http://18.143.205.116:8003")
    results = []

    print("\nDetailed Performance Metrics:")
    print("-" * 80)
    print(f"{'Concurrency':<12} {'Time (s)':<12} {'RAM (MB)':<12} {'CPU (%)':<12}")
    print("-" * 80)

    for concurrency in [1, 10, 100]:
        result = await tester.run_concurrent_requests(concurrency, sample_text)
        results.append(result)

        # Calculate and display metrics
        print(
            f"{concurrency:<12} "
            f"{result['avg_response_time_s']:.3f}       "
            f"{result['delta_ram']:.3f}       "
            f"{result['delta_cpu']:.3f}"
        )

        # Add detailed logging to Langfuse
        langfuse.trace(
            name="performance_metrics",
            metadata={
                "concurrency": concurrency,
                "avg_time_seconds": round(result["avg_response_time_s"], 3),
                "ram_usage_mb": round(result["delta_ram"], 3),
                "cpu_usage_percent": round(result["delta_cpu"], 3),
            },
        )

        await asyncio.sleep(10)  # Cool-down period

    print("-" * 80)
    print("\nGenerating performance plots...")
    plot_results(results)


if __name__ == "__main__":
    asyncio.run(main())
