import ast
import csv
import json
import os
import requests
import time
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from typing import List
from utils import (
    setup_logging,
    validate_env_variables,
    validate_embedding_config,
    get_service_timeout,
)

# Initialize logger
logger = setup_logging("compliance_checker")


@dataclass
class ViolationFound:
    """Represents a detected law violation."""

    category: str
    section_name: str
    description: str
    reference_text: str


class ComplianceChecker:
    """Main compliance checking engine using vector search and LLM analysis."""

    def __init__(self):
        load_dotenv()
        self._validate_and_init_config()
        self._init_qdrant_client()
        self._setup_collections()

    def _validate_and_init_config(self):
        """Initialize and validate configuration"""
        if not validate_embedding_config():
            raise EnvironmentError("Missing embedding configuration")

        # Initialize embedding configuration
        self.embedding_url = os.getenv("EMBEDDING_MODEL_URL")
        self.embedding_model = os.getenv("EMBEDDING_MODEL_NAME")
        self.embedding_timeout = get_service_timeout("EMBEDDING")

        # Initialize LLM configuration
        self.llm_url = os.getenv("LLM_BASE_URL")
        self.llm_key = os.getenv("LLM_API_KEY")
        self.llm_model = os.getenv("MODEL")
        self.llm_timeout = get_service_timeout("LLM")

        # Initialize Qdrant configuration
        self.qdrant_url = os.getenv("QDRANT_HOST")
        self.qdrant_key = os.getenv("QDRANT_API_KEY")
        self.qdrant_timeout = get_service_timeout("QDRANT")

    def _init_qdrant_client(self):
        """Initialize Qdrant vector database client."""
        self.qdrant = QdrantClient(
            url=self.qdrant_url, api_key=self.qdrant_key, timeout=self.qdrant_timeout
        )

    def _setup_collections(self):
        """Define collection mappings and order."""
        self.collections = {
            # 'CMA_1998': '',
            "PENAL_CODE": "Penal_Code.json.law_document.extraction.test",
            "SEDITION_ACT": "akta-15-akta-hasutan-1948.v1.en.law_document",
            # 'TIKTOK_GUIDELINES': ''
        }
        self.collection_order = list(self.collections.keys())

    def get_embedding(self, text: str, max_retries: int = 3) -> List[float]:
        """Get embedding vector for text content."""
        for attempt in range(max_retries):
            try:
                # Send request to embedding service
                response = requests.get(
                    self.embedding_url,
                    params={"promt": text, "model": self.embedding_model},
                )
                response.raise_for_status()

                # Parse response using ast.literal_eval
                result = ast.literal_eval(response.content.decode("utf-8"))

                if not isinstance(result, list):
                    raise ValueError("Invalid embedding response format")

                # Force dimension to 768
                current_dim = len(result)
                if current_dim > 768:
                    # Truncate to 768 dimensions
                    result = result[:768]
                elif current_dim < 768:
                    # Pad with zeros to reach 768 dimensions
                    result.extend([0.0] * (768 - current_dim))

                return result

            except Exception as e:
                logger.error(
                    f"Embedding failed (attempt {attempt + 1}/{max_retries}): {str(e)}"
                )
                if attempt == max_retries - 1:
                    raise
                time.sleep(2**attempt)

    def query_llm(self, prompt: str, max_retries: int = 3) -> str:
        """Query LLM for compliance analysis."""
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.llm_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.llm_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.llm_model,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=self.llm_timeout,
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]

                if "NO_VIOLATIONS" in content:
                    return content

                # Extract and validate JSON response
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    parsed_json = json.loads(json_str)
                    if isinstance(parsed_json, dict) and "violations" in parsed_json:
                        return json_str

                return "NO_VIOLATIONS"

            except Exception as e:
                logger.error(
                    f"LLM query failed (attempt {attempt + 1}/{max_retries}): {str(e)}"
                )
                if attempt == max_retries - 1:
                    raise
                time.sleep(2**attempt)

    def analyze_content(
        self, content: str, document_ids: List[str] = None
    ) -> List[ViolationFound]:
        """Analyze content for law violations using vector search and LLM."""
        violations = []
        start_time = time.time()
        logger.info(f"Starting compliance analysis for documents: {document_ids}")

        try:
            query_vector = self.get_embedding(content)

            # Use provided document_ids or all collections if None
            categories_to_check = (
                document_ids if document_ids else self.collection_order
            )

            for category in categories_to_check:
                if category.upper() not in self.collections:
                    logger.warning(f"Skipping unknown category: {category}")
                    continue

                collection_name = self.collections[category.upper()]
                search_results = self.qdrant.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=5,
                    with_payload=True,
                )

                if not search_results:
                    continue

                # Prepare analysis context and prompt
                context = "\n\n".join(
                    [f"Reference:\n{hit.payload['text']}" for hit in search_results]
                )

                prompt = self._generate_analysis_prompt(category, context, content)
                llm_response = self.query_llm(prompt)

                if "NO_VIOLATIONS" not in llm_response:
                    try:
                        response_data = json.loads(llm_response)
                        if response_data.get("violations"):
                            for v in response_data["violations"]:
                                violations.append(ViolationFound(**v))
                                logger.info(
                                    f"Found violation in {category}: {v['section_name']}"
                                )
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse LLM response for {category}")

            logger.info(
                f"Analysis completed in {time.time() - start_time:.2f}s - Found {len(violations)} violations"
            )
            return violations

        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise

    def _generate_analysis_prompt(
        self, category: str, context: str, content: str
    ) -> str:
        """Generate category-specific analysis prompt."""
        return f"""
        As a Compliance Checker Agent (Chepir), analyze the following content specifically against {category} regulations:

        {context}

        Content to analyze:
        "{content}"

        Focus your analysis ONLY on {category} violations. Consider:
        1. Specific sections or rules being violated
        2. Clear explanation of how the content violates these sections
        3. Direct quotes from the reference text supporting the violation

        If no violations are found for {category}, respond with "NO_VIOLATIONS".

        Format your response as JSON:
        {{
            "violations": [
                {{
                    "category": "{category}",
                    "section_name": "specific section number/name",
                    "description": "detailed explanation",
                    "reference_text": "quoted text from reference"
                }}
            ]
        }}"""

    def format_violations_report(self, violations: List[ViolationFound]) -> str:
        """Format violations into a structured report."""
        categories = {
            # "CMA 1998": [],
            "Penal Code": [],
            "Sedition Act 1948": [],
            # "TikTok Community Guidelines": []
        }

        for v in violations:
            if v.category in categories:
                categories[v.category].append(v)

        report = ["Law Violations:\n"]
        for category, cat_violations in categories.items():
            report.append(f"\n{category}:")
            if cat_violations:
                sections = {v.section_name for v in cat_violations}
                report.extend([f"- {section}" for section in sections])
                report.append("\nViolation Details:")
                for v in cat_violations:
                    report.extend(
                        [f"- {v.description}", f"  Reference: {v.reference_text}\n"]
                    )
            else:
                report.append("No violations found.\n")

        return "\n".join(report)


