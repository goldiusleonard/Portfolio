"""Module to generate wordcloud and push to database."""

from __future__ import annotations

import logging
import os
import string
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import en_core_web_md
import gensim
import pandas as pd
import pytz
import spacy
from dotenv import load_dotenv
from gensim import corpora
from nltk.corpus import stopwords
from sqlalchemy import func

from connections.azure_connection import get_azure_engine, get_azure_session
from credentials.mysql_credentials import get_credentials
from models.ba_content_data_asset_table import ContentModel
from models.word_cloud_table import WordCloud

if TYPE_CHECKING:
    from spacy.language import Language
    from sqlalchemy.orm import Session


load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def load_stopwords(file_path: str) -> set[str]:
    """Load stopwords from files."""
    with Path(file_path).open(encoding="utf-8") as file:
        return {line.strip().lower() for line in file}


def clean_text(text: str) -> str:
    """Clean text and remove punctuation."""
    max_length = 3
    delete_dict = {sp_char: "" for sp_char in string.punctuation}
    delete_dict[" "] = " "
    table = str.maketrans(delete_dict)
    text1 = text.translate(table)
    text_arr = text1.split()
    text2 = " ".join([w for w in text_arr if (not w.isdigit() and len(w) > max_length)])
    return text2.lower()


def remove_stopwords(text: str, stop_words: set[str]) -> str:
    """Remove stopwords from the text."""
    text_arr = text.split(" ")
    filtered_words = [word for word in text_arr if word.lower() not in stop_words]
    return " ".join(filtered_words)


def lemmatization(
    texts: list,
    allowed_postags: list | None = None,
    nlp: Language = None,
) -> list:
    """Perform lemmatization."""
    allowed_postags = ["NOUN", "ADJ", "X", "PROPN"]
    output = []
    for sent in texts:
        doc = nlp(sent)
        output.append([token.lemma_ for token in doc if token.pos_ in allowed_postags])
    return output


def clean_text2(text: str) -> str:
    """Clean text."""
    translator = str.maketrans("", "", string.punctuation)
    return text.translate(translator).lower()


def filter_keywords_by_pos(
    word_freq: list,
    pos_tags: list | None = None,
    nlp: Language = None,
) -> list:
    """Classify words into POS tags (noun, adjective, and 'X')."""
    filtered_keywords = []
    pos_tags = ["NOUN", "ADJ", "X", "PROPN"]

    for word in word_freq:
        # Process the word using spaCy
        doc = nlp(word)

        # Check if the word is tagged with any of the desired POS tags
        for token in doc:
            if token.pos_ in pos_tags:
                filtered_keywords.append(word)
                break

    return filtered_keywords


def push_tables(wordcloud_df: pd.DataFrame) -> None:
    """Push tables to database."""
    ada_da_test_db = os.getenv("MCMC_BA_DB_NAME")
    user, password, host, port = get_credentials("ada")
    session = get_azure_session(ada_da_test_db, user, password, host, port)
    try:
        # Convert DataFrame rows to SQLAlchemy model instances
        instances = [WordCloud(**row.to_dict()) for _, row in wordcloud_df.iterrows()]

        # Add all instances to the session
        session.add_all(instances)

        # Commit the transaction
        session.commit()
        logging.info("Data inserted successfully!")
    except Exception:
        session.rollback()
        logging.exception("An error occurred")
    finally:
        session.close()
        logging.info("session closed")


def clean_text3(input_df: pd.DataFrame) -> pd.DataFrame:
    """Clean columns."""
    input_df["video_description"] = input_df["video_description"].fillna("")
    input_df["original_transcription"] = input_df["original_transcription"].fillna("")
    # Combine the two columns for analysis
    input_df["text"] = (
        input_df["original_transcription"] + " " + input_df["video_description"]
    )
    # Clean the text data
    input_df["text"] = input_df["text"].apply(clean_text)
    input_df["Num_words_text"] = input_df["text"].apply(lambda x: len(str(x).split()))
    return input_df


