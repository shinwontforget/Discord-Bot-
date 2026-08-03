import os
import io
import shutil
from PIL import Image, ImageDraw, ImageFont

COLOR_HEX_MAP = {
    "brown": "#8B4513",
    "light_blue": "#38BDF8",
    "pink": "#F472B6",
    "orange": "#FB923C",
    "red": "#EF4444",
    "yellow": "#FACC15",
    "green": "#22C55E",
    "dark_blue": "#1D4ED8",
}

from stats_db import get_player_stats

PLAYER_NEON_SCHEMES = [
    {"rgb": (255, 0, 85),   "hex": "#FF0055", "label": "P1"},  # Neon Pink/Red
    {"rgb": (0, 240, 255),  "hex": "#00F0FF", "label": "P2"},  # Neon Cyan
    {"rgb": (57, 255, 20),  "hex": "#39FF14", "label": "P3"},  # Neon Green
    {"rgb": (255, 230, 0),  "hex": "#FFE600", "label": "P4"},  # Neon Gold
]

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "board_template.png")
ALT_SOURCE = r"C:\Users\Soumil\.gemini\antigravity-ide\brain\e8f112d4-3ae1-4183-a2d1-7820ce3f0e91\media__1785782821637.png"

if not os.path.exists(TEMPLATE_PATH) and os.path.exists(ALT_SOURCE):
    try:
        shutil.copy(ALT_SOURCE, TEMPLATE_PATH)
    except Exception:
        pass