def check_required_files() -> bool:
    """Validate presence of all required input files."""
    required_files = [
        "data/subcategories.csv",
        "data/video_summary.csv",
        "data/video_captions.csv",
        "data/volga_results_dev.csv",
        "data/video_justification_risk.csv",
    ]
    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        raise FileNotFoundError(f"Missing required files: {missing}")
    return True


def combine_input_data(
    subcategories_file: str,
    video_summary_file: str,
    video_captions_file: str,
    transcriptions_file: str,
    risk_justification_file: str,
) -> str:
    """Combine data from multiple CSV files into a permanent input file."""
    logger.info("Combining input data from multiple sources")
    combined_file = "data/chepir_input.csv"

    try:
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)

        # Verify input files exist
        for file_path in [
            subcategories_file,
            video_summary_file,
            video_captions_file,
            transcriptions_file,
            risk_justification_file,
        ]:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Input file not found: {file_path}")
            if os.path.getsize(file_path) == 0:
                raise ValueError(f"Input file is empty: {file_path}")

        # Read and combine all data into a single text column
        with open(combined_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["_id", "text"])
            writer.writeheader()

            # Process each file and combine the content
            all_data = {}
            for file_path in [
                subcategories_file,
                video_summary_file,
                video_captions_file,
                transcriptions_file,
                risk_justification_file,
            ]:
                with open(file_path, "r", encoding="utf-8") as input_file:
                    reader = csv.DictReader(input_file)
                    for row in reader:
                        video_id = row.get("_id", "")
                        if video_id not in all_data:
                            all_data[video_id] = []
                        # Collect all non-empty values from the row
                        row_values = [v for v in row.values() if v and v != video_id]
                        all_data[video_id].extend(row_values)

            # Write combined data
            for video_id, values in all_data.items():
                combined_text = " ".join(values).strip()
                if combined_text:
                    writer.writerow({"_id": video_id, "text": combined_text})

            logger.info(
                f"Successfully combined {len(all_data)} items into: {combined_file}"
            )
        return combined_file

    except Exception as e:
        logger.error(f"Error combining input data: {str(e)}")
        raise


