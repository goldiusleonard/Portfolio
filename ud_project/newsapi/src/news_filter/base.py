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


def filter_news(
    article_list: list,
    news_query: str,
) -> list:
    filtered_list: list = []
    for article in article_list:
        title = article["title"]

        system_prompt = """Analyse the given news article title and its query. Your task is to label the news as `relevant` or `irrelevant` based on the news title compared to its query. Output only `relevant` or `irrelevant`. Do not include any explanations.

Examples:

1. News article title: "Apple launches new iPhone 15 with groundbreaking features"
   Query: "Latest smartphone releases"
   Output: relevant

2. News article title: "Global warming impacts Arctic wildlife"
   Query: "Smartphone industry trends"
   Output: irrelevant

3. News article title: "Tesla unveils new electric truck with enhanced battery life"
   Query: "Electric vehicle innovations"
   Output: relevant

4. News article title: "Study reveals health benefits of Mediterranean diet"
   Query: "Technology advancements in healthcare"
   Output: irrelevant

5. News article title: "Meta introduces AI-driven features for Facebook and Instagram"
   Query: "Social media AI tools"
   Output: relevant

"""

        user_prompt = f"""News article title: {title}
Query: {news_query}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        result = llama70b_client.chat.completions.create(
            model=llama_model,
            messages=messages,
            max_tokens=5,
            temperature=0.1,
        )
        result = result.choices[0].message.content

        if result.lower() == "relevant":
            filtered_list.append(article)

    return filtered_list
