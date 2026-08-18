"""One-shot generator: scrapes chefsimon.com for French recipes with images.

Run once during development to produce:
  app/scripts/demo_recipes/recipes.json
  app/scripts/demo_recipes/images/<hex32>.jpg       (full-size, ≤2000 px)
  app/scripts/demo_recipes/images/thumb_<hex32>.jpg (400 px thumbnail)

Usage:
  uv run python -m app.scripts.build_demo_recipes

Requires: httpx, Pillow (both in project deps).
"""

import io
import json
import re
import time
import uuid
from pathlib import Path

import httpx
from PIL import Image

# ── Config ────────────────────────────────────────────────────────────────────

TARGET = 50
OUT_DIR = Path(__file__).parent / "demo_recipes"
IMAGES_DIR = OUT_DIR / "images"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# French unit abbreviation → canonical English name (must match AmountUnit.name in DB)
UNIT_MAP: list[tuple[str, str]] = sorted(
    [
        ("cuillères à soupe", "tablespoon"),
        ("cuillère à soupe", "tablespoon"),
        ("cuilleres a soupe", "tablespoon"),
        ("cuillères à café", "teaspoon"),
        ("cuillère à café", "teaspoon"),
        ("cuilleres a cafe", "teaspoon"),
        ("c. à soupe", "tablespoon"),
        ("c.à soupe", "tablespoon"),
        ("c. à café", "teaspoon"),
        ("c.à café", "teaspoon"),
        ("c.a.soupe", "tablespoon"),
        ("c.a.cafe", "teaspoon"),
        ("tasses", "cup"),
        ("tasse", "cup"),
        ("pincées", "pinch"),
        ("pincée", "pinch"),
        ("pincee", "pinch"),
        ("grammes", "gram"),
        ("gramme", "gram"),
        ("kilos", "kilogram"),
        ("kilo", "kilogram"),
        ("litres", "liter"),
        ("litre", "liter"),
        ("kg", "kilogram"),
        ("ml", "milliliter"),
        ("cl", "centiliter"),
        ("dl", "deciliter"),
        ("gr", "gram"),
        ("g", "gram"),
        ("l", "liter"),
    ],
    key=lambda x: -len(x[0]),  # longest first to avoid partial matches
)

TYPE_KEYWORDS: list[tuple[str, str]] = [
    ("milkshake", "Beverage"),
    ("boisson", "Beverage"),
    ("cocktail", "Beverage"),
    ("jus ", "Beverage"),
    ("smoothie", "Beverage"),
    ("soupe", "Soup"),
    ("potage", "Soup"),
    ("velouté", "Soup"),
    ("bouillon", "Soup"),
    ("salade", "Salad"),
    ("tarte", "Dessert"),
    ("gâteau", "Dessert"),
    ("gateau", "Dessert"),
    ("cake", "Dessert"),
    ("mousse", "Dessert"),
    ("crème dessert", "Dessert"),
    ("dessert", "Dessert"),
    ("sorbet", "Dessert"),
    ("glace", "Dessert"),
    ("macaron", "Dessert"),
    ("biscuit", "Dessert"),
    ("cookie", "Dessert"),
    ("muffin", "Dessert"),
    ("brownie", "Dessert"),
    ("ganache", "Dessert"),
    ("sauce", "Sauce"),
    ("vinaigrette", "Sauce"),
    ("entrée", "Starter"),
    ("amuse", "Starter"),
    ("apéritif", "Starter"),
    ("toast", "Starter"),
    ("tartine", "Starter"),
    ("verrines", "Starter"),
    ("petit-déjeuner", "Breakfast"),
    ("pancake", "Breakfast"),
    ("pain perdu", "Breakfast"),
    ("accompagnement", "Side dish"),
    ("gratin", "Side dish"),
]


# ── Parsing helpers ───────────────────────────────────────────────────────────


