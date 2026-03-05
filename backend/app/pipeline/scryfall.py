import httpx
import asyncio
from dataclasses import dataclass
from typing import Optional

SCRYFALL_BASE = "https://api.scryfall.com"

@dataclass
class ScryfallResult:
    scryfall_id: str
    name: str
    colors: list[str]
    color_identity: list[str]
    type_line: str
    mana_cost: str
    oracle_text: str
    image_url: Optional[str]

async def lookup_card(name: str) -> Optional[ScryfallResult]:
    """Fuzzy-lookup a card by name on Scryfall. Returns None if not found."""
    await asyncio.sleep(0.1)  # respect Scryfall rate limit
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SCRYFALL_BASE}/cards/named",
            params={"fuzzy": name},
            timeout=10.0,
        )
    if resp.status_code != 200:
        return None

    data = resp.json()
    # Handle double-faced cards (image is on card_faces[0])
    image_uris = data.get("image_uris") or (
        data.get("card_faces", [{}])[0].get("image_uris", {})
    )
    return ScryfallResult(
        scryfall_id=data["id"],
        name=data["name"],
        colors=data.get("colors", []),
        color_identity=data.get("color_identity", []),
        type_line=data.get("type_line", ""),
        mana_cost=data.get("mana_cost", ""),
        oracle_text=data.get("oracle_text", ""),
        image_url=image_uris.get("normal"),
    )
