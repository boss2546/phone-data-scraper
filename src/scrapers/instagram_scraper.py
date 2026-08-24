import urllib.request
import json
from typing import Dict, Any, Optional
from config.settings import DEFAULT_HEADERS

class InstagramScraper:
    """Scraper สำหรับดึงข้อมูลโปรไฟล์และโพสต์จาก Instagram ผ่าน Internal Web API"""

    API_URL = "https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    APP_ID = "936619743392459"  # Instagram Public Web App ID

    def __init__(self):
        self.headers = {
            **DEFAULT_HEADERS,
            "X-IG-App-ID": self.APP_ID,
            "Accept": "*/*",
            "Sec-Fetch-Site": "same-origin"
        }

    def fetch_profile_and_posts(self, username_or_url: str) -> Dict[str, Any]:
        """
        ดึงข้อมูลโปรไฟล์ + โพสต์ล่าสุดทั้งหมดของบัญชี Instagram
        """
        # สกัด username ออกจาก URL (ถ้าผู้ใช้ส่งมาเป็น URL)
        username = username_or_url.strip().rstrip("/").split("/")[-1].replace("@", "")
        
        url = self.API_URL.format(username=username)
        req = urllib.request.Request(url, headers={**self.headers, "Referer": f"https://www.instagram.com/{username}/"})

        try:
            with urllib.request.urlopen(req, timeout=12) as res:
                raw = json.loads(res.read().decode("utf-8"))
        except Exception as e:
            return {
                "status": "error",
                "message": f"ไม่สามารถยิง API ของ Instagram ได้: {str(e)}",
                "username": username
            }

        user_data = raw.get("data", {}).get("user", {})
        if not user_data:
            return {"status": "error", "message": "ไม่พบบัญชีผู้ใช้นี้", "username": username}

        # สรุปข้อมูลโปรไฟล์
        profile = {
            "username": user_data.get("username"),
            "full_name": user_data.get("full_name"),
            "biography": user_data.get("biography"),
            "followers": user_data.get("edge_followed_by", {}).get("count"),
            "following": user_data.get("edge_follow", {}).get("count"),
            "total_posts": user_data.get("edge_owner_to_timeline_media", {}).get("count"),
            "profile_pic_url": user_data.get("profile_pic_url_hd") or user_data.get("profile_pic_url"),
            "is_verified": user_data.get("is_verified")
        }

        # สกัดข้อมูลโพสต์ล่าสุด
        timeline_edges = user_data.get("edge_owner_to_timeline_media", {}).get("edges", [])
        posts = []

        for edge in timeline_edges:
            node = edge.get("node", {})
            caption = ""
            caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
            if caption_edges:
                caption = caption_edges[0].get("node", {}).get("text", "")

            # ดึงรูปภาพทั้งหมด (รองรับรูปเดี่ยวและอัลบั้มหลายรูป GraphSidecar)
            images = [node.get("display_url")]
            sidecar_edges = node.get("edge_sidecar_to_children", {}).get("edges", [])
            if sidecar_edges:
                images = [child.get("node", {}).get("display_url") for child in sidecar_edges if child.get("node", {}).get("display_url")]

            shortcode = node.get("shortcode")
            posts.append({
                "post_id": node.get("id"),
                "shortcode": shortcode,
                "url": f"https://www.instagram.com/p/{shortcode}/",
                "type": node.get("__typename"),
                "caption": caption,
                "likes": node.get("edge_liked_by", {}).get("count"),
                "comments": node.get("edge_media_to_comment", {}).get("count"),
                "images_count": len(images),
                "images": images,
                "timestamp": node.get("taken_at_timestamp")
            })

        return {
            "status": "success",
            "profile": profile,
            "posts_count": len(posts),
            "posts": posts
        }
