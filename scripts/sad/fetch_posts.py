import requests
import json
import os
from datetime import datetime

# Bot Configuration
BOT_TOKEN = "8148088456:AAHQVENaU_AJFTbJMtqpnFysTXK8UN2ku8g"
CHANNEL_ID = "2464314362"
LAST_UPDATE_ID = 0

def ensure_folder_exists(folder_path):
    """Ensure directory exists"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def download_image(file_id, folder_path):
    """Download image from Telegram"""
    try:
        # Get file path from Telegram
        file_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
        file_response = requests.get(file_url)
        file_response.raise_for_status()
        file_path = file_response.json()["result"]["file_path"]
        
        # Download image
        image_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        
        # Save image
        image_name = f"{file_id}.jpg"
        image_path = os.path.join(folder_path, image_name)
        
        with open(image_path, "wb") as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                out_file.write(chunk)
        
        return f"posts_data/sad/images/{image_name}"
    
    except Exception as e:
        print(f"Error downloading image: {e}")
        return ""

def load_last_update_id():
    """Load last update ID from file"""
    try:
        with open(f"update_tracking/sad_last_id.txt", "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def save_last_update_id(update_id):
    """Save last update ID to file"""
    ensure_folder_exists("update_tracking")
    with open(f"update_tracking/sad_last_id.txt", "w") as f:
        f.write(str(update_id))

def fetch_posts():
    """Fetch new posts from channel"""
    global LAST_UPDATE_ID
    LAST_UPDATE_ID = load_last_update_id()
    
    try:
        ensure_folder_exists(f"posts_data/sad/images")
        
        # Get new updates
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={LAST_UPDATE_ID + 1}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("ok", False):
            print("Failed to get updates:", data.get("description", "Unknown error"))
            return
        
        posts = []
        new_updates = False
        
        for update in data.get("result", []):
            if "channel_post" in update:
                chat_id = str(update["channel_post"]["chat"]["id"])
                if chat_id == CHANNEL_ID:
                    new_updates = True
                    LAST_UPDATE_ID = max(LAST_UPDATE_ID, update["update_id"])
                    
                    # Skip media-only posts
                    has_photo = "photo" in update["channel_post"]
                    has_text = "text" in update["channel_post"]
                    has_caption = "caption" in update["channel_post"]
                    
                    if has_photo and not (has_text or has_caption):
                        continue
                    
                    post = {
                        "text": "",
                        "image": "",
                        "date": datetime.fromtimestamp(update["channel_post"]["date"]).strftime("%d/%m/%Y"),
                        "copy_text": "",
                        "type": "حزين"
                    }
                    
                    # Get text content
                    if has_text:
                        post["text"] = update["channel_post"]["text"]
                        post["copy_text"] = post["text"]
                    elif has_caption:
                        post["text"] = update["channel_post"]["caption"]
                        post["copy_text"] = post["text"]
                    
                    # Download image if exists
                    if (has_text or has_caption) and has_photo:
                        file_id = update["channel_post"]["photo"][-1]["file_id"]
                        image_path = download_image(file_id, f"posts_data/sad/images")
                        if image_path:
                            post["image"] = image_path
                    
                    # Add post if has content
                    if post["text"]:
                        posts.append(post)
        
        if new_updates:
            save_last_update_id(LAST_UPDATE_ID)
            
            # Read existing posts
            existing_posts = []
            try:
                with open(f"posts_data/sad/posts.json", "r", encoding="utf-8") as f:
                    existing_posts = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            
            # Merge posts
            updated_posts = posts + existing_posts
            
            # Save to file
            with open(f"posts_data/sad/posts.json", "w", encoding="utf-8") as f:
                json.dump(updated_posts, f, ensure_ascii=False, indent=4)
            
            print(f"Added {len(posts)} new posts")
        else:
            print("No new posts found")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    fetch_posts()
