def standardize_tweets(tweets, source):
    standardized_results = []

    if source == "tweepy":
        for tweet in tweets:
            standardized_results.append(
                {
                    "id": tweet["id"],
                    "text": tweet["text"],
                    "author_id": tweet["author_id"],
                    "username": tweet.get("username", None),
                    "created_at": tweet["created_at"],
                    "url": None,
                    "retweet_count": None,
                    "reply_count": None,
                    "like_count": None,
                    "quote_count": None,
                    "bookmark_count": None,
                    "is_retweet": None,
                    "is_quote": None,
                }
            )

    elif source == "apify":
        for tweet in tweets:
            standardized_results.append(
                {
                    "id": tweet["id"],
                    "text": tweet["text"],
                    "author_id": None,
                    "username": None,
                    "created_at": tweet["createdAt"],
                    "url": tweet["url"],
                    "retweet_count": tweet["retweetCount"],
                    "reply_count": tweet["replyCount"],
                    "like_count": tweet["likeCount"],
                    "quote_count": tweet["quoteCount"],
                    "bookmark_count": tweet["bookmarkCount"],
                    "is_retweet": tweet["isRetweet"],
                    "is_quote": tweet["isQuotes"],
                }
            )

    else:
        raise ValueError("Unsupported source. Use 'tweepy' or 'apify'.")

    return standardized_results


def standardize_profile(user_detail, source):
    if source == "tweepy":
        return {
            "id": user_detail["user_id"],
            "name": user_detail["name"],
            "username": user_detail["username"],
            "description": None,  # Tweepy does not provide description
            "location": None,  # Tweepy does not provide location
            "profile_picture": None,  # Tweepy does not provide profile picture
            "cover_picture": None,  # Tweepy does not provide cover picture
            "status": None,  # Tweepy does not provide status
            "is_verified": None,  # Tweepy does not provide verification info
            "created_at": user_detail["created_at"],
            "followers": user_detail["followers"],
            "following": user_detail["following"],
        }

    elif source == "apify":
        return {
            "id": user_detail["id"],
            "name": user_detail["name"],
            "username": user_detail["userName"],
            "description": user_detail.get("description", None),
            "location": user_detail.get("location", None),
            "profile_picture": user_detail.get("profilePicture", None),
            "cover_picture": user_detail.get("coverPicture", None),
            "status": user_detail.get("status", None),
            "is_verified": user_detail.get("isVerified", None),
            "created_at": None,  # Apify does not provide account creation date
            "followers": user_detail["followers"],
            "following": user_detail["following"],
        }

    else:
        raise ValueError("Unsupported source. Use 'tweepy' or 'apify'.")
