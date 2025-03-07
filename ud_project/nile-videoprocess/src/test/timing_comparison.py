# import shutil
# import subprocess
# import time
# import httpx
# import logging
# from pathlib import Path
# from typing import Dict, Any
# from concurrent.futures import ThreadPoolExecutor
# import sys
# from ..caption import VideoCaptioner
# import json


# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class CaptionTimingComparison:
#     def __init__(self, florence_url: str, litserve_url: str = "http://localhost:8000"):
#         self.litserve_url = litserve_url
#         self.direct_captioner = VideoCaptioner(florence_url=florence_url)
#         self.litserve_endpoint = f"{litserve_url}/caption/generate_caption"

#     @staticmethod
#     def check_prerequisites():
#         """Check if required tools are installed"""
#         # Check FFmpeg
#         if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
#             raise RuntimeError(
#                 "FFmpeg/FFprobe not found. Please install FFmpeg:\n"
#                 "- On macOS: brew install ffmpeg\n"
#                 "- On Ubuntu: sudo apt-get install ffmpeg\n"
#                 "- On Windows: Download from https://ffmpeg.org/download.html"
#             )

#         # Test FFprobe functionality
#         try:
#             subprocess.run(['ffprobe', '-version'],
#                          stdout=subprocess.PIPE,
#                          stderr=subprocess.PIPE,
#                          check=True)
#         except subprocess.CalledProcessError:
#             raise RuntimeError("FFprobe installation appears broken")

#     def check_litserve_connection(self) -> bool:
#         """Check if LitServe is running"""
#         try:
#             with httpx.Client(timeout=5.0) as client:
#                 response = client.get(f"{self.litserve_url}/docs")
#                 return response.status_code == 200
#         except Exception:
#             return False

#     def test_with_litserve(self, video_path: str) -> Dict[str, Any]:
#         """Test caption generation using LitServe"""
#         start_time = time.time()

#         if not self.check_litserve_connection():
#             return {
#                 "method": "litserve",
#                 "error": "LitServe server not running. Please start it with 'litserve run'",
#                 "total_time": 0
#             }

#         try:
#             video_file = Path(video_path)
#             if not video_file.exists():
#                 raise FileNotFoundError(f"Video file not found: {video_path}")

#             with open(video_path, 'rb') as f:
#                 files = {'file': (video_file.name, f, 'video/mp4')}
#                 logger.info(f"Starting LitServe caption generation for {video_file.name}")

#                 with httpx.Client(timeout=300) as client:  # Increased timeout to 5 minutes
#                     response = client.post(self.litserve_endpoint, files=files)

#                 response.raise_for_status()
#                 result = response.json()

#                 total_time = time.time() - start_time

#                 timing_results = {
#                     "method": "litserve",
#                     "total_time": total_time,
#                     "api_response": result,
#                     "video_name": video_file.name,
#                     "video_size_mb": round(video_file.stat().st_size / (1024 * 1024), 2)
#                 }

#                 logger.info(f"LitServe caption generation completed in {total_time:.2f} seconds")
#                 return timing_results

#         except Exception as e:
#             logger.error(f"Error in LitServe test: {e}")
#             return {
#                 "method": "litserve",
#                 "error": str(e),
#                 "total_time": time.time() - start_time
#             }

#     def test_without_litserve(self, video_path: str) -> Dict[str, Any]:
#         """Test caption generation directly using VideoCaptioner"""
#         start_time = time.time()

#         try:
#             video_file = Path(video_path)
#             if not video_file.exists():
#                 raise FileNotFoundError(f"Video file not found: {video_path}")

#             logger.info(f"Starting direct caption generation for {video_file.name}")

#             with open(video_path, 'rb') as f:
#                 result = self.direct_captioner.caption_video_from_file(f)

#             total_time = time.time() - start_time

#             timing_results = {
#                 "method": "direct",
#                 "total_time": total_time,
#                 "api_response": result,
#                 "video_name": video_file.name,
#                 "video_size_mb": round(video_file.stat().st_size / (1024 * 1024), 2)
#             }

#             logger.info(f"Direct caption generation completed in {total_time:.2f} seconds")
#             return timing_results

