from components.utils.token import calculate_token_usage


def test_calculate_token_usage():
    test_1 = "hello"
    test_2 = [
        {
            "role": "system",
            "content": "You are a skilled SQL query assistant specializing in MySQL SQL query",
        },
        {
            "role": "user",
            "content": "Please think step-by-step. Generate the MySQL sql query based on the question",
        },
    ]

    result_1 = calculate_token_usage(test_1)
    assert isinstance(result_1, int)
    assert result_1 > 0

    result_2 = calculate_token_usage(test_2)
    assert isinstance(result_2, int)
    assert result_2 > 0

    result_3 = calculate_token_usage(test_1, test_2)
    assert isinstance(result_3, int)
    assert result_3 > 0
    assert result_3 == result_1 + result_2

    result_4 = calculate_token_usage("")
    assert result_4 == 0
