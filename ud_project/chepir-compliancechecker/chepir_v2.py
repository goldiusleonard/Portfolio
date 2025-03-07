import ast
import json
import os
import requests
import time
from dataclasses import dataclass
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from typing import List
from utils import setup_logging, validate_embedding_config, get_service_timeout

# Initialize logger
logger = setup_logging("compliance_checker_v2")


@dataclass
class ViolationFound:
    """Represents a detected law violation."""

    category: str
    section_name: str
    description: str
    reference_text: str


class ComplianceChecker:
    """Streamlined compliance checking engine for API usage."""

    def __init__(self):
        load_dotenv()
        self._validate_and_init_config()
        self._init_qdrant_client()
        self._setup_collections()

    def _validate_and_init_config(self):
        """Initialize and validate configuration"""
        if not validate_embedding_config():
            raise EnvironmentError("Missing embedding configuration")

        # Initialize configurations
        self.embedding_url = os.getenv("EMBEDDING_MODEL_URL")
        self.embedding_model = os.getenv("EMBEDDING_MODEL_NAME")
        self.embedding_timeout = get_service_timeout("EMBEDDING")

        self.llm_url = os.getenv("LLM_BASE_URL")
        self.llm_key = os.getenv("LLM_API_KEY")
        self.llm_model = os.getenv("MODEL")
        self.llm_timeout = get_service_timeout("LLM")

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
            "PENAL_CODE": "Penal_Code.json.law_document.extraction.test",
            "SEDITION_ACT": "akta-15-akta-hasutan-1948.v1.en.law_document",
        }
        self.collection_order = list(self.collections.keys())

    def get_embedding(self, text: str, max_retries: int = 3) -> List[float]:
        """Get embedding vector for text content."""
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    self.embedding_url,
                    params={"promt": text, "model": self.embedding_model},
                )
                response.raise_for_status()

                result = ast.literal_eval(response.content.decode("utf-8"))

                if not isinstance(result, list):
                    raise ValueError("Invalid embedding response format")

                # Force dimension to 768
                current_dim = len(result)
                if current_dim > 768:
                    result = result[:768]
                elif current_dim < 768:
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