#         except Exception as e:
#             logger.error(f"Error in direct test: {e}")
#             return {
#                 "method": "direct",
#                 "error": str(e),
#                 "total_time": time.time() - start_time
#             }

#     def run_comparison(self, video_path: str, num_runs: int = 3) -> Dict[str, Any]:
#         """Run multiple comparison tests and average the results"""
#         # Check prerequisites first
#         self.check_prerequisites()

#         litserve_results = []
#         direct_results = []

#         for i in range(num_runs):
#             logger.info(f"\nRun {i+1}/{num_runs}")

#             # Test with LitServe
#             litserve_result = self.test_with_litserve(video_path)
#             litserve_results.append(litserve_result)

#             # Test without LitServe
#             direct_result = self.test_without_litserve(video_path)
#             direct_results.append(direct_result)

#             # Wait between runs to avoid overloading
#             if i < num_runs - 1:
#                 time.sleep(2)

#         # Calculate averages (excluding error runs)
#         valid_litserve = [r for r in litserve_results if "error" not in r]
#         valid_direct = [r for r in direct_results if "error" not in r]

#         comparison = {
#             "video_info": {
#                 "name": Path(video_path).name,
#                 "size_mb": round(Path(video_path).stat().st_size / (1024 * 1024), 2)
#             },
#             "litserve": {
#                 "average_time": sum(r["total_time"] for r in valid_litserve) / len(valid_litserve) if valid_litserve else 0,
#                 "min_time": min((r["total_time"] for r in valid_litserve), default=0),
#                 "max_time": max((r["total_time"] for r in valid_litserve), default=0),
#                 "successful_runs": len(valid_litserve),
#                 "failed_runs": len(litserve_results) - len(valid_litserve),
#                 "errors": [r.get("error") for r in litserve_results if "error" in r],
#                 "individual_runs": litserve_results
#             },
#             "direct": {
#                 "average_time": sum(r["total_time"] for r in valid_direct) / len(valid_direct) if valid_direct else 0,
#                 "min_time": min((r["total_time"] for r in valid_direct), default=0),
#                 "max_time": max((r["total_time"] for r in valid_direct), default=0),
#                 "successful_runs": len(valid_direct),
#                 "failed_runs": len(direct_results) - len(valid_direct),
#                 "errors": [r.get("error") for r in direct_results if "error" in r],
#                 "individual_runs": direct_results
#             },
#             "num_runs": num_runs
#         }

#         return comparison

# def main():
#     """Main function to run comparison tests"""
#     if len(sys.argv) < 3:
#         print("Usage: python timing_comparison.py <florence_url> <video_path> [num_runs]")
#         sys.exit(1)

#     florence_url = sys.argv[1]
#     video_path = sys.argv[2]
#     num_runs = int(sys.argv[3]) if len(sys.argv) > 3 else 3

#     try:
#         comparison = CaptionTimingComparison(florence_url=florence_url)
#         results = comparison.run_comparison(video_path, num_runs)

#         # Print formatted results
#         print("\nTiming Comparison Results:")
#         print("=" * 60)
#         print(f"Video: {results['video_info']['name']}")
#         print(f"Size: {results['video_info']['size_mb']} MB")
#         print(f"Number of test runs: {results['num_runs']}")

#         print("\nLitServe Results:")
#         print("-" * 30)
#         if results['litserve']['successful_runs'] > 0:
#             print(f"Successful runs: {results['litserve']['successful_runs']}/{results['num_runs']}")
#             print(f"Average Time: {results['litserve']['average_time']:.2f} seconds")
#             print(f"Min Time: {results['litserve']['min_time']:.2f} seconds")
#             print(f"Max Time: {results['litserve']['max_time']:.2f} seconds")
#         if results['litserve']['errors']:
#             print("Errors encountered:")
#             for error in results['litserve']['errors']:
#                 print(f"- {error}")

#         print("\nDirect Results:")
#         print("-" * 30)
#         if results['direct']['successful_runs'] > 0:
#             print(f"Successful runs: {results['direct']['successful_runs']}/{results['num_runs']}")
#             print(f"Average Time: {results['direct']['average_time']:.2f} seconds")
#             print(f"Min Time: {results['direct']['min_time']:.2f} seconds")
#             print(f"Max Time: {results['direct']['max_time']:.2f} seconds")
#         if results['direct']['errors']:
#             print("Errors encountered:")
#             for error in results['direct']['errors']:
#                 print(f"- {error}")