def find_json_ld_recipe(html: str) -> dict | None:
    for raw in re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    ):
        try:
            data = json.loads(raw.strip())
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("@type") == "Recipe":
                    return item
        elif isinstance(data, dict) and data.get("@type") == "Recipe":
            return data
    return None


def find_recipe_urls(html: str) -> list[str]:
    return list(
        dict.fromkeys(
            re.findall(
                r'https://chefsimon\.com/gourmets/([^"\'>\s/]+)/recettes/([^"\'>\s?#]+)',
                html,
            )
        )
    )


def gourmet_names_from_html(html: str) -> list[str]:
    return list(
        dict.fromkeys(
            m[0]
            for m in re.findall(
                r'https://chefsimon\.com/gourmets/([^"\'>\s/]+)/recettes/([^"\'>\s?#]+)',
                html,
            )
        )
    )


def parse_iso_duration(s: str | None) -> int | None:
    if not s:
        return None
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", str(s))
    if not m:
        return None
    total = int(m.group(1) or 0) * 60 + int(m.group(2) or 0)
    return total or None


def guess_type(title: str, description: str | None) -> str:
    text = (title + " " + (description or "")).lower()
    for kw, rtype in TYPE_KEYWORDS:
        if kw in text:
            return rtype
    return "Main course"


def parse_ingredient(raw: str) -> dict | None:
    raw = raw.strip().replace(",", ".")
    if not raw:
        return None
    for fr_unit, en_unit in UNIT_MAP:
        pat = rf"^(\d+(?:\.\d+)?)\s*{re.escape(fr_unit)}\s*(?:de\s+)?(.+)$"
        m = re.match(pat, raw, re.IGNORECASE)
        if m:
            name = m.group(2).strip().rstrip(".")
            return {"name": name, "amount": float(m.group(1)), "unit_name": en_unit}
    m = re.match(r"^(\d+(?:\.\d+)?)\s+(?:de\s+)?(.+)$", raw, re.IGNORECASE)
    if m:
        return {
            "name": m.group(2).strip().rstrip("."),
            "amount": float(m.group(1)),
            "unit_name": "piece",
        }
    return {"name": raw.rstrip("."), "amount": 1.0, "unit_name": "piece"}


def parse_steps(instructions) -> list[str]:
    result = []
    if isinstance(instructions, str):
        result = [s.strip() for s in instructions.split("\n") if s.strip()]
    elif isinstance(instructions, list):
        for item in instructions:
            text = item.get("text", "").strip() if isinstance(item, dict) else str(item).strip()
            if text:
                result.append(text)
    return result


def get_image_url(ld: dict) -> str | None:
    img = ld.get("image")
    if isinstance(img, str):
        return img
    if isinstance(img, list) and img:
        first = img[0]
        return first if isinstance(first, str) else (first or {}).get("url")
    if isinstance(img, dict):
        return img.get("url")
    return None


def parse_servings(val) -> int | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    m = re.search(r"\d+", str(val))
    return int(m.group()) if m else None


def save_image(client: httpx.Client, url: str, stem: str) -> bool:
    try:
        r = client.get(url, timeout=20, follow_redirects=True)
        r.raise_for_status()
        raw = r.content
        img = Image.open(io.BytesIO(raw))
        img.verify()
        img = Image.open(io.BytesIO(raw)).convert("RGB")

        orig = img.copy()
        if max(orig.size) > 2000:
            orig.thumbnail((2000, 2000), Image.LANCZOS)
        orig.save(IMAGES_DIR / f"{stem}.jpg", format="JPEG", quality=85, optimize=True)

        thumb = img.copy()
        thumb.thumbnail((400, 400), Image.LANCZOS)
        thumb.save(IMAGES_DIR / f"thumb_{stem}.jpg", format="JPEG", quality=80, optimize=True)
        return True
    except Exception as exc:
        print(f"    [img error] {exc}")
        return False


# ── Discovery ─────────────────────────────────────────────────────────────────