def check_datetime(session: Session) -> tuple[bool, datetime.datetime]:
    """Check if there is new data."""
    malaysia_timezone = pytz.timezone("Asia/Kuala_Lumpur")
    latest_marketplace_date = session.query(
        func.max(ContentModel.ss_process_timestamp),
    ).scalar()
    latest_marketplace_date = malaysia_timezone.localize(latest_marketplace_date)
    latest_wordcloud_date = session.query(
        func.max(WordCloud.processed_timestamp),
    ).scalar()
    latest_wordcloud_date_tz = malaysia_timezone.localize(latest_wordcloud_date)

    formatted_dt_wordcloud = latest_wordcloud_date_tz.strftime("%Y-%m-%d %H:%M:%S")
    formatted_dt_marketplace = latest_marketplace_date.strftime("%Y-%m-%d %H:%M:%S")
    no_new_data = formatted_dt_wordcloud > formatted_dt_marketplace
    return no_new_data, latest_wordcloud_date


def get_wordcloud(input_df: pd.DataFrame) -> pd.DataFrame:
    """Generate wordcloud."""
    max_length = 150
    min_length = 20
    # Part 2: Get stopwords
    stopwords_dir = Path(os.getenv("STOPWORDS_PATH", "./input/"))

    malay_indonesian_stopwords_path = stopwords_dir / "malay-indonesian_stopwords.txt"
    english_stopwords_path = stopwords_dir / "english-stopwords.txt"

    malay_indonesian_stopwords = load_stopwords(malay_indonesian_stopwords_path)
    english_stopwords = load_stopwords(english_stopwords_path)
    stop_words = (
        set(stopwords.words("english")) | malay_indonesian_stopwords | english_stopwords
    )

    # Part 3: Clean and combine columns to be used
    input_df = clean_text3(input_df)

    # Filter short reviews for analysis
    mask = (input_df["Num_words_text"] < max_length) & (
        input_df["Num_words_text"] >= min_length
    )
    df_short_reviews = input_df[mask]
    # Sample 100 records if the DataFrame has a sufficient number of rows
    df_sampled = df_short_reviews.sample(
        n=min(100, len(df_short_reviews)),
        random_state=42,
    )
    # Remove stopwords from the text
    df_sampled["text"] = df_sampled["text"].apply(
        lambda x: remove_stopwords(x, stop_words),
    )
    # Perform lemmatization
    nlp = en_core_web_md.load(disable=["parser"])
    text_list = df_sampled["text"].tolist()
    tokenized_reviews = lemmatization(text_list, nlp=nlp)
    # Convert to document term frequency
    dictionary = corpora.Dictionary(tokenized_reviews)
    doc_term_matrix = [dictionary.doc2bow(rev) for rev in tokenized_reviews]

    # Part4: LDA model
    # Create LDA model
    lda = gensim.models.ldamodel.LdaModel
    lda_model = lda(
        corpus=doc_term_matrix,
        id2word=dictionary,
        num_topics=10,
        random_state=100,
        chunksize=1000,
        passes=50,
        iterations=100,
    )

    # Part 5: Get and store all words
    combined_text = (
        input_df["original_transcription"].fillna("")
        + " "
        + input_df["video_description"].fillna("")
    )
    cleaned_corpus = combined_text.apply(clean_text2).str.cat(sep=" ")
    all_words = [word for word in cleaned_corpus.split() if word not in stop_words]
    logging.info("length of words: %s", len(all_words))

    # Part 6: Get LDA keywords
    topics = lda_model.print_topics()
    keywords = []
    # Extract words from LDA topics and add to keywords
    for _topic_id, topic_words in topics:
        # Extract words by splitting the string (ignoring weights)
        words = [word.split("*")[1].strip('"') for word in topic_words.split(" + ")]
        # Update keywords list with new words (avoiding duplicates)
        keywords.extend([word for word in words if word not in keywords])

    # Remove duplicates if any
    keywords = list(set(keywords))
    # Print the updated keywords list
    logging.info("length of keywords: %s", len(keywords))

    # Part 7: filter the keywords with all words
    # Load the spaCy language model
    nlp = spacy.load("en_core_web_sm")
    # Get the filtered keywords (NOUN, ADJ, and X)
    filtered_keywords = filter_keywords_by_pos(keywords, nlp=nlp)
    # Print the filtered keywords
    logging.info("length of filtered keywords: %s", len(filtered_keywords))
    logging.info("%s", filtered_keywords)

    # Part 7: count the frequency of filtered keywords in all words
    # Filter the words to count only those in the keywords list
    filtered_words = [word for word in all_words if word in filtered_keywords]
    # Use Counter to count the occurrences of each keyword in the filtered list
    word_freq = Counter(filtered_words)
    logging.info("word_freq: %s", word_freq)
    logging.info("len word_freq: %s", len(word_freq))

    # Part 8: Getting final output structure
    malaysia_timezone = pytz.timezone("Asia/Kuala_Lumpur")
    keyword_data = []
    for keyword, count in word_freq.items():
        for _, row in df_sampled.iterrows():
            keyword_data.append(
                {
                    "id": row.name,  # Use the DataFrame index as ID
                    "keyword": keyword,
                    "count": count,
                    "category": row["category"],
                    "crawling_timestamp": row["ss_process_timestamp"],
                    "processed_timestamp": datetime.now(malaysia_timezone).strftime(
                        "%Y-%m-%d %H:%M:%S",
                    ),
                },
            )
    output_df = pd.DataFrame(keyword_data)
    logging.info("output_df head(10): %s", output_df.head(10))

    # Step 1: Convert 'timestamp' column to datetime
    output_df["crawling_timestamp"] = pd.to_datetime(output_df["crawling_timestamp"])

    # Step 2: Sort by 'timestamp' in descending order
    output_df = output_df.sort_values(by="crawling_timestamp", ascending=False)

    # Step 3: Drop duplicates based on both 'keyword' and 'category'
    output_df = output_df.drop_duplicates(subset=["keyword", "category"], keep="first")

    # Step 4: Reset the index to make 'id' auto-increment
    output_df.reset_index(drop=True)
    output_df["id"] = output_df.index

    # Final DataFrame
    logging.info("final output_df head(10): %s", output_df.head(10))
    return output_df


