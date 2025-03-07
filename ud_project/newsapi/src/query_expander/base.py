import os
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()

llama_model = os.getenv("LLAMA70B_MODEL")
if llama_model == "":
    raise ValueError("llama_model is not valid!")

llama_base_url = os.getenv("LLAMA70B_LLM_BASE_URL")
if llama_base_url == "":
    raise ValueError("llama_base_url is not valid!")

llama_api_key = os.getenv("LLAMA70B_LLM_API_KEY")
if llama_api_key == "":
    raise ValueError("llama_api_key is not valid!")


llama70b_client = OpenAI(base_url=llama_base_url, api_key=llama_api_key)


# to expand the topic before sending to the API
def expand_topic(
    topic_to_expand: str,
) -> str:
    system_prompt: str = """Write one expanded news query based on the news query given to enhance the news searching. Write only the expandend news query. Do not include operators. Hard limit the expanded query to 15 words. Do not include any explanation.
"""

    user_prompt: str = f"""News query: {topic_to_expand}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    result = llama70b_client.chat.completions.create(
        model=llama_model,
        messages=messages,
        max_tokens=500,
        temperature=0.3,
    )

    result_to_clean = result.choices[0].message.content
    clean_output = result_to_clean.replace("```python", "").replace("```", "")

    return clean_output
