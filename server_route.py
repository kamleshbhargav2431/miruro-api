import base64, json, gzip, httpx
from fastapi import APIRouter, HTTPException

router = APIRouter()

MIRURO_API_BASE = "https://mirouapi.45.43.92.254.sslip.io"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.miruro.online/",
}

PROVIDER_NAMES = {
    "arc":  "AnimeKai",
    "dune": "AnimeDunya",
    "kiwi": "AnimePahe",
    "zoro": "AniWatch",
    "bee":  "AniKoto",
    "jet":  "AnimeJet",
}


@router.get("/api/server/{provider}/{anilist_id}/{episode_number}")
async def get_server(provider: str, anilist_id: int, episode_number: int):
    """
    Returns sub + dub servers for a specific provider/episode.
    Response matches exactly what server.php expects:
    {
      "success": true,
      "results": [
        { "type": "sub", "serverName": "AniWatch", "server_id": "1" },
        { "type": "dub", "serverName": "AniWatch", "server_id": "2" }
      ]
    }
    """

    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(
            f"{MIRURO_API_BASE}/episodes/{anilist_id}",
            headers=HEADERS,
        )

    if res.status_code != 200:
        return {"success": False, "error": f"Upstream returned {res.status_code}", "results": []}

    try:
        data = res.json()
    except Exception:
        return {"success": False, "error": "Invalid JSON from upstream", "results": []}

    provider_data = data.get("providers", {}).get(provider)
    if not provider_data:
        available = list(data.get("providers", {}).keys())
        return {
            "success": False,
            "error": f"Provider '{provider}' not found. Available: {available}",
            "results": []
        }

    server_name = PROVIDER_NAMES.get(provider, provider.capitalize())
    results = []
    server_id_counter = 1

    for category in ["sub", "dub"]:
        ep_list = provider_data.get("episodes", {}).get(category, [])
        if not ep_list:
            continue

        match = next((ep for ep in ep_list if ep.get("number") == episode_number), None)
        if not match:
            continue

        results.append({
            "type": category,
            "serverName": server_name,
            "server_id": str(server_id_counter),
        })
        server_id_counter += 1

    if not results:
        return {
            "success": False,
            "error": f"No servers found for episode {episode_number}",
            "results": []
        }

    return {
        "success": True,
        "results": results,
    }
