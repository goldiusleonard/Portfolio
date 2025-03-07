from datetime import datetime, timezone

def extract_fields_from_instaloader_for_post(data):
    return {
        "id": data.get("node", {}).get("id", ""),
        "shortCode": data.get("node", {}).get("shortcode", ""),
        "caption": data.get("node", {}).get("caption", "") or "",
        "commentsCount": data.get("node", {})
        .get("iphone_struct", {})
        .get("comment_count", 0),
        "dimensionsHeight": data.get("node", {})
        .get("iphone_struct", {})
        .get("original_height", 0),
        "dimensionsWidth": data.get("node", {})
        .get("iphone_struct", {})
        .get("original_width", 0),
        "displayUrl": data.get("node", {})
        .get("iphone_struct", {})
        .get("display_uri", ""),
        "likesCount": data.get("node", {})
        .get("iphone_struct", {})
        .get("like_count", 0),
        "timestamp": datetime.fromtimestamp(
            data.get("node", {}).get("date", 0), tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "owner": {
            "id": data.get("node", {}).get("owner", {}).get("id", ""),
            "username": data.get("node", {}).get("owner", {}).get("username", ""),
            "full_name": data.get("node", {}).get("owner", {}).get("full_name", ""),
        },
        "usertags": [
            {
                "full_name": user.get("user", {}).get("full_name", ""),
                "id": user.get("user", {}).get("id", ""),
                "is_verified": user.get("user", {}).get("is_verified", False),
                "profile_pic_url": user.get("user", {}).get("profile_pic_url", ""),
                "username": user.get("user", {}).get("username", ""),
            }
            for user in (
                data.get("node", {})
                .get("iphone_struct", {})
                .get("usertags", {})
                .get("in", [])
                if data.get("node", {}).get("iphone_struct", {}).get("usertags")
                else []
            )
        ],
        "child_posts": [
            {
                "id": user.get("id", ""),
                "displayUrl": user.get("image_versions2", {})
                .get("candidates", [])[0]
                .get("url", ""),
            }
            for user in (
                data.get("node", {}).get("iphone_struct", {}).get("carousel_media", [])
                if data.get("node", {}).get("iphone_struct", {}).get("carousel_media")
                else []
            )
        ],
    }

def extract_fields_from_apify_for_post(data):
    return {
        "id": data.get("id", ""),
        "shortCode": data.get("shortCode", ""),
        "caption": data.get("caption", ""),
        "commentsCount": data.get("commentsCount", 0),
        "dimensionsHeight": data.get("dimensionsHeight", 0),
        "dimensionsWidth": data.get("dimensionsWidth", 0),
        "displayUrl": data.get("displayUrl", ""),
        "likesCount": data.get("likesCount", 0),
        "timestamp": data.get("timestamp", ""),
        "owner": {
            "id": data.get("ownerId", ""),
            "username": data.get("ownerUsername", ""),
            "full_name": data.get("ownerFullName", ""),
        },
        "usertags": data.get("taggedUsers", ""),
        "child_posts": [
            {"id": child.get("id", ""), "displayUrl": child.get("displayUrl", "")}
            for child in data.get("childPosts", [])
        ],
    }

def extract_fields_from_apify_for_post_url(data):
    return [
        post.get("url", "")
        for index, post in enumerate(data.get("topPosts", []))
        if index < 28
    ]