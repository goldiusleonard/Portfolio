import os
import csv
import json
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


# to evaluate news articles
def evaluator(
    expanded_query,
    sub_category,
    topic,
    title,
):
    system_prompt = """

Please analyze and evaluate the news article title against the expanded query, sub_category, and topic below. 
Based on the relevance, return a score:
- If the title is **relevant** to the sub_category, topic, and expanded query, return **1**.
- If the title is **not relevant**, return **0**.
Do **not** provide any explanation or reasoning, only return the score (0 or 1).
DO NOT HALLUCINATE.
"""

    user_prompt = f"""
Analyse and Evaluate the strings below:
sub_category: {sub_category}
topic: {topic}
News article title: {title}

Expanded Query: {expanded_query}

"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    result = llama70b_client.chat.completions.create(
        model=llama_model,
        messages=messages,
        max_tokens=1000,
        temperature=0.3,
    )
    result = result.choices[0].message.content
    print("the score:", result)

    return result


#### the testcase_articles.json

# Assuming your JSON data is in a file named 'testcase_articles.json'
with open("evaluation/testcase_articles.json", "r") as file:
    data = json.load(file)

# Extracting 'topic', 'expanded_query', and 'title' from each dictionary inside the list
extracted_data = []
sub_category = "Hate Speech"

for entry_list in data:
    for entry in entry_list:
        topic = entry.get("topic")
        expanded_query = entry.get("expanded_query")
        title = entry.get("title")

        score = evaluator(expanded_query, sub_category, topic, title)

        extracted_data.append(
            {
                "topic": topic,
                "expanded_query": expanded_query,
                "title": title,
                "score": score,
            }
        )

# Print the extracted data
for item in extracted_data:
    print(item)

# Writing the extracted data into a CSV file
with open("extracted_data.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file, fieldnames=["topic", "expanded_query", "title", "score"]
    )
    writer.writeheader()  # Write the header
    writer.writerows(extracted_data)  # Write the data rows

print("Data has been written to 'extracted_data.csv'.")