def process_wordcloud() -> dict:
    """Generate wordcloud."""
    # Part 1: Fetch marketpplace tables from MySQL
    db_name = os.getenv("MCMC_BA_DB_NAME")

    user, password, host, port = get_credentials("ada")

    engine = get_azure_engine(db_name, user, password, host, port)
    session = get_azure_session(db_name, user, password, host, port)

    no_new_data, latest_wordcloud_date = check_datetime(session)

    if no_new_data:
        logging.info("no new data, ending process.")
        return {"message": "No new data to be processed"}

    logging.info("engine: %s", engine)
    logging.info("session: %s", session)
    all_output_dfs = []

    unique_values = session.query(ContentModel.category).distinct().all()
    unique_values = [value[0] for value in unique_values]
    logging.info("Unique categories: %s", unique_values)
    try:
        for values in unique_values:
            input_df = pd.read_sql(
                session.query(ContentModel)
                .filter(ContentModel.category == values)
                .statement,
                session.bind,
            )
            # filter only new data
            input_df["ss_process_timestamp"] = pd.to_datetime(
                input_df["ss_process_timestamp"],
            )
            formatted_dt = latest_wordcloud_date.strftime("%Y-%m-%d %H:%M:%S")
            input_df = input_df[input_df["ss_process_timestamp"] > formatted_dt]
            logging.info(
                "Table fetched. Category: %s, Shape: %s",
                values,
                input_df.shape,
            )
            output_df = get_wordcloud(input_df)
            all_output_dfs.append(output_df)
            count = session.query(func.count(WordCloud.id)).scalar()
            logging.info("Count of current wordcloud: %s", count)
    finally:
        session.close()
        logging.info("session closed")

    final_output_df = pd.concat(all_output_dfs, ignore_index=True)
    final_output_df = (
        final_output_df.sort_values(by="count", ascending=False)
        .groupby("category")
        .apply(lambda x: x)
    )
    final_output_df = final_output_df.reset_index(drop=True)
    if "id" in final_output_df.columns:
        final_output_df = final_output_df.drop(columns=["id"])
    push_tables(final_output_df)
    logging.info("new data processed.")
    return {"message": "Data processed."}


if __name__ == "__main__":
    process_wordcloud()
