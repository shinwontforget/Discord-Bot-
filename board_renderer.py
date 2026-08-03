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
            raw_name = tile["name"]
            if tile_type == "property":
                parts = raw_name.split(",")
                city_part = parts[0].strip()
                city_part = "".join([char for char in city_part if ord(char) < 128 or char.isalnum() or char == ' ']).strip()
                clean_label = city_part.upper() if city_part else "PROPERTY"
            elif tile_type == "community_chest":
                clean_label = "TREASURY"
            elif tile_type == "chance":
                clean_label = "NEWS"
            elif tile_type == "tax":
                clean_label = "TAX"
            elif tile_type == "railroad":
                clean_label = raw_name.replace("✈️", "").replace("Airport", "").strip().upper()
            elif tile_type == "utility":
                clean_label = raw_name.replace("⚡", "").replace("📡", "").replace("☢️", "").replace("🛰️", "").replace("Grid", "").replace("Network", "").strip().upper()
            else:
                clean_label = tile_type.upper()

            # Dynamic Font Scaling for Tile Text
            target_font_size = max(8, int(tile_w * 0.16))
            tile_font = get_font(target_font_size, bold=True)

            text_x = x1 + (tile_w // 2)
            text_y = y1 + int(tile_h * 0.18) if (1 <= pos <= 9 or 21 <= pos <= 29) else y1 + int(tile_h * 0.22)
            
            draw.text((text_x, text_y), clean_label, fill=(255, 255, 255, 230), font=tile_font, anchor="mm")

            # Draw Price
            if tile_type in ("property", "railroad", "utility") and pos not in game.properties_owned:
                price = tile.get("price", 0)
                price_y = y2 - int(tile_h * 0.20)
                draw.text((text_x, price_y), f"${price}", fill=(0, 240, 255, 255), font=font_tiny, anchor="mm")

            # Draw Mortgaged Badge
            if is_mortgaged:
                draw.rectangle([x1 + 2, y1 + (tile_h // 3), x2 - 2, y2 - (tile_h // 3)], fill=(255, 0, 0, 160))
                draw.text((text_x, y1 + (tile_h // 2)), "MORTGAGED", fill=(255, 255, 255, 255), font=font_tiny, anchor="mm")

            # Draw Houses/Skyscraper Indicator
            houses = tile.get("houses", 0)
            if houses > 0:
                h_text = "🏢 SKY" if houses == 5 else f"🏠x{houses}"
                draw.rectangle([x1 + 4, y1 + 4, x1 + 38, y1 + 18], fill=(0, 240, 255, 200))
                draw.text((x1 + 21, y1 + 11), h_text, fill=(0, 0, 0, 255), font=font_tiny, anchor="mm")

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

    # 3. Draw Translucent Center Scorecard & Game Log Dashboard
    cx1 = int(W * 0.23)
    cy1 = int(H * 0.44)
    cx2 = int(W * 0.77)
    cy2 = int(H * 0.88)

    draw.rectangle([cx1, cy1, cx2, cy2], fill=(10, 15, 29, 210), outline=(0, 240, 255, 180), width=2)
    draw.rectangle([cx1 + 4, cy1 + 4, cx2 - 4, cy2 - 4], outline=(244, 114, 182, 100), width=1)

    draw.text((cx1 + 20, cy1 + 15), "MUTSERI'S WORLD MONOPOLY — LIVE STANDINGS", fill=(0, 240, 255, 255), font=font_header)
    draw.line([cx1 + 20, cy1 + 40, cx2 - 20, cy1 + 40], fill=(255, 255, 255, 60), width=1)

    card_y = cy1 + 50
    for idx, player in enumerate(game.player_list):
        state = game.get_player_state(player.id)
        scheme = PLAYER_NEON_SCHEMES[idx % len(PLAYER_NEON_SCHEMES)]
        r, g, b = scheme["rgb"]
        is_current = (player.id == game.get_current_player().id)
        is_bankrupt = state.get("bankrupt", False)

        card_bg = (30, 41, 59, 220) if is_current else (15, 23, 42, 180)
        outline_c = (255, 0, 85, 255) if is_bankrupt else ((r, g, b, 255) if is_current else (71, 85, 105, 150))

        draw.rectangle([cx1 + 20, card_y, cx2 - 20, card_y + 48], fill=card_bg, outline=outline_c, width=2)

        draw.ellipse([cx1 + 32, card_y + 12, cx1 + 56, card_y + 36], fill=(r, g, b, 230), outline=(255, 255, 255, 255), width=2)
        draw.text((cx1 + 44, card_y + 24), scheme["label"], fill=(255, 255, 255, 255), font=font_tiny, anchor="mm")

        status_str = " 💥 BANKRUPT" if is_bankrupt else (" 🔒 IN JAIL" if state["in_jail"] else (" [TURN]" if is_current else ""))
        draw.text((cx1 + 68, card_y + 10), f"{player.display_name}{status_str}", fill=(255, 255, 255, 255), font=font_body)

        stats_line = f"Cash: ${state['money']}  |  Props: {len(state['properties'])}  |  Passes: {state.get('has_jail_card', 0)}"
        draw.text((cx1 + 68, card_y + 28), stats_line, fill=(148, 163, 184, 255), font=font_tiny)

        card_y += 56

    draw.line([cx1 + 20, card_y + 6, cx2 - 20, card_y + 6], fill=(255, 255, 255, 60), width=1)
    draw.text((cx1 + 20, card_y + 12), "RECENT GAME EVENTS", fill=(244, 114, 182, 255), font=font_header)

    log_y = card_y + 34
    recent_logs = game.log[-3:] if game.log else ["Game initialized. Roll the dice to begin!"]
    for log_msg in recent_logs:
        clean_log = log_msg.encode("ascii", "ignore").decode("ascii").strip()
        draw.text((cx1 + 30, log_y), f"• {clean_log[:75]}", fill=(226, 232, 240, 255), font=font_tiny)
        log_y += 18

    # Combine Base Image and Overlay
    final_img = Image.alpha_composite(base_img, overlay).convert("RGB")

    buf = io.BytesIO()
    final_img.save(buf, format="PNG")
    buf.seek(0)
    return buf