def get_font(size=14, bold=False):
    font_candidates = [
        "arialbd.ttf" if bold else "arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for font_name in font_candidates:
        try:
            return ImageFont.truetype(font_name, size)
        except IOError:
            continue
    return ImageFont.load_default()

def get_tile_bounds(pos: int, W: int, H: int) -> tuple[int, int, int, int]:
    margin_x_left = int(0.132 * W)
    margin_x_right = int(0.868 * W)
    margin_y_top = int(0.160 * H)
    margin_y_bottom = int(0.840 * H)

    tile_w = (margin_x_right - margin_x_left) / 9.0
    tile_h = (margin_y_bottom - margin_y_top) / 9.0

    if pos == 0:  # Top-Left START
        return (0, 0, margin_x_left, margin_y_top)
    elif pos == 10:  # Top-Right JAIL
        return (margin_x_right, 0, W, margin_y_top)
    elif pos == 20:  # Bottom-Right VACATION
        return (margin_x_right, margin_y_bottom, W, H)
    elif pos == 30:  # Bottom-Left GO TO JAIL
        return (0, margin_y_bottom, margin_x_left, H)
    elif 1 <= pos <= 9:  # Top Row (left to right)
        x1 = int(margin_x_left + (pos - 1) * tile_w)
        return (x1, 0, int(x1 + tile_w), margin_y_top)
    elif 11 <= pos <= 19:  # Right Column (top to bottom)
        y1 = int(margin_y_top + (pos - 11) * tile_h)
        return (margin_x_right, y1, W, int(y1 + tile_h))
    elif 21 <= pos <= 29:  # Bottom Row (right to left)
        x1 = int(margin_x_right - (pos - 20) * tile_w)
        return (x1, margin_y_bottom, int(x1 + tile_w), H)
    elif 31 <= pos <= 39:  # Left Column (bottom to top)
        y1 = int(margin_y_bottom - (pos - 30) * tile_h)
        return (0, int(y1 - tile_h), margin_x_left, int(y1))
    raise ValueError(f"Invalid position {pos}")

def render_board_image(game) -> io.BytesIO:
    # Ensure template image is copied locally
    if not os.path.exists(TEMPLATE_PATH) and os.path.exists(ALT_SOURCE):
        try:
            shutil.copy(ALT_SOURCE, TEMPLATE_PATH)
        except Exception:
            pass

    if os.path.exists(TEMPLATE_PATH):
        base_img = Image.open(TEMPLATE_PATH).convert("RGBA")
    else:
        # High quality dark neon fallback canvas if template image missing
        base_img = Image.new("RGBA", (1200, 960), (10, 15, 29, 255))

    W, H = base_img.size

    # Create overlay layer for translucent glows and clean text
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_header = get_font(max(12, int(W * 0.013)), bold=True)
    font_body = get_font(max(10, int(W * 0.011)), bold=False)
    font_tiny = get_font(max(8, int(W * 0.009)), bold=False)

    # 1. Overlay Dynamic Property Text, Owner Badges & Mortgaged Status
    for pos in range(40):
        x1, y1, x2, y2 = get_tile_bounds(pos, W, H)
        tile = game.board[pos]
        tile_type = tile["type"]
        is_mortgaged = tile.get("is_mortgaged", False)
        tile_w = x2 - x1
        tile_h = y2 - y1

        # Draw Owner Glow Border
        if pos in game.properties_owned:
            owner_id = game.properties_owned[pos]
            owner_idx = next((i for i, p in enumerate(game.player_list) if p.id == owner_id), 0)
            scheme = PLAYER_NEON_SCHEMES[owner_idx % len(PLAYER_NEON_SCHEMES)]
            r, g, b = scheme["rgb"]

            draw.rectangle([x1 + 1, y1 + 1, x2 - 1, y2 - 1], outline=(r, g, b, 120), width=4)
            draw.rectangle([x1 + 3, y1 + 3, x2 - 3, y2 - 3], outline=(r, g, b, 255), width=2)

        # Draw Dynamic City / Special Tile Name
        if pos not in (0, 10, 20, 30):
            if tile_type == "property":
                city_name = tile.get("city", "")
                if not city_name:
                    raw_name = tile["name"]
                    parts = raw_name.split(",")
                    city_name = parts[0].strip()
                # Strip emoji characters only
                city_name = "".join([c for c in city_name if not (0x1F600 <= ord(c) <= 0x1F9FF or 0x1F300 <= ord(c) <= 0x1F5FF or 0x1F680 <= ord(c) <= 0x1F6FF or 0x2600 <= ord(c) <= 0x27BF)]).strip()
                # Split into two lines if long
                words = city_name.upper().split()
                if len(words) == 1:
                    line1, line2 = words[0][:10], ""
                elif len(words) == 2:
                    line1, line2 = words[0][:10], words[1][:10]
                else:
                    line1 = " ".join(words[:len(words)//2 + 1])[:10]
                    line2 = " ".join(words[len(words)//2 + 1:])[:10]
                clean_label = line1
                clean_label2 = line2
            elif tile_type == "community_chest":
                clean_label, clean_label2 = "TREASURY", ""
            elif tile_type == "chance":
                clean_label, clean_label2 = "NEWS", ""
            elif tile_type == "tax":
                clean_label, clean_label2 = "TAX", ""
            elif tile_type == "railroad":
                clean_label, clean_label2 = "AIRPORT", ""
            elif tile_type == "utility":
                clean_label, clean_label2 = "UTILITY", ""
            else:
                clean_label, clean_label2 = tile_type.upper()[:10], ""

            # --- Cover template's baked-in text with a dark fill ---
            # Determine the text zone for this tile side
            pad = 3
            if 1 <= pos <= 9:
                # Top row: cover inner 80% horizontally, top 85% vertically (leave color-bar bottom)
                cx1 = x1 + pad
                cy1 = y1 + pad
                cx2 = x2 - pad
                cy2 = y2 - int(tile_h * 0.18)  # leave the colored bar strip at bottom
            elif 21 <= pos <= 29:
                # Bottom row: cover inner, leave color-bar at top
                cx1 = x1 + pad
                cy1 = y1 + int(tile_h * 0.18)  # leave colored bar at top
                cx2 = x2 - pad
                cy2 = y2 - pad
            elif 11 <= pos <= 19:
                # Right column: leave color-bar on left edge
                cx1 = x1 + int(tile_w * 0.22)
                cy1 = y1 + pad
                cx2 = x2 - pad
                cy2 = y2 - pad
            else:  # 31 <= pos <= 39, left column
                # Leave color-bar on right edge
                cx1 = x1 + pad
                cy1 = y1 + pad
                cx2 = x2 - int(tile_w * 0.22)
                cy2 = y2 - pad

            draw.rectangle([cx1, cy1, cx2, cy2], fill=(8, 12, 28, 235))

            # Font sizing: use tile's narrower dimension for scale
            narrow = min(tile_w, tile_h)
            target_font_size = max(9, min(14, int(narrow * 0.18)))
            tile_font = get_font(target_font_size, bold=True)
            price_font = get_font(max(8, target_font_size - 2), bold=False)

            text_x = (cx1 + cx2) // 2

            if tile_type == "property":
                # Two-line city name, centered
                line_gap = target_font_size + 2
                total_text_h = (line_gap * (2 if clean_label2 else 1))
                center_y = (cy1 + cy2) // 2
                ty1 = center_y - total_text_h // 2 + line_gap // 2
                draw.text((text_x, ty1), clean_label, fill=(255, 255, 255, 245), font=tile_font, anchor="mm")
                if clean_label2:
                    draw.text((text_x, ty1 + line_gap), clean_label2, fill=(255, 255, 255, 245), font=tile_font, anchor="mm")
                # Price at bottom of text zone
                if pos not in game.properties_owned:
                    price = tile.get("price", 0)
                    draw.text((text_x, cy2 - target_font_size // 2 - 2), f"${price}", fill=(0, 240, 255, 255), font=price_font, anchor="mm")
            else:
                # Single label centered
                center_y = (cy1 + cy2) // 2
                draw.text((text_x, center_y), clean_label, fill=(255, 255, 255, 230), font=tile_font, anchor="mm")
                # Price for railroad/utility
                if tile_type in ("railroad", "utility") and pos not in game.properties_owned:
                    price = tile.get("price", 0)
                    draw.text((text_x, cy2 - target_font_size // 2 - 2), f"${price}", fill=(0, 240, 255, 255), font=price_font, anchor="mm")
                elif tile_type == "tax":
                    amount = tile.get("amount", 0)
                    draw.text((text_x, cy2 - target_font_size // 2 - 2), f"-${amount}", fill=(255, 80, 80, 255), font=price_font, anchor="mm")

            # Draw Mortgaged Badge
            if is_mortgaged:
                draw.rectangle([cx1 + 2, cy1 + (tile_h // 3), cx2 - 2, cy1 + (2 * tile_h // 3)], fill=(255, 0, 0, 180))
                draw.text((text_x, cy1 + (tile_h // 2)), "MORTGAGED", fill=(255, 255, 255, 255), font=price_font, anchor="mm")

            # Draw Houses/Skyscraper Indicator
            houses = tile.get("houses", 0)
            if houses > 0:
                h_text = "SKY" if houses == 5 else f"{houses}H"
                hw = 26
                hh = 14
                draw.rectangle([cx1 + 2, cy1 + 2, cx1 + hw, cy1 + hh], fill=(0, 200, 255, 230))
                draw.text((cx1 + hw // 2 + 1, cy1 + hh // 2 + 1), h_text, fill=(0, 0, 0, 255), font=price_font, anchor="mm")

    # 2. Draw Multi-Layer Glowing Neon Player Piece Locators
    pos_players: dict[int, list[int]] = {}
    for idx, player in enumerate(game.player_list):
        state = game.get_player_state(player.id)
        if not state.get("bankrupt", False):
            p = state["position"]
            pos_players.setdefault(p, []).append(idx)

    for pos, player_indices in pos_players.items():
        x1, y1, x2, y2 = get_tile_bounds(pos, W, H)
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        count = len(player_indices)

        for i, p_idx in enumerate(player_indices):
            offset_x = int((i - (count - 1) / 2) * (W * 0.022))
            tx = center_x + offset_x
            ty = center_y + int(H * 0.015) if pos not in (0, 10, 20, 30) else center_y

            scheme = PLAYER_NEON_SCHEMES[p_idx % len(PLAYER_NEON_SCHEMES)]
            r, g, b = scheme["rgb"]

            # Layer 1: Translucent Glowing Aura
            r_aura = int(W * 0.018)
            draw.ellipse([tx - r_aura, ty - r_aura, tx + r_aura, ty + r_aura], fill=(r, g, b, 70))

            # Layer 2: Secondary Bloom Ring
            r_bloom = int(W * 0.014)
            draw.ellipse([tx - r_bloom, ty - r_bloom, tx + r_bloom, ty + r_bloom], fill=(r, g, b, 140))

            # Layer 3: Crisp Outer White Ring
            r_ring = int(W * 0.011)
            draw.ellipse([tx - r_ring, ty - r_ring, tx + r_ring, ty + r_ring], outline=(255, 255, 255, 255), width=2)

            # Layer 4: Solid Neon Core
            r_core = int(W * 0.009)
            draw.ellipse([tx - r_core, ty - r_core, tx + r_core, ty + r_core], fill=(r, g, b, 240))

            # Layer 5: Centered Player Label
            draw.text((tx, ty), scheme["label"], fill=(255, 255, 255, 255), font=font_tiny, anchor="mm")

    # Combine Base Image and Overlay
    final_img = Image.alpha_composite(base_img, overlay).convert("RGB")

    buf = io.BytesIO()
    final_img.save(buf, format="PNG")
    buf.seek(0)
    return buf
    buf.seek(0)
    return buf
