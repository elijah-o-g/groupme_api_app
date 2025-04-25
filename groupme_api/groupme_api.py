#!/usr/bin/env python3
"""
GroupMe Scraper Tool

- Lists all group chats for a user
- Prompts for a group to analyze
- Detects aggressive messages
- Downloads unique images from a specified time range
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

import openai
from exceptions import (
    AggressionAnalysisError,
    GroupSelectionError,
    ImageDownloadError,
    MessageFetchError,
    OpenAIServiceError,
    TokenMissingError,
)

openai.api_key = os.getenv("OPENAI_API_KEY")

import requests

# -------------------------------
# Configuration
# -------------------------------
AGGRESSIVE_WORDS = {"hate", "kill", "stupid", "shut up", "dumb", "idiot"}
DOWNLOAD_DIR = "downloads"
MAX_MESSAGES = 10000
LOG_FILE = "groupme_scraper.log"

logging.basicConfig(
    filename=LOG_FILE, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# -------------------------------
# Core Functions
# -------------------------------


def get_token() -> str:
    """Prompt the user for a GroupMe token if not set."""
    token = os.getenv("GROUPME_TOKEN")
    if not token:
        token = input("🔐 Enter your GroupMe access token: ").strip()
    if not token:
        raise TokenMissingError("Missing GroupMe token.")
    return token


def fetch_groups(token: str) -> list[dict[str, Any]]:
    """Fetch the user's group chats."""
    url = f"https://api.groupme.com/v3/groups?token={token}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json().get("response", [])


def list_groups(groups: list[dict[str, Any]]) -> None:
    """Print all group chat names."""
    print("\n📋 Available Group Chats:")
    for i, group in enumerate(groups):
        print(f"  [{i}] {group['name']} ({len(group['members'])} members)")


def select_group(groups: list[dict[str, Any]]) -> dict[str, Any]:
    """Prompt user to select a group."""
    try:
        idx = int(input("\n👉 Enter the index of the group to analyze: "))
        return groups[idx]
    except (ValueError, IndexError):
        raise GroupSelectionError("Invalid group selection.")


def fetch_all_messages(token: str, group_id: str) -> list[dict[str, Any]]:
    """Fetch messages from a group using pagination."""
    messages = []
    before_id = None

    try:
        while len(messages) < MAX_MESSAGES:
            url = f"https://api.groupme.com/v3/groups/{group_id}/messages?token={token}&limit=100"
            if before_id:
                url += f"&before_id={before_id}"

            resp = requests.get(url)
            resp.raise_for_status()
            batch = resp.json()["response"]["messages"]

            if not batch:
                break

            messages.extend(batch)
            before_id = batch[-1]["id"]
    except Exception as e:
        raise MessageFetchError(f"Failed to fetch messages: {e}")

    return messages


def is_aggressive(text: str) -> bool:
    """Uses GPT to classify aggression."""
    try:
        # ... same prompt logic
        ...
    except Exception as e:
        raise OpenAIServiceError(f"OpenAI classification failed: {e}")


def find_aggressive_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Use OpenAI to detect aggression in messages."""
    flagged = []
    for msg in messages:
        text = msg.get("text", "")
        if text and is_aggressive(text):
            flagged.append(msg)
    return flagged


def find_aggressive_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return messages containing aggressive language."""
    return [
        msg
        for msg in messages
        if msg.get("text") and any(word in msg["text"].lower() for word in AGGRESSIVE_WORDS)
    ]


def download_images(
    messages: list[dict[str, Any]], group_name: str, start: datetime, end: datetime
) -> None:
    """Download unique image attachments from messages in a time range."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    group_dir = os.path.join(DOWNLOAD_DIR, group_name.replace(" ", "_"))
    os.makedirs(group_dir, exist_ok=True)

    record_file = os.path.join(group_dir, "downloaded.json")
    downloaded: set[str] = set()
    if os.path.exists(record_file):
        with open(record_file, "r") as f:
            downloaded = set(json.load(f))

    count = 0
    for msg in messages:
        created_at = datetime.fromtimestamp(msg["created_at"])
        if not (start <= created_at <= end):
            continue

        for attachment in msg.get("attachments", []):
            if attachment["type"] == "image":
                img_url = attachment["url"]
                img_id = img_url.split("/")[-1]
                if img_id in downloaded:
                    continue

                img_path = os.path.join(group_dir, img_id + ".jpg")
                try:
                    img_data = requests.get(img_url)
                    with open(img_path, "wb") as f:
                        f.write(img_data.content)
                    downloaded.add(img_id)
                    count += 1
                except Exception as e:
                    logging.warning(f"Failed to download image: {e}")

    with open(record_file, "w") as f:
        json.dump(list(downloaded), f)

    print(f"📸 Downloaded {count} new images to '{group_dir}'")


def prompt_date_range() -> tuple[datetime, datetime]:
    """Prompt the user for a start and end date."""
    fmt = "%Y-%m-%d"
    start_str = input("📅 Start date (YYYY-MM-DD): ")
    end_str = input("📅 End date   (YYYY-MM-DD): ")

    return datetime.strptime(start_str, fmt), datetime.strptime(end_str, fmt)


def main() -> None:
    try:
        token = get_token()
        groups = fetch_groups(token)
        list_groups(groups)

        group = select_group(groups)
        messages = fetch_all_messages(token, group["id"])

        print("🧠 Scanning for aggressive messages...")
        aggressive = find_aggressive_messages(messages)
        print(f"⚠️  Found {len(aggressive)} aggressive messages.")
        for msg in aggressive[:10]:
            print(f"- {msg['name']}: {msg.get('text', '')}")

        start, end = prompt_date_range()
        print("📥 Downloading images...")
        download_images(messages, group["name"], start, end)

        print("✅ Done.")
    except GroupMeScraperError as e:
        print(f"🚨 Error: {e}")
        logging.error(e)
    except KeyboardInterrupt:
        print("\n🛑 Aborted by user.")


if __name__ == "__main__":
    main()