# Tag pages serve server-side HTML with recipe links — no JS rendering needed.
DISCOVERY_TAGS = [
    "poulet",
    "boeuf",
    "poisson",
    "chocolat",
    "fromage",
    "agneau",
    "porc",
    "dessert",
    "soupe",
    "pates",
    "riz",
    "legumes",
    "salade",
    "tarte",
    "sauce",
]


def collect_candidate_urls(client: httpx.Client) -> list[tuple[str, str]]:
    """Return a deduplicated list of (gourmet, slug) tuples via tag pages."""
    seen: set[tuple[str, str]] = set()
    candidates: list[tuple[str, str]] = []

    for tag in DISCOVERY_TAGS:
        if len(candidates) >= TARGET * 4:
            break
        url = f"https://chefsimon.com/recettes/tag/{tag}"
        try:
            r = client.get(url, follow_redirects=True, timeout=15)
            pairs = find_recipe_urls(r.text)
            new = [p for p in pairs if p not in seen]
            seen.update(new)
            candidates.extend(new)
            print(f"  Tag '{tag}': +{len(new)} ({len(candidates)} total)")
            time.sleep(0.3)
        except Exception as exc:
            print(f"  [tag error] {tag}: {exc}")

    return candidates


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    IMAGES_DIR.mkdir(exist_ok=True)

    recipes: list[dict] = []

    with httpx.Client(headers=HEADERS, timeout=15) as client:
        print("Discovering recipe URLs…")
        candidates = collect_candidate_urls(client)
        print(f"Found {len(candidates)} candidate recipe URLs\n")

        for gourmet, slug in candidates:
            if len(recipes) >= TARGET:
                break

            recipe_url = f"https://chefsimon.com/gourmets/{gourmet}/recettes/{slug}"
            try:
                time.sleep(0.4)
                r = client.get(recipe_url, follow_redirects=True, timeout=15)
                ld = find_json_ld_recipe(r.text)
                if not ld:
                    print(f"  SKIP (no JSON-LD): {slug}")
                    continue

                title = (ld.get("name") or "").strip()
                if not title:
                    continue

                steps_raw = parse_steps(ld.get("recipeInstructions", []))
                if not steps_raw:
                    print(f"  SKIP (no steps): {title}")
                    continue

                ingredients = []
                for raw in ld.get("recipeIngredient", []):
                    parsed = parse_ingredient(raw)
                    if parsed:
                        ingredients.append(parsed)

                description = (ld.get("description") or "").strip() or None
                servings = parse_servings(ld.get("recipeYield"))
                cook_time = parse_iso_duration(ld.get("cookTime") or ld.get("totalTime"))
                image_url = get_image_url(ld)
                recipe_type = guess_type(title, description)

                # Distribute cook_time across steps roughly
                step_duration = None
                if cook_time and steps_raw:
                    step_duration = max(1, cook_time // len(steps_raw))

                image_filename = None
                if image_url:
                    stem = uuid.uuid4().hex
                    if save_image(client, image_url, stem):
                        image_filename = f"{stem}.jpg"

                entry = {
                    "title": title,
                    "description": description,
                    "type_name": recipe_type,
                    "servings": servings,
                    "ingredients": ingredients,
                    "steps": [{"description": s, "duration": step_duration} for s in steps_raw],
                    "image_filename": image_filename,
                }
                recipes.append(entry)
                print(f"  ✓ [{len(recipes)}/{TARGET}] {title}")

            except Exception as exc:
                print(f"  ERROR {slug}: {exc}")

    (OUT_DIR / "recipes.json").write_text(
        json.dumps(recipes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nSaved {len(recipes)} recipes → {OUT_DIR / 'recipes.json'}")
    if len(recipes) < TARGET:
        print(f"WARNING: only got {len(recipes)}/{TARGET}. Re-run or add more sources.")


if __name__ == "__main__":
    main()
