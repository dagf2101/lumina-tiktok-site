#!/usr/bin/env python3
"""
Lumina — TikTok OAuth Token Retriever (Sandbox & Production)
"""

import os
import sys
import json
import urllib.parse
import urllib.request
import urllib.error

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
TOKENS_PATH = os.path.join(os.path.dirname(__file__), "tiktok_tokens.json")

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

def main():
    env = load_env()
    client_key = env.get("TIKTOK_CLIENT_KEY")
    client_secret = env.get("TIKTOK_CLIENT_SECRET")
    redirect_uri = env.get("TIKTOK_REDIRECT_URI", "https://dagf2101.github.io/lumina-tiktok-site/")

    if not client_key or not client_secret:
        print("❌ Erreur: TIKTOK_CLIENT_KEY ou TIKTOK_CLIENT_SECRET introuvable dans .env")
        sys.exit(1)

    print("=================================================================")
    print("      LUMINA — RÉCUPÉRATION DES TOKENS TIKTOK (OAUTH 2.0)        ")
    print("=================================================================")
    print(f"🔑 Client Key:    {client_key}")
    print(f"🌐 Redirect URI:  {redirect_uri}")
    print("-----------------------------------------------------------------")

    # Scopes
    scopes = "user.info.basic,video.upload,video.publish"
    
    # Generate Authorization URL
    params = {
        "client_key": client_key,
        "scope": scopes,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": "lumina_auth_state"
    }
    auth_url = f"https://www.tiktok.com/v2/auth/authorize/?{urllib.parse.urlencode(params)}"

    print("\n👉 ÉTAPE 1 : Ouvrez ce lien dans votre navigateur :")
    print(f"\n{auth_url}\n")
    print("-----------------------------------------------------------------")
    print("👉 ÉTAPE 2 : Autorisez Lumina avec votre compte testeur TikTok.")
    print("Vous allez être redirigé vers une URL contenant '?code=...'")
    print("-----------------------------------------------------------------")

    # Prompt user for code or full URL
    input_str = input("\n👉 ÉTAPE 3 : Collez ici l'URL complète de redirection ou le 'code' : ").strip()

    code = input_str
    if "code=" in input_str:
        # Extract code from URL query parameter
        parsed = urllib.parse.urlparse(input_str)
        q = urllib.parse.parse_qs(parsed.query)
        if "code" in q:
            code = q["code"][0]
        else:
            # Maybe in fragment or raw string
            code = input_str.split("code=")[1].split("&")[0]

    if not code:
        print("❌ Code d'autorisation invalide.")
        sys.exit(1)

    print(f"\n⏳ Échange du code contre les tokens auprès de TikTok...")

    # Exchange code for tokens
    token_endpoint = "https://open.tiktokapis.com/v2/oauth/token/"
    payload = urllib.parse.urlencode({
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }).encode("utf-8")

    req = urllib.request.Request(
        token_endpoint,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"\n❌ Erreur API TikTok ({e.code}) :")
        print(err_body)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur réseau : {e}")
        sys.exit(1)

    if resp_data.get("error") and resp_data["error"].get("code") != "ok" and resp_data["error"].get("code") != 0:
        print("\n❌ Erreur retournée par TikTok :")
        print(json.dumps(resp_data, indent=2))
        sys.exit(1)

    data = resp_data.get("data", resp_data)

    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    open_id = data.get("open_id")
    expires_in = data.get("expires_in")
    refresh_expires_in = data.get("refresh_expires_in")

    if not access_token:
        print("\n❌ Pas de token reçu :")
        print(json.dumps(resp_data, indent=2))
        sys.exit(1)

    # Save tokens to local file
    tokens_payload = {
        "client_key": client_key,
        "open_id": open_id,
        "access_token": access_token,
        "expires_in": expires_in,
        "refresh_token": refresh_token,
        "refresh_expires_in": refresh_expires_in,
        "scope": data.get("scope")
    }

    with open(TOKENS_PATH, "w") as f:
        json.dump(tokens_payload, f, indent=2)

    print("\n" + "="*65)
    print("       🎉 TOKENS TIKTOK RÉCUPÉRÉS AVEC SUCCÈS !        ")
    print("="*65)
    print(f"✓ Open ID :          {open_id}")
    print(f"✓ Access Token :     {access_token[:15]}... (valable {expires_in} sec / ~24h)")
    print(f"✓ Refresh Token :    {refresh_token[:15]}... (valable {refresh_expires_in} sec / ~365j)")
    print(f"✓ Fichier sauvé :    {TOKENS_PATH}")
    print("="*65)

    # Test user info call
    print("\n🔍 Test de récupération du profil TikTok avec l'access_token...")
    user_req = urllib.request.Request(
        "https://open.tiktokapis.com/v2/user/info/?fields=open_id,union_id,avatar_url,display_name",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    try:
        with urllib.request.urlopen(user_req) as uresp:
            user_info = json.loads(uresp.read().decode("utf-8"))
            print("✓ Profil connecté :")
            print(json.dumps(user_info, indent=2))
    except Exception as e:
        print(f"ℹ️ Info profil (optionnel) : {e}")

if __name__ == "__main__":
    main()
