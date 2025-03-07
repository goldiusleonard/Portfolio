from datetime import datetime, timezone

def convert_timestamp_to_utc(created_at):
    if isinstance(created_at, int) and created_at > 0:
        utc_time = datetime.fromtimestamp(created_at, tz=timezone.utc)
        formatted_time = (
            utc_time.strftime("%Y-%m-%dT%H:%M:%S.")
            + f"{utc_time.microsecond // 1000:03d}Z"
        )
    else:
        formatted_time = created_at
    return formatted_time

def extract_fields_from_instaloader_for_comments(data):
    extracted_comments = []

    for comment in data:
        created_at = comment.get("created_at", 0)

        updated_comment = {
            "id": comment.get("id", ""),
            "created_at": convert_timestamp_to_utc(created_at),
            "text": comment.get("text", ""),
            "owner": comment.get("owner", {}),
            "likes_count": comment.get("likes_count", 0),
            "replies": [],
        }

        if "answers" in comment:
            updated_comment["replies"] = []
            for reply in comment.get("answers", []):
                reply_data = {
                    "id": reply.get("id", ""),
                    "created_at": convert_timestamp_to_utc(reply.get("created_at", 0)),
                    "text": reply.get("text", ""),
                    "owner": {
                        "id": reply.get("owner", {}).get("id", ""),
                        "username": reply.get("owner", {}).get("username", ""),
                        "profile_pic_url": reply.get("owner", {}).get(
                            "profile_pic_url", ""
                        ),
                        "is_verified": reply.get("owner", {}).get("is_verified", False),
                    },
                    "likes_count": reply.get("likesCount", 0),
                }
                updated_comment["replies"].append(reply_data)

        extracted_comments.append(updated_comment)

    return extracted_comments

def extract_fields_from_apify_for_comments(data):
    extracted_comments = []

    comments_data = data.get("latestComments", [])

    for comment in comments_data:
        comment_info = {
            "id": comment.get("id", ""),
            "created_at": comment.get("timestamp", ""),
            "text": comment.get("text", ""),
            "owner": {
                "id": comment.get("owner", {}).get("id", ""),
                "is_verified": comment.get("owner", {}).get("is_verified", False),
                "profile_pic_url": comment.get("owner", {}).get("profile_pic_url", ""),
                "username": comment.get("owner", {}).get("username", ""),
            },
            "likes_count": comment.get("likesCount", 0),
            "replies": [],
        }

        if comment.get("repliesCount", 0) > 0:
            for reply in comment.get("replies", []):
                reply_data = {
                    "id": reply.get("id", ""),
                    "created_at": reply.get("timestamp", ""),
                    "text": reply.get("text", ""),
                    "owner": {
                        "id": reply.get("owner", {}).get("id", ""),
                        "is_verified": reply.get("owner", {}).get("is_verified", False),
                        "profile_pic_url": reply.get("owner", {}).get(
                            "profile_pic_url", ""
                        ),
                        "username": reply.get("owner", {}).get("username", ""),
                    },
                    "likes_count": reply.get("likesCount", 0),
                }
                comment_info["replies"].append(reply_data)

        extracted_comments.append(comment_info)

    return extracted_comments