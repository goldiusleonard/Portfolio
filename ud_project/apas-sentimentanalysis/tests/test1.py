import os
import shutil


class SentimentAnalyzer:
    """Mock sentiment analyzer for testing."""

    def analyze_text_files_in_folder(self, input_folder, output_folder):
        os.makedirs(output_folder, exist_ok=True)
        for file_name in os.listdir(input_folder):
            if file_name.endswith(".txt"):
                with open(
                    os.path.join(input_folder, file_name),
                    encoding="utf-8",
                ) as file:
                    text = file.read()
                sentiment = self.analyze_text(text)
                output_file_name = os.path.splitext(file_name)[0] + "_sentiment.txt"
                output_file_path = os.path.join(
                    output_folder,
                    os.path.splitext(file_name)[0],
                    output_file_name,
                )
                os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
                with open(output_file_path, "w", encoding="utf-8") as output_file:
                    output_file.write(f"Text: {text}\nSentiment: {sentiment}\n")

    def analyze_text(self, text):
        """Mock analysis to determine sentiment."""
        if "amazing" in text or "love" in text:
            return "Positive"
        if "bad" in text or "hate" in text:
            return "Negative"
        return "Neutral"


def test_sentiment_analysis_hardcoded():
    """Run a test for the sentiment analyzer with hardcoded text."""
    # Define folders and filenames
    TEST_INPUT_FOLDER = "test_input_hardcoded"
    TEST_OUTPUT_FOLDER = "test_output_hardcoded"
    TEST_FILE_NAME = "test_file_hardcoded.txt"
    TEST_FILE_CONTENT = (
        "This product is absolutely amazing and I love using it every day!"
    )

    # Setup: Create test environment
    if os.path.exists(TEST_INPUT_FOLDER):
        shutil.rmtree(TEST_INPUT_FOLDER)
    if os.path.exists(TEST_OUTPUT_FOLDER):
        shutil.rmtree(TEST_OUTPUT_FOLDER)

    os.makedirs(TEST_INPUT_FOLDER, exist_ok=True)

    # Create the hardcoded text file
    input_file_path = os.path.join(TEST_INPUT_FOLDER, TEST_FILE_NAME)
    with open(input_file_path, "w", encoding="utf-8") as file:
        file.write(TEST_FILE_CONTENT)

    try:
        # Instantiate the sentiment analyzer
        sentiment_analyzer = SentimentAnalyzer()

        # Run the analysis
        sentiment_analyzer.analyze_text_files_in_folder(
            TEST_INPUT_FOLDER,
            TEST_OUTPUT_FOLDER,
        )

        # Verify output file
        output_folder = os.path.join(
            TEST_OUTPUT_FOLDER,
            os.path.splitext(TEST_FILE_NAME)[0],
        )
        output_file_path = os.path.join(
            output_folder,
            f"{os.path.splitext(TEST_FILE_NAME)[0]}_sentiment.txt",
        )
        assert os.path.exists(output_file_path), "Sentiment output file not created."

        # Display and validate the output
        with open(output_file_path, encoding="utf-8") as output_file:
            output_content = output_file.read()
            print("Sentiment Analysis Output:")
            print(output_content)
            assert (
                "Positive" in output_content
                or "Negative" in output_content
                or "Neutral" in output_content
            ), "Sentiment output does not contain valid sentiments."

        print("Test Passed!")
    finally:
        # Cleanup
        if os.path.exists(TEST_INPUT_FOLDER):
            shutil.rmtree(TEST_INPUT_FOLDER)
        if os.path.exists(TEST_OUTPUT_FOLDER):
            shutil.rmtree(TEST_OUTPUT_FOLDER)


if __name__ == "__main__":
    test_sentiment_analysis_hardcoded()