#         # Calculate performance difference only if both have successful runs
#         if results['litserve']['successful_runs'] > 0 and results['direct']['successful_runs'] > 0:
#             time_diff = results['litserve']['average_time'] - results['direct']['average_time']
#             percent_diff = (time_diff / results['direct']['average_time']) * 100
#             print(f"\nPerformance Difference:")
#             print(f"LitServe is {abs(percent_diff):.1f}% {'slower' if percent_diff > 0 else 'faster'} than direct execution")

#         # Save detailed results to file
#         output_file = f"timing_comparison_{Path(video_path).stem}.json"
#         with open(output_file, 'w') as f:
#             json.dump(results, f, indent=2)
#         print(f"\nDetailed results saved to: {output_file}")

#     except Exception as e:
#         print(f"\nError running comparison: {e}")
#         sys.exit(1)

# if __name__ == "__main__":
#     main()


import time
import httpx
import logging
from pathlib import Path
from typing import Dict, Any, List
import sys
from ..caption import VideoCaptioner
import json
import hdbscan  # New import
import numpy as np  # For potential HDBSCAN usage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExtendedTimingComparison:
    def __init__(self, florence_url: str, litserve_url: str = "http://localhost:8000"):
        self.litserve_url = litserve_url
        self.direct_captioner = VideoCaptioner(florence_url=florence_url)
        self.litserve_endpoint = f"{litserve_url}/caption/generate_caption"
        self.florence_url = florence_url

    def check_litserve_connection(self) -> bool:
        """Check if LitServe is running"""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.litserve_url}/docs")
                return response.status_code == 200
        except Exception:
            return False

    def test_with_litserve(self, video_path: str) -> Dict[str, Any]:
        """Test caption generation using LitServe"""
        start_time = time.time()

        if not self.check_litserve_connection():
            return {
                "method": "litserve",
                "error": "LitServe server not running. Please start it with 'litserve run'",
                "total_time": 0,
            }

        try:
            video_file = Path(video_path)
            if not video_file.exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")

            with open(video_path, "rb") as f:
                files = {"file": (video_file.name, f, "video/mp4")}
                logger.info(
                    f"Starting LitServe caption generation for {video_file.name}"
                )

                with httpx.Client(
                    timeout=300
                ) as client:  # Increased timeout to 5 minutes
                    response = client.post(self.litserve_endpoint, files=files)

                response.raise_for_status()
                result = response.json()

                total_time = time.time() - start_time

                timing_results = {
                    "method": "litserve",
                    "total_time": total_time,
                    "api_response": result,
                    "video_name": video_file.name,
                    "video_size_mb": round(
                        video_file.stat().st_size / (1024 * 1024), 2
                    ),
                }

                logger.info(
                    f"LitServe caption generation completed in {total_time:.2f} seconds"
                )
                return timing_results

        except Exception as e:
            logger.error(f"Error in LitServe test: {e}")
            return {
                "method": "litserve",
                "error": str(e),
                "total_time": time.time() - start_time,
            }

    def test_without_litserve(self, video_path: str) -> Dict[str, Any]:
        """Test caption generation directly using VideoCaptioner"""
        start_time = time.time()

        try:
            video_file = Path(video_path)
            if not video_file.exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")

            logger.info(f"Starting direct caption generation for {video_file.name}")

            with open(video_path, "rb") as f:
                result = self.direct_captioner.caption_video_from_file(f)

            total_time = time.time() - start_time

            timing_results = {
                "method": "direct",
                "total_time": total_time,
                "api_response": result,
                "video_name": video_file.name,
                "video_size_mb": round(video_file.stat().st_size / (1024 * 1024), 2),
            }

            logger.info(
                f"Direct caption generation completed in {total_time:.2f} seconds"
            )
            return timing_results

        except Exception as e:
            logger.error(f"Error in direct test: {e}")
            return {
                "method": "direct",
                "error": str(e),
                "total_time": time.time() - start_time,
            }

    def measure_florence_time(self, method: str, input_data):
        """Measure Florence model processing time"""
        start_time = time.time()
        try:
            # Placeholder for actual Florence processing
            # Replace with actual Florence model inference logic
            time.sleep(0.1)  # Simulated processing time
            florence_time = time.time() - start_time
            return florence_time
        except Exception as e:
            logger.error(f"Florence timing error: {e}")
            return None

    def measure_hdbscan_time(self, data):
        """Measure HDBSCAN clustering time"""
        start_time = time.time()
        try:
            # Generate sample data if none provided
            if data is None:
                data = np.random.rand(100, 10)

            clusterer = hdbscan.HDBSCAN(min_cluster_size=10)
            clusterer.fit(data)
            hdbscan_time = time.time() - start_time
            return hdbscan_time
        except Exception as e:
            logger.error(f"HDBSCAN timing error: {e}")
            return None

    def run_detailed_comparison(self, video_path: str, num_runs: int = 3):
        """Run comprehensive timing comparison"""
        results: Dict[str, Dict[str, List[float]]] = {
            "litserve": {"florence_times": [], "hdbscan_times": [], "total_times": []},
            "direct": {"florence_times": [], "hdbscan_times": [], "total_times": []},
        }

        for _ in range(num_runs):
            # LitServe method
            litserve_start = time.time()
            litserve_result = self.test_with_litserve(video_path)
            litserve_total_time = time.time() - litserve_start

            # Direct method
            direct_start = time.time()
            direct_result = self.test_without_litserve(video_path)
            direct_total_time = time.time() - direct_start

            # Measure Florence and HDBSCAN times
            litserve_florence_time = self.measure_florence_time(
                "litserve", litserve_result
            )
            direct_florence_time = self.measure_florence_time("direct", direct_result)

            # Generate sample data for HDBSCAN
            sample_data = np.random.rand(100, 10)
            litserve_hdbscan_time = self.measure_hdbscan_time(sample_data)
            direct_hdbscan_time = self.measure_hdbscan_time(sample_data)

            # Store results
            results["litserve"]["florence_times"].append(litserve_florence_time)
            results["litserve"]["hdbscan_times"].append(litserve_hdbscan_time)
            results["litserve"]["total_times"].append(litserve_total_time)

            results["direct"]["florence_times"].append(direct_florence_time)
            results["direct"]["hdbscan_times"].append(direct_hdbscan_time)
            results["direct"]["total_times"].append(direct_total_time)

        # Calculate statistics
        def calculate_stats(times):
            valid_times = [t for t in times if t is not None]
            return {
                "average": np.mean(valid_times) if valid_times else None,
                "min": np.min(valid_times) if valid_times else None,
                "max": np.max(valid_times) if valid_times else None,
            }

        return {
            "litserve": {
                "florence": calculate_stats(results["litserve"]["florence_times"]),
                "hdbscan": calculate_stats(results["litserve"]["hdbscan_times"]),
                "total": calculate_stats(results["litserve"]["total_times"]),
            },
            "direct": {
                "florence": calculate_stats(results["direct"]["florence_times"]),
                "hdbscan": calculate_stats(results["direct"]["hdbscan_times"]),
                "total": calculate_stats(results["direct"]["total_times"]),
            },
        }


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: python timing_comparison.py <florence_url> <video_path> [num_runs]"
        )
        sys.exit(1)

    florence_url = sys.argv[1]
    video_path = sys.argv[2]
    num_runs = int(sys.argv[3]) if len(sys.argv) > 3 else 3

    comparison = ExtendedTimingComparison(florence_url=florence_url)
    results = comparison.run_detailed_comparison(video_path, num_runs)

    # Print results
    print("\nDetailed Timing Results:")
    for method in ["litserve", "direct"]:
        print(f"\n{method.capitalize()} Method:")
        print(f"Florence Timing - Avg: {results[method]['florence']['average']:.4f}s")
        print(f"HDBSCAN Timing  - Avg: {results[method]['hdbscan']['average']:.4f}s")
        print(f"Total Timing    - Avg: {results[method]['total']['average']:.4f}s")

    # Save detailed results
    with open("detailed_timing_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
