import os

import requests
from fastapi import HTTPException

from logging_section import setup_logging

# import pandas as pd

logger = setup_logging()


def gen_category_subcategory(content: str):
    """Input: Content (text)
    Return: Generate category and subcategories.
    """
    logger.info("Starting category & subcategory generation")

    LLM_BASE_URL = os.getenv("LLM_BASE_URL")
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    MODEL = os.getenv("MODEL")

    prompt = f"""
        Context:  
        You are an advanced AI model specializing in classifying content into below defined categories and subcategories.  
        Below are the categories and subcategories that you can classify the content into:

        List of categories and subcategories:
        - **Scam**  
        - Gold, Cryptocurrency, Forex  

        - **3R**  
        - Race, Religion, Royalty  

        - **ATIPSOM**  
        - Human trafficking, Job Scam, Illegal Immigrants  

        - **Sexual and Family**  
        - Sexual Crimes, Violation of women’s rights, Violation of Children’s rights  

        Their definitions are as below:

        Categories and Subcategories:
        Category: Scams
        This category includes deceptive practices intended to defraud individuals or organizations, often by offering false promises or misleading information.
        Gold: Scams involving investments in gold or fraudulent schemes promising high returns related to gold trading.
        Cryptocurrency: Scams related to digital currencies, including fake initial coin offerings (ICOs), phishing attacks targeting crypto wallets, and Ponzi schemes.
        Forex: Fraudulent activities involving foreign exchange trading, such as unregistered brokers, pyramid schemes, or promises of guaranteed profits from forex trades.
        
        Category: 3R
        This category covers sensitive topics related to race, religion, and royalty, which may provoke controversy or violate societal norms.
        Race: Content that highlights or discriminates based on ethnicity or racial differences, potentially inciting hatred or division.
        Religion: Material discussing or criticizing religious beliefs, practices, or figures in ways that may cause offense or controversy.
        Royalty: Issues involving members of the monarchy or discussions that could be deemed disrespectful or inappropriate regarding royal figures.
        
        Category: ATIPSOM
        This category focuses on crimes and issues covered under the Anti-Trafficking in Persons and Smuggling of Migrants (ATIPSOM) Act.
        Human trafficking: Activities involving the illegal trade or exploitation of people, including forced labor and sex trafficking.
        Job Scam: Fraudulent job offers that exploit individuals, often leading to forced labor or financial loss.
        Illegal Immigrants: Issues involving the smuggling or exploitation of individuals crossing borders unlawfully.
        
        Category: Sexual and Family
        This category addresses sensitive topics related to sexual offenses, family dynamics, and violations of individual rights.
        Sexual Crimes: Includes crimes such as pornography distribution, rape, and other forms of sexual exploitation.
        Violation of Women’s Rights: Situations where women’s rights are infringed upon, including gender-based violence, discrimination, or denial of fundamental rights.
        Violation of Children’s Rights: Issues such as child abuse, neglect, trafficking, or exploitation that infringe on the rights of children. 

        Instructions:  
        1. Carefully analyze the provided content.  
        2. Determine the single most relevant category and subcategory from the list above that best describes the content.  
        3. If the content does not provide enough information to determine a category or subcategory, return:  Not Related, Not Related
        4. If no subcategory from the list applies to the content, respond with "Not Related" for the subcategory. 
        5. If the input is empty, null or none, return:  None, None.
        6. Your response must strictly adhere to this format:  <Category>,<Subcategory>

        Rules: 
        - Do not include any explanations, notes, or additional formatting.  
        - Do not rephrase or repeat the content.
        - Strictly do not include include phrase "Category", "Subcategory", "Response" or "Output" in your response.
        - Only return categories and subcategories from the list provided.
        - Do not include fallback responses like "Please provide the category and subcategory."  
        - The output must only contain the  one category and one subcategory in the specified format.  

        Content:
        {content}  

        Example Output: 
        Scam,Gold  

        Before responding, check again and confirm if your output is compliant with the rules. If not, adjust your output to comply the formats above.
        """

    # Prepare payload
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "temperature": 0.3,  # High: Creative but unpredictable responses. Low: Predictable and coherent answers
        "top_p": 0.4,  # High: Diverse and creative responses. Low: Accurate and fact-based results.
        "max_tokens": 50,  # Low: Short, concise answers.
        "frequency_penalty": 0.2,  # High: More varied output. Low: Repetitive output.
        "presence_penalty": 0.2,  # High: Variety in the output. Low: Repetitive responses.
        # "extra_body": {"guided_choice": ["category"] }
    }

    # Set headers for API request
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        # Make POST request to the LLM API
        response = requests.post(
            f"{LLM_BASE_URL}/completions",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()

        result = response.json()
        output = result["choices"][0]["text"].strip()

        result = parse_llm_response(output)

        logger.info("Category & Subcategories generation completed successfully")

        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"API Request Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error with LLM API: {e}")

    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        raise HTTPException(status_code=500, detail=f"Error parsing response: {e}")


def parse_llm_response(response):
    """Parse the LLM response to extract category and subcategory.
    Args: response (str): The response string from LLM.
    Returns: dict: A dictionary containing 'category' and 'subcategory'.
    """
    try:
        # Extract the part after 'Response:'
        if "Response:" in response:
            clean_response = response.split("Response:")[1].strip()
        else:
            clean_response = response.strip()

        # Remove any newlines or whitespace around the response
        clean_response = clean_response.replace("\n", "").strip()

        # Split into category and subcategory
        category, subcategory = [item.strip() for item in clean_response.split(",")]

        return {
            "category": category,
            "subcategory": subcategory,
        }
    except Exception as e:
        print(f"Error parsing response: {e}")
        # Return None in case of an error
        return {
            "category": "None",
            "subcategory": "None",
        }


# sample_text =  """
# Forex trading, also known as foreign exchange trading, involves buying and selling currencies in the global market.
# While it presents opportunities for profit, it has also become a breeding ground for fraudulent activities and scams.
# Unsuspecting traders, especially beginners, are often lured into deceptive schemes that promise high returns with minimal risk.
# """


# # for local testing
# if __name__ == "__main__":
#     #sample_output = pd.read_csv('sample_summary.csv')
#     # print(gen_category_subcategory(sample_text))
#     #Apply the function to the 'video_summary' column and store the result in the 'result' column
#     #sample_output['result'] = sample_output['video_summary'].apply(gen_category_subcategory)
#     #sample_output.to_csv('sample_summary_output.csv', index=False)


# ### "extra_body"={"guided_choice": ["dimension", "fact"]},
