import io
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

PLAYER_COLOR_SCHEMES = [
    {"fill": (239, 68, 68),   "outline": (255, 255, 255), "label": "P1"},
    {"fill": (59, 130, 246),  "outline": (255, 255, 255), "label": "P2"},
    {"fill": (34, 197, 94),   "outline": (255, 255, 255), "label": "P3"},
    {"fill": (234, 179, 8),   "outline": (0, 0, 0),       "label": "P4"},
]


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

def get_tile_bounds(pos: int) -> tuple[int, int, int, int]:
    if pos == 0: return (1060, 1060, 1220, 1220)
    elif pos == 10: return (0, 1060, 160, 1220)
    elif pos == 20: return (0, 0, 160, 160)
    elif pos == 30: return (1060, 0, 1220, 160)
    elif 1 <= pos <= 9:
        x1 = 1060 - pos * 100
        return (x1, 1060, x1 + 100, 1220)
    elif 11 <= pos <= 19:
        y1 = 1060 - (pos - 10) * 100
        return (0, y1, 160, y1 + 100)
    elif 21 <= pos <= 29:
        x1 = 160 + (pos - 20) * 100
        return (x1, 0, x1 + 100, 160)
    elif 31 <= pos <= 39:
        y1 = 160 + (pos - 30) * 100
        return (1060, y1, 1220, y1 + 100)
    raise ValueError(f"Invalid position {pos}")

