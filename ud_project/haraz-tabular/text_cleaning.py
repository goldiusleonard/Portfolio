import re
import string

from logging_section import setup_logging

# Set up logging
logger = setup_logging()


class TextCleaner:
    def __init__(self):
        pass

    def basic_cleaning(self, text):
        """Basic cleaning operations like removing special characters and excessive whitespace"""

        # Remove swear words (****)
        text = re.sub(r"\*+", "swear", text)
        # Remove excessive whitespace
        text = " ".join(text.split())
        # Remove punctuation marks
        text = re.sub(r"[!?]+", "", text)
        # Reduce repetitive alphabets
        text = re.sub(r"([a-zA-Z])\1{2,}", r"\1", text)
        # Reduce repetitive special characters
        text = re.sub(r"([^\w\s])\1{2,}", r"\1", text)
        # Replace newlines with a space
        text = re.sub(r"\s*\n\s*", " ", text)
        return text

    def unbold_character(self, text):
        """Convert bold Unicode text to regular ASCII font"""
        bold_to_regular = {
            **{
                char: chr(65 + i) for i, char in enumerate("𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙")
            },
            **{
                char: chr(97 + i) for i, char in enumerate("𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳")
            },
            **{char: str(i) for i, char in enumerate("𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗")},
        }
        return "".join(bold_to_regular.get(char, char) for char in text)

    @staticmethod
    def filter_latin_word(df, column, threshold=70.0):
        """Filter rows the column contain at least a threshold percentage of Latin words."""
        # Set of valid Latin characters (lowercase and uppercase)
        latin_chars = set(string.ascii_letters)

        def latin_percentage(text):
            if not isinstance(text, str) or not text.strip():
                return 0.0
            words = text.split()
            latin_words = sum(
                all(char in latin_chars for char in word if char.isalpha())
                for word in words
            )
            return (latin_words / len(words)) * 100

        # Filter rows by applying the function to all specified columns
        df = df[df[column].apply(latin_percentage) >= threshold]

        return df

    def clean(self, df, column):
        logger.info(f"Starting text cleaning for columns: {column}")
        try:
            df[column] = df[column].astype(str).apply(self.basic_cleaning)
            df[column] = df[column].astype(str).apply(self.unbold_character)
            logger.info("Text cleaning completed.")
            return df
        except Exception as e:
            logger.error(f"Error during text cleaning: {e}")
            raise