def process_content(input_file: str, output_file: str):
    """Process content with incremental saving"""
    checker = ComplianceChecker()

    try:
        os.makedirs("output", exist_ok=True)
        output_file = output_file.replace(".csv", ".json")

        # Initialize or load existing results
        if os.path.exists(output_file):
            with open(output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                results = data.get("analysis_results", [])
                processed_ids = {r["content_id"] for r in results}
        else:
            results = []
            processed_ids = set()

        with open(input_file, "r", encoding="utf-8") as infile:
            reader = csv.DictReader(infile)
            rows = list(reader)

            logger.info(f"Processing {len(rows)} rows from input file")

            for row in rows:
                content_id = row.get("_id", "")

                # Skip if already processed
                if content_id in processed_ids:
                    logger.info(f"Skipping already processed ID: {content_id}")
                    continue

                text = row.get("text", "")
                if not text:
                    logger.warning(f"Empty content for ID: {content_id}")
                    continue

                try:
                    logger.info(f"Processing content ID: {content_id}")
                    violations = checker.analyze_content(text)
                    violations_report = checker.format_violations_report(violations)

                    # Create result for this row
                    result = {
                        "content_id": content_id,
                        "violations_found": len(violations) > 0,
                        "violations_report": violations_report,
                        "violations_details": [
                            {
                                "category": v.category,
                                "section_name": v.section_name,
                                "description": v.description,
                                "reference_text": v.reference_text,
                            }
                            for v in violations
                        ],
                        "analysis_timestamp": datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }

                    results.append(result)

                    # Save after each successful row
                    with open(output_file, "w", encoding="utf-8") as outfile:
                        json.dump(
                            {
                                "analysis_results": results,
                                "total_processed": len(results),
                                "last_update": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            },
                            outfile,
                            indent=2,
                            ensure_ascii=False,
                        )

                    logger.info(
                        f"Processed and saved content ID: {content_id} - Found {len(violations)} violations"
                    )
                    processed_ids.add(content_id)

                except Exception as e:
                    logger.error(f"Error processing content ID {content_id}: {str(e)}")
                    continue

        logger.info(
            f"Results saved to: {output_file} ({os.path.getsize(output_file)} bytes)"
        )
        return True

    except Exception as e:
        logger.error(f"Error in process_content: {str(e)}")
        return False


if __name__ == "__main__":
    try:
        # Validate environment and required files
        logger.info("Validating environment and required files...")
        validate_env_variables()
        check_required_files()

        # Process input data with progress logging
        logger.info("Starting compliance analysis...")
        input_file = combine_input_data(
            "data/subcategories.csv",
            "data/video_summary.csv",
            "data/video_captions.csv",
            "data/volga_results_dev.csv",
            "data/video_justification_risk.csv",
        )
        logger.info(f"Combined input file created and saved as: {input_file}")

        output_file = "output/compliance_analysis.json"
        logger.info(f"Processing content and writing results to: {output_file}")
        process_content(input_file, output_file)
        logger.info("Compliance analysis completed successfully")

        # Verify final output
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            logger.info(f"Results available in: {output_file}")
        else:
            raise ValueError("Output file missing or empty")

    except Exception as e:
        logger.error(f"Program terminated with error: {str(e)}")
        raise