def render_board_image(game) -> io.BytesIO:
    width, height = 1220, 1220
    img = Image.new("RGB", (width, height), "#0F172A")
    draw = ImageDraw.Draw(img)

    font_title = get_font(28, bold=True)
    font_header = get_font(18, bold=True)
    font_body = get_font(14, bold=False)
    font_small = get_font(11, bold=False)
    font_tiny = get_font(9, bold=False)

    # 1. Draw 40 Tiles
    for pos in range(40):
        x1, y1, x2, y2 = get_tile_bounds(pos)
        tile = game.board[pos]
        tile_type = tile["type"]
        is_mortgaged = tile.get("is_mortgaged", False)

        bg_color = "#334155" if pos in (0, 10, 20, 30) else ("#475569" if is_mortgaged else "#1E293B")
        draw.rectangle([x1, y1, x2, y2], fill=bg_color, outline="#475569", width=2)

        # Draw banner strip for properties
        if tile_type == "property":
            c_hex = COLOR_HEX_MAP.get(tile.get("color", ""), "#94A3B8")
            banner_size = 28
            if 1 <= pos <= 9:
                draw.rectangle([x1, y1, x2, y1 + banner_size], fill=c_hex)
            elif 11 <= pos <= 19:
                draw.rectangle([x2 - banner_size, y1, x2, y2], fill=c_hex)
            elif 21 <= pos <= 29:
                draw.rectangle([x1, y2 - banner_size, x2, y2], fill=c_hex)
            elif 31 <= pos <= 39:
                draw.rectangle([x1, y1, x1 + banner_size, y2], fill=c_hex)

            # Draw Houses/Skyscrapers on banner
            houses = tile.get("houses", 0)
            if houses > 0:
                h_text = "🏢 SKY" if houses == 5 else f"🏠x{houses}"
                draw.text((x1 + 8, y1 + 6), h_text, fill="#FFFFFF", font=font_tiny)

        # Draw owner border badge
        if pos in game.properties_owned:
            owner_id = game.properties_owned[pos]
            owner_idx = next((i for i, p in enumerate(game.player_list) if p.id == owner_id), 0)
            owner_color = PLAYER_COLOR_SCHEMES[owner_idx % len(PLAYER_COLOR_SCHEMES)]["fill"]
            draw.rectangle([x1 + 3, y1 + 3, x2 - 3, y2 - 3], outline=owner_color, width=3)

        # Tile Label
        name = tile["name"]
        clean_name = name.encode("ascii", "ignore").decode("ascii").strip()
        if not clean_name:
            if tile_type == "go": clean_name = "START / GO"
            elif tile_type == "jail": clean_name = "BORDER CTRL"
            elif tile_type == "free_parking": clean_name = "INTL WATERS"
            elif tile_type == "go_to_jail": clean_name = "DEPORTED"
            elif tile_type == "community_chest": clean_name = "TREASURY"
            elif tile_type == "chance": clean_name = "GLOBAL NEWS"
            elif tile_type == "tax": clean_name = "TAX"
            else: clean_name = tile_type.upper()

        if is_mortgaged:
            clean_name = f"[MORTGAGED] {clean_name}"

        short_name = clean_name[:16] + ".." if len(clean_name) > 18 else clean_name

        draw.text((x1 + 6, y1 + 4), f"#{pos:02d}", fill="#94A3B8", font=font_tiny)
        text_y = y1 + 32 if (1 <= pos <= 9 or tile_type == "property") else y1 + 20
        draw.text((x1 + 6, text_y), short_name, fill="#F8FAFC", font=font_tiny)

        if tile_type in ("property", "railroad", "utility") and pos not in game.properties_owned:
            price = tile.get("price", 0)
            draw.text((x1 + 6, y2 - 18), f"${price}", fill="#38BDF8", font=font_tiny)

    # 2. Draw Player Tokens
    pos_players: dict[int, list[int]] = {}
    for idx, player in enumerate(game.player_list):
        state = game.get_player_state(player.id)
        if not state.get("bankrupt", False):
            p = state["position"]
            pos_players.setdefault(p, []).append(idx)

    for pos, player_indices in pos_players.items():
        x1, y1, x2, y2 = get_tile_bounds(pos)
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        token_radius = 12
        count = len(player_indices)
        for i, p_idx in enumerate(player_indices):
            offset_x = (i - (count - 1) / 2) * 26
            tx = int(center_x + offset_x)
            ty = center_y + 10
            scheme = PLAYER_COLOR_SCHEMES[p_idx % len(PLAYER_COLOR_SCHEMES)]
            draw.ellipse(
                [tx - token_radius, ty - token_radius, tx + token_radius, ty + token_radius],
                fill=scheme["fill"],
                outline=scheme["outline"],
                width=2
            )
            draw.text((tx - 6, ty - 7), scheme["label"], fill="#FFFFFF", font=font_tiny)

    # 3. Draw Center Dashboard
    cx1, cy1, cx2, cy2 = 180, 180, 1040, 1040
    draw.rectangle([cx1, cy1, cx2, cy2], fill="#0F172A", outline="#334155", width=3)
    draw.rectangle([cx1 + 10, cy1 + 10, cx2 - 10, cy2 - 10], fill="#1E293B", outline="#475569", width=2)

    draw.text((cx1 + 30, cy1 + 30), "MUTSERI'S WORLD MONOPOLY", fill="#F59E0B", font=font_title)
    draw.line([cx1 + 30, cy1 + 70, cx2 - 30, cy1 + 70], fill="#475569", width=2)

    draw.text((cx1 + 30, cy1 + 85), "PLAYER SCORECARD", fill="#38BDF8", font=font_header)

    card_y = cy1 + 120
    for idx, player in enumerate(game.player_list):
        state = game.get_player_state(player.id)
        scheme = PLAYER_COLOR_SCHEMES[idx % len(PLAYER_COLOR_SCHEMES)]
        is_current = (player.id == game.get_current_player().id)
        is_bankrupt = state.get("bankrupt", False)

        card_bg = "#334155" if is_current else "#0F172A"
        outline_color = "#EF4444" if is_bankrupt else (scheme["fill"] if is_current else "#475569")
        draw.rectangle([cx1 + 30, card_y, cx2 - 30, card_y + 65], fill=card_bg, outline=outline_color, width=2)

        draw.ellipse([cx1 + 45, card_y + 18, cx1 + 75, card_y + 48], fill=scheme["fill"], outline="#FFFFFF", width=2)
        draw.text((cx1 + 52, card_y + 25), scheme["label"], fill="#FFFFFF", font=font_small)

        status_tag = " [BANKRUPT 💥]" if is_bankrupt else (" [IN JAIL 🔒]" if state["in_jail"] else (" [CURRENT TURN]" if is_current else ""))
        draw.text((cx1 + 90, card_y + 12), f"{player.display_name}{status_tag}", fill="#F8FAFC", font=font_body)
        
        tile_name = game.board[state["position"]]["name"].encode("ascii", "ignore").decode("ascii").strip()
        stats_str = f"Cash: ${state['money']}  |  Properties: {len(state['properties'])}  |  Diplomatic Passes: {state.get('has_jail_card', 0)}"
        draw.text((cx1 + 90, card_y + 36), stats_str, fill="#94A3B8", font=font_small)

        card_y += 75

    draw.line([cx1 + 30, card_y + 10, cx2 - 30, card_y + 10], fill="#475569", width=2)
    draw.text((cx1 + 30, card_y + 20), "RECENT GAME LOG", fill="#38BDF8", font=font_header)

    log_y = card_y + 50
    recent_logs = game.log[-5:] if game.log else ["Game started! Roll dice to begin."]
    for log_msg in recent_logs:
        clean_log = log_msg.encode("ascii", "ignore").decode("ascii").strip()
        draw.text((cx1 + 40, log_y), f"• {clean_log[:85]}", fill="#E2E8F0", font=font_small)
        log_y += 24

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
