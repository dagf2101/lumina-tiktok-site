#!/usr/bin/env python3
"""
Lumina — TikTok API Client
Handles token auto-refresh, profile inspection, and video publishing.
"""

import os
import time
import json
import urllib.parse
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(__file__)
ENV_PATH = os.path.join(BASE_DIR, ".env")
TOKENS_PATH = os.path.join(BASE_DIR, "tiktok_tokens.json")

def load_env():
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip("\"'")
    return env

def load_tokens():
    if not os.path.exists(TOKENS_PATH):
        raise FileNotFoundError(f"Tokens file not found: {TOKENS_PATH}. Run get_tiktok_tokens.py first.")
    with open(TOKENS_PATH, "r") as f:
        return json.load(f)

def save_tokens(tokens):
    with open(TOKENS_PATH, "w") as f:
        json.dump(tokens, f, indent=2)

def refresh_access_token():
    """Refreshes the access_token using the refresh_token (valid for 365 days)"""
    tokens = load_tokens()
    env = load_env()

    client_key = env.get("TIKTOK_CLIENT_KEY", tokens.get("client_key"))
    client_secret = env.get("TIKTOK_CLIENT_SECRET")
    refresh_token = tokens.get("refresh_token")

    if not client_secret:
        raise ValueError("TIKTOK_CLIENT_SECRET is missing from .env")
    if not refresh_token:
        raise ValueError("refresh_token is missing from tiktok_tokens.json")

    url = "https://open.tiktokapis.com/v2/oauth/token/"
    payload = urllib.parse.urlencode({
        "client_key": client_key,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )

    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))

    data = res.get("data", res)
    tokens["access_token"] = data["access_token"]
    tokens["refresh_token"] = data["refresh_token"]
    tokens["expires_in"] = data.get("expires_in", 86400)
    tokens["refresh_expires_in"] = data.get("refresh_expires_in", 31536000)
    tokens["updated_at"] = int(time.time())

    save_tokens(tokens)
    print("✓ Access token successfully refreshed!")
    return tokens["access_token"]

def get_user_profile():
    """Fetches user profile information using the current access_token"""
    tokens = load_tokens()
    access_token = tokens["access_token"]

    url = "https://open.tiktokapis.com/v2/user/info/?fields=open_id,union_id,avatar_url,display_name"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("Access token expired. Refreshing...")
            new_token = refresh_access_token()
            req = urllib.request.Request(
                url,
                headers={"Authorization": f"Bearer {new_token}"}
            )
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        raise

if __name__ == "__main__":
    profile = get_user_profile()
    print("Lumina TikTok Client Status: ACTIVE")
    print(json.dumps(profile, indent=2))
