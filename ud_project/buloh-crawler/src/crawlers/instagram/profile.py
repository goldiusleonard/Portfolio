def extract_fields_from_apify_for_profile(data: dict):
    return {
        "id": data.get("id"),
        "username": data.get("username"),
        "fullName": data.get("fullName"),
        "biography": data.get("biography"),
        "followersCount": data.get("followersCount", 0),
        "followsCount": data.get("followsCount", 0),
        "hasChannel": data.get("hasChannel"),
        "highlightReelCount": data.get("highlightReelCount"),
        "isBusinessAccount": data.get("isBusinessAccount"),
        "joinedRecently": data.get("joinedRecently"),
        "businessCategoryName": data.get("businessCategoryName"),
        "private": data.get("private"),
        "verified": data.get("verified"),
        "profilePicUrl": data.get("profilePicUrl"),
        "profilePicUrlHD": data.get("profilePicUrlHD"),
    }

def extract_fields_from_instaloader_for_profile(data: dict):
    return {
        "id": data["node"].get("id"),
        "username": data["node"].get("username"),
        "fullName": data["node"].get("full_name"),
        "biography": data["node"].get("biography"),
        "followersCount": data["node"].get("edge_followed_by", {}).get("count", 0),
        "followsCount": data["node"].get("edge_follow", {}).get("count", 0),
        "hasChannel": data["node"].get("has_channel"),
        "highlightReelCount": data["node"].get("highlight_reel_count"),
        "isBusinessAccount": data["node"].get("is_business_account"),
        "joinedRecently": data["node"].get("is_joined_recently"),
        "businessCategoryName": data["node"].get("business_category_name"),
        "private": data["node"].get("is_private"),
        "verified": data["node"].get("is_verified"),
        "profilePicUrl": data["node"].get("profile_pic_url"),
        "profilePicUrlHD": data["node"].get("profile_pic_url_hd"),
    }

def extract_fields_from_apify_for_profile_url(data):
    return data.get("inputUrl", "")