import os
import asyncio
import discord
from aiohttp import web
from discord.ext import commands
from game import MonopolyGame, generate_random_country_board
from board_renderer import render_board_image
from trade_view import TradeProposalView
from stats_db import (
    get_player_stats, record_game_win, claim_daily,
    get_top_leaderboard, set_custom_token
)
from dotenv import load_dotenv

load_dotenv()

PLAYER_TOKENS = ["🔴", "🔵", "🟢", "🟡"]

COLOR_LABELS = {
    "brown":     "🟤",
    "light_blue":"🔵",
    "pink":      "🩷",
    "orange":    "🟠",
    "red":       "🔴",
    "yellow":    "🟡",
    "green":     "🟢",
    "dark_blue": "💙",
}

def build_board_embed(game: MonopolyGame) -> discord.Embed:
    """Builds a rich Discord embed showing the full board state across 4 paths."""
    board = game.board
    player_list = game.player_list

    pos_tokens: dict[int, list[str]] = {}
    for i, player in enumerate(player_list):
        state = game.get_player_state(player.id)
        if not state.get("bankrupt", False):
            p = state["position"]
            st = get_player_stats(player.id, player.display_name)
            token = st.get("custom_token") or PLAYER_TOKENS[i % len(PLAYER_TOKENS)]
            pos_tokens.setdefault(p, []).append(token)

    owner_names: dict[int, str] = {}
    for pos, owner_id in game.properties_owned.items():
        owner_names[pos] = game.players[owner_id]["member"].display_name

    def render_tile(pos: int) -> str:
        tile = board[pos]
        t = tile["type"]
        name = tile["name"]

        tokens = " ".join(pos_tokens.get(pos, []))
        tokens_str = f" {tokens}" if tokens else ""

        if t == "go":
            return f"`{pos:02}` 🛫 **START/GO**{tokens_str}"
        elif t == "jail":
            return f"`{pos:02}` 🛂 **Border Control**{tokens_str}"
        elif t == "free_parking":
            return f"`{pos:02}` 🏝️ **International Waters**{tokens_str}"
        elif t == "go_to_jail":
            return f"`{pos:02}` 🚨 **Deportation Zone**{tokens_str}"
        elif t == "community_chest":
            return f"`{pos:02}` 🏦 World Treasury{tokens_str}"
        elif t == "chance":
            return f"`{pos:02}` 🌐 Global News Event{tokens_str}"
        elif t == "tax":
            return f"`{pos:02}` 💸 {name} (-${tile['amount']}){tokens_str}"
        elif t in ("railroad", "utility", "property"):
            mortgage_tag = " *(Mortgaged)*" if tile.get("is_mortgaged", False) else ""
            houses = tile.get("houses", 0)
            h_tag = f" [🏢 Skyscraper]" if houses == 5 else (f" [{houses}🏠]" if houses > 0 else "")
            
            if pos in owner_names:
                return f"`{pos:02}` {name} *(owned by {owner_names[pos]})*{h_tag}{mortgage_tag}{tokens_str}"
            return f"`{pos:02}` {name} — ${tile['price']}{tokens_str}"
        return f"`{pos:02}` {name}{tokens_str}"

    embed = discord.Embed(
        title="🌍 Mutseri's World Monopoly — Board State",
        color=discord.Color.dark_gold()
    )

    path_ranges = [
        ("🟤 Path 1 — Budget (Brown & Light Blue)", range(0, 10)),
        ("🟠 Path 2 — Mid-Low (Pink & Orange)",     range(10, 20)),
        ("🔴 Path 3 — Mid-High (Red & Yellow)",     range(20, 30)),
        ("🏆 Path 4 — Premium (Green & Dark Blue)", range(30, 40)),
    ]
    for path_name, rng in path_ranges:
        lines = [render_tile(i) for i in rng]
        embed.add_field(name=path_name, value="\n".join(lines), inline=False)

    scorecard_lines = []
    for i, player in enumerate(player_list):
        state = game.get_player_state(player.id)
        st = get_player_stats(player.id, player.display_name)
        token = st.get("custom_token") or PLAYER_TOKENS[i % len(PLAYER_TOKENS)]
        jail_tag = " 🔒 In Jail" if state["in_jail"] else ""
        bankrupt_tag = " 💥 BANKRUPT" if state.get("bankrupt", False) else ""
        props = len(state["properties"])
        scorecard_lines.append(
            f"{token} **{player.display_name}** — 💰 ${state['money']} | 🏠 {props} properties{jail_tag}{bankrupt_tag}"
        )
    embed.add_field(name="📊 Player Scorecard", value="\n".join(scorecard_lines), inline=False)

    current = game.get_current_player()
    embed.set_footer(text=f"🎲 It is currently {current.display_name}'s turn (⏱️ 90s timer active).")
    return embed


class TurnView(discord.ui.View):
    def __init__(self, game, channel_id):
        super().__init__(timeout=None)
        self.game = game
        self.channel_id = channel_id
        self.timer_task = None
        self.setup_buttons()
        self.reset_timer()

    def reset_timer(self):
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()
        self.timer_task = asyncio.create_task(self.turn_timeout_task())

    async def turn_timeout_task(self):
        try:
            await asyncio.sleep(90)  # 90-second turn limit
            current_player = self.game.get_current_player()
            player_state = self.game.get_player_state(current_player.id)

            if not player_state["has_rolled"]:
                d1, d2 = self.game.roll_dice()
                total = d1 + d2
                self.game.log_event(f"⏱️ AUTO-ROLL: {current_player.display_name} rolled {d1} and {d2} (Total: {total})")
                self.game.move_player(current_player.id, total)
                player_state["has_rolled"] = True

            self.game.log_event(f"⏱️ TIME EXPIRED: {current_player.display_name}'s turn was automatically ended.")
            self.game.next_turn()

            channel = bot.get_channel(self.channel_id)
            if channel:
                next_p = self.game.get_current_player()
                embed = discord.Embed(
                    title="⏱️ Turn Time Limit Expired (90s)",
                    description=f"**{current_player.display_name}** took too long! Turn automatically passed to **{next_p.display_name}**.",
                    color=discord.Color.orange()
                )
                self.setup_buttons()
                buf = render_board_image(self.game)
                file = discord.File(buf, filename="monopoly_board.png")
                embed.set_image(url="attachment://monopoly_board.png")
                await channel.send(embed=embed, view=self, file=file)
                self.reset_timer()
        except asyncio.CancelledError:
            pass

    def setup_buttons(self):
        self.clear_items()
        current_player = self.game.get_current_player()
        player_state = self.game.get_player_state(current_player.id)

        # 1. Jail Options
        if player_state["in_jail"]:
            bail_btn = discord.ui.Button(label="💳 Pay $50 Bail", style=discord.ButtonStyle.green, custom_id="bail")
            bail_btn.callback = self.bail_callback
            self.add_item(bail_btn)

            doubles_btn = discord.ui.Button(label="🎲 Roll Doubles", style=discord.ButtonStyle.blurple, custom_id="doubles")
            doubles_btn.callback = self.doubles_callback
            self.add_item(doubles_btn)

            if player_state.get("has_jail_card", 0) > 0:
                pass_btn = discord.ui.Button(label="🎟️ Use Diplomatic Pass", style=discord.ButtonStyle.gold, custom_id="jail_pass")
                pass_btn.callback = self.jail_card_callback
                self.add_item(pass_btn)

        # 2. Emergency Bankruptcy Rescue
        elif player_state["money"] < 0:
            mort_btn = discord.ui.Button(label="🏦 Mortgage Property", style=discord.ButtonStyle.secondary, custom_id="mortgage")
            mort_btn.callback = self.mortgage_callback
            self.add_item(mort_btn)

            sell_btn = discord.ui.Button(label="🏷️ Sell House", style=discord.ButtonStyle.secondary, custom_id="sell_house")
            sell_btn.callback = self.sell_house_callback
            self.add_item(sell_btn)

            bankrupt_btn = discord.ui.Button(label="💥 Declare Bankruptcy", style=discord.ButtonStyle.danger, custom_id="bankruptcy")
            bankrupt_btn.callback = self.bankruptcy_callback
            self.add_item(bankrupt_btn)

        # 3. Normal Turn Actions
        else:
            if not player_state["has_rolled"]:
                roll_btn = discord.ui.Button(label="🎲 Roll Dice", style=discord.ButtonStyle.blurple, custom_id="roll")
                roll_btn.callback = self.roll_callback
                self.add_item(roll_btn)
            else:
                pos = player_state["position"]
                tile = self.game.board[pos]

                if tile["type"] in ["property", "railroad", "utility"] and pos not in self.game.properties_owned:
                    buy_btn = discord.ui.Button(label=f"🏠 Buy for ${tile['price']}", style=discord.ButtonStyle.green, custom_id="buy")
                    buy_btn.callback = self.buy_callback
                    self.add_item(buy_btn)

                has_monopolies = any(self.game.has_monopoly(current_player.id, color) for color in COLOR_LABELS)
                if has_monopolies:
                    build_btn = discord.ui.Button(label="🏗️ Build House", style=discord.ButtonStyle.primary, custom_id="build")
                    build_btn.callback = self.build_callback
                    self.add_item(build_btn)

                end_btn = discord.ui.Button(label="⏩ End Turn", style=discord.ButtonStyle.red, custom_id="end")
                end_btn.callback = self.end_callback
                self.add_item(end_btn)

        board_btn = discord.ui.Button(label="📋 View Board", style=discord.ButtonStyle.grey, custom_id="board")
        board_btn.callback = self.board_callback
        self.add_item(board_btn)

    async def update_turn_message(self, interaction: discord.Interaction, embed: discord.Embed):
        self.reset_timer()
        self.setup_buttons()
        buf = render_board_image(self.game)
        file = discord.File(buf, filename="monopoly_board.png")
        embed.set_image(url="attachment://monopoly_board.png")
        await interaction.response.edit_message(embed=embed, view=self, attachments=[file])

    async def roll_callback(self, interaction: discord.Interaction):
        current_player = self.game.get_current_player()
        if interaction.user.id != current_player.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        d1, d2 = self.game.roll_dice()
        total = d1 + d2
        self.game.log_event(f"{current_player.display_name} rolled {d1} and {d2} (Total: {total})")
        self.game.move_player(current_player.id, total)

        player_state = self.game.get_player_state(current_player.id)
        player_state["has_rolled"] = True
        current_tile = self.game.board[player_state["position"]]

        embed = discord.Embed(
            title=f"🎲 {current_player.display_name} Rolled {total}!",
            description=f"Landed on **{current_tile['name']}**.\n\n" + "\n".join(self.game.log[-3:]),
            color=discord.Color.blue()
        )
        embed.add_field(name="Balance", value=f"${player_state['money']}")
        await self.update_turn_message(interaction, embed)

    async def buy_callback(self, interaction: discord.Interaction):
        current_player = self.game.get_current_player()
        if interaction.user.id != current_player.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        player_state = self.game.get_player_state(current_player.id)
        pos = player_state["position"]
        success = self.game.buy_property(current_player.id, pos)

        if success:
            current_tile = self.game.board[pos]
            embed = discord.Embed(
                title="🏠 Property Purchased!",
                description=f"Bought **{current_tile['name']}**.\n\n" + "\n".join(self.game.log[-3:]),
                color=discord.Color.green()
            )
            embed.add_field(name="Balance", value=f"${player_state['money']}")
            await self.update_turn_message(interaction, embed)
        else:
            await interaction.response.send_message("You don't have enough money!", ephemeral=True)

    async def build_callback(self, interaction: discord.Interaction):
        current_player = self.game.get_current_player()
        if interaction.user.id != current_player.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        player_state = self.game.get_player_state(current_player.id)
        buildable = [p for p in player_state["properties"] if self.game.has_monopoly(current_player.id, self.game.board[p]["color"]) and self.game.board[p]["houses"] < 5]

        if not buildable:
            await interaction.response.send_message("You don't have any complete monopoly properties to build on!", ephemeral=True)
            return

        pos = buildable[0]
        success = self.game.build_house(current_player.id, pos)
        if success:
            tile = self.game.board[pos]
            embed = discord.Embed(
                title="🏗️ House Constructed!",
                description=f"Built on **{tile['name']}**!\n\n" + "\n".join(self.game.log[-2:]),
                color=discord.Color.green()
            )
            await self.update_turn_message(interaction, embed)
        else:
            await interaction.response.send_message("Not enough cash to build!", ephemeral=True)

    async def mortgage_callback(self, interaction: discord.Interaction):
        current_player = self.game.get_current_player()
        if interaction.user.id != current_player.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        player_state = self.game.get_player_state(current_player.id)
        unmortgaged = [p for p in player_state["properties"] if not self.game.board[p].get("is_mortgaged", False)]
        if not unmortgaged:
            await interaction.response.send_message("You have no eligible properties to mortgage!", ephemeral=True)
            return

        pos = unmortgaged[0]
        self.game.mortgage_property(current_player.id, pos)
        tile = self.game.board[pos]
        embed = discord.Embed(
            title="🏦 Property Mortgaged",
            description=f"Mortgaged **{tile['name']}** for cash!\n\n" + "\n".join(self.game.log[-2:]),
            color=discord.Color.gold()
        )
        await self.update_turn_message(interaction, embed)

    async def sell_house_callback(self, interaction: discord.Interaction):
        current_player = self.game.get_current_player()
        if interaction.user.id != current_player.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        player_state = self.game.get_player_state(current_player.id)
        houses = [p for p in player_state["properties"] if self.game.board[p].get("houses", 0) > 0]
        if not houses:
            await interaction.response.send_message("You have no houses to sell!", ephemeral=True)
            return

        pos = houses[0]
        self.game.sell_house(current_player.id, pos)
        tile = self.game.board[pos]
        embed = discord.Embed(
            title="🏷️ House Sold",
            description=f"Sold house on **{tile['name']}** for 50% value.\n\n" + "\n".join(self.game.log[-2:]),
            color=discord.Color.gold()
        )
        await self.update_turn_message(interaction, embed)

    async def bail_callback(self, interaction: discord.Interaction):
        current_player = self.game.get_current_player()
        if interaction.user.id != current_player.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        success = self.game.pay_jail_bail(current_player.id)
        if success:
            embed = discord.Embed(title="💳 Bail Paid!", description="Escaped Border Control! You can now roll.", color=discord.Color.green())
            await self.update_turn_message(interaction, embed)
        else:
            await interaction.response.send_message("You need $50 to pay bail!", ephemeral=True)

    async def doubles_callback(self, interaction: discord.Interaction):
        current_player = self.game.get_current_player()
        if interaction.user.id != current_player.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        d1, d2, escaped = self.game.attempt_jail_doubles(current_player.id)
        embed = discord.Embed(
            title=f"🎲 Rolled {d1} and {d2}!",
            description="Escaped Border Control!" if escaped else "No doubles! Remain in Border Control.",
            color=discord.Color.green() if escaped else discord.Color.red()
        )
        await self.update_turn_message(interaction, embed)

    async def jail_card_callback(self, interaction: discord.Interaction):
        current_player = self.game.get_current_player()
        if interaction.user.id != current_player.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        success = self.game.use_jail_card(current_player.id)
        if success:
            embed = discord.Embed(title="🎟️ Pass Used!", description="Diplomatic Immunity used! You are free.", color=discord.Color.gold())
            await self.update_turn_message(interaction, embed)

    async def bankruptcy_callback(self, interaction: discord.Interaction):
        current_player = self.game.get_current_player()
        if interaction.user.id != current_player.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        self.game.declare_bankruptcy(current_player.id)
        active_players = [p for p in self.game.player_list if not self.game.players[p.id]["bankrupt"]]
        
        if len(active_players) == 1:
            winner = active_players[0]
            record_game_win(winner.id, [p.id for p in self.game.player_list])
            embed = discord.Embed(
                title="🏆 GAME OVER — VICTORY!",
                description=f"🎉 **{winner.display_name}** is the sole surviving Monopoly Tycoon and wins the game!",
                color=discord.Color.gold()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            if self.channel_id in active_games:
                del active_games[self.channel_id]
            return

        self.game.next_turn()
        next_player = self.game.get_current_player()
        embed = discord.Embed(
            title="💥 Bankruptcy Declared!",
            description=f"**{current_player.display_name}** has surrendered all assets and was eliminated!\n\nIt is now {next_player.display_name}'s turn.",
            color=discord.Color.red()
        )
        await self.update_turn_message(interaction, embed)

    async def end_callback(self, interaction: discord.Interaction):
        current_player = self.game.get_current_player()
        if interaction.user.id != current_player.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        player_state = self.game.get_player_state(current_player.id)
        if player_state["money"] < 0:
            await interaction.response.send_message("⚠️ You have a negative cash balance! Mortgage properties, sell houses, trade, or declare bankruptcy before ending your turn.", ephemeral=True)
            return

        self.game.next_turn()
        next_player = self.game.get_current_player()

        scorecard_lines = []
        for i, player in enumerate(self.game.player_list):
            state = self.game.get_player_state(player.id)
            st = get_player_stats(player.id, player.display_name)
            token = st.get("custom_token") or PLAYER_TOKENS[i % len(PLAYER_TOKENS)]
            tile_name = self.game.board[state["position"]]["name"]
            jail_tag = " 🔒" if state["in_jail"] else ""
            bankrupt_tag = " 💥" if state.get("bankrupt", False) else ""
            is_current = " ← **Your turn!**" if player.id == next_player.id else ""
            scorecard_lines.append(
                f"{token} **{player.display_name}**{jail_tag}{bankrupt_tag} — 💰 ${state['money']}\n"
                f"　　📍 {tile_name}{is_current}"
            )

        embed = discord.Embed(
            title=f"🎲 {next_player.display_name}'s Turn!",
            description="\n\n".join(scorecard_lines),
            color=discord.Color.green()
        )
        await self.update_turn_message(interaction, embed)

    async def board_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        buf = render_board_image(self.game)
        file = discord.File(buf, filename="monopoly_board.png")
        embed = build_board_embed(self.game)
        embed.set_image(url="attachment://monopoly_board.png")
        await interaction.followup.send(embed=embed, file=file, ephemeral=True)


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="ms!", intents=intents)

active_games = {} 

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

MIN_PLAYERS = 2
MAX_FREE_PLAYERS = 4

@bot.command()
async def start_monopoly(ctx, *opponents: discord.Member):
    if ctx.channel.id in active_games:
        await ctx.send("A game is already running in this channel!")
        return

    if not opponents:
        await ctx.send("Please mention 1 to 3 opponents to play! Example: `!start_monopoly @User1 @User2`")
        return

    if any(opp.bot for opp in opponents):
        await ctx.send("You cannot play against a bot!")
        return

    if ctx.author in opponents:
        await ctx.send("You cannot play against yourself!")
        return

    unique_opponents = []
    for opp in opponents:
        if opp not in unique_opponents:
            unique_opponents.append(opp)

    players = [ctx.author] + unique_opponents
    if len(players) < MIN_PLAYERS:
        await ctx.send("You need at least 2 players to start a game!")
        return

    if len(players) > MAX_FREE_PLAYERS:
        await ctx.send(f"Free games support up to {MAX_FREE_PLAYERS} players!")
        return

    board = generate_random_country_board()
    game = MonopolyGame(players, board=board)
    active_games[ctx.channel.id] = game

    # Apply daily bonus cash buffers to starting balances if claimed
    for p in players:
        st = get_player_stats(p.id, p.display_name)
        if st.get("bonus_cash", 0) > 0:
            game.players[p.id]["money"] += st["bonus_cash"]
            st["bonus_cash"] = 0

    player_mentions = ", ".join(p.mention for p in players)
    embed = discord.Embed(
        title="🌍 Mutseri's World Monopoly Started!",
        color=discord.Color.green()
    )
    embed.description = f"A unique randomized board has been generated!\n**Players:** {player_mentions}\n\n🎲 It is {game.get_current_player().mention}'s turn!"

    view = TurnView(game, ctx.channel.id)
    buf = render_board_image(game)
    file = discord.File(buf, filename="monopoly_board.png")
    embed.set_image(url="attachment://monopoly_board.png")

    await ctx.send(embed=embed, view=view, file=file)

@bot.command()
async def trade(ctx, target: discord.Member, offer_cash: int = 0, req_cash: int = 0):
    """Propose a 90-second trade deal with another player."""
    if ctx.channel.id not in active_games:
        await ctx.send("No active Monopoly game in this channel!")
        return

    game = active_games[ctx.channel.id]
    if ctx.author.id not in game.players or target.id not in game.players:
        await ctx.send("Both players must be in the active game!")
        return

    view = TradeProposalView(game, ctx.author, target, [], offer_cash, [], req_cash)
    embed = discord.Embed(
        title="🤝 Trade Proposal Offered! (⏱️ 90s limit)",
        description=f"**{ctx.author.display_name}** offers **${offer_cash}** to **{target.display_name}** for **${req_cash}**.\n\n{target.mention}, click Accept or Decline within 90s!",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed, view=view)

@bot.command()
async def daily(ctx):
    """Claims daily reward cash and streak bonuses."""
    success, msg, reward = claim_daily(ctx.author.id, ctx.author.display_name)
    embed = discord.Embed(
        title="🎡 Daily Monopoly Reward",
        description=msg,
        color=discord.Color.green() if success else discord.Color.orange()
    )
    await ctx.send(embed=embed)

@bot.command()
async def stats(ctx, member: discord.Member = None):
    """Displays player statistics and career performance."""
    target = member or ctx.author
    st = get_player_stats(target.id, target.display_name)
    
    played = st.get("games_played", 0)
    wins = st.get("wins", 0)
    win_rate = (wins / played * 100) if played > 0 else 0.0
    token = st.get("custom_token") or "🔴"

    embed = discord.Embed(
        title=f"📊 Tycoon Stats — {target.display_name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="Equipped Token", value=token, inline=True)
    embed.add_field(name="Career Wins", value=f"🏆 {wins}", inline=True)
    embed.add_field(name="Games Played", value=f"🎲 {played}", inline=True)
    embed.add_field(name="Win Rate", value=f"📈 {win_rate:.1f}%", inline=True)
    embed.add_field(name="Daily Streak", value=f"🔥 {st.get('daily_streak', 0)} days", inline=True)
    embed.add_field(name="Bonus Cash Buffer", value=f"💰 ${st.get('bonus_cash', 0)}", inline=True)

    await ctx.send(embed=embed)

@bot.command()
async def leaderboard(ctx):
    """Displays top 10 Monopoly Tycoons on the server."""
    top_players = get_top_leaderboard(10)
    if not top_players:
        await ctx.send("No game history recorded yet!")
        return

    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for i, p in enumerate(top_players):
        rank_icon = medals[i] if i < 3 else f"`#{i+1:02d}`"
        token = p.get("custom_token") or "🎲"
        lines.append(
            f"{rank_icon} {token} **{p.get('display_name', 'Player')}** — 🏆 {p.get('wins', 0)} Wins ({p.get('games_played', 0)} played)"
        )

    embed = discord.Embed(
        title="🏆 Server Monopoly Leaderboard",
        description="\n".join(lines),
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

@bot.command()
async def set_token(ctx, emoji: str):
    """Equips a custom player token emoji."""
    success, msg = set_custom_token(ctx.author.id, ctx.author.display_name, emoji)
    await ctx.send(msg)

@bot.command()
async def end_monopoly(ctx):
    if ctx.channel.id in active_games:
        del active_games[ctx.channel.id]
        await ctx.send("The Monopoly game in this channel has been ended.")
    else:
        await ctx.send("There is no active Monopoly game in this channel.")

@bot.command()
async def board(ctx):
    if ctx.channel.id not in active_games:
        await ctx.send("There is no active Monopoly game in this channel!")
        return
    game = active_games[ctx.channel.id]
    buf = render_board_image(game)
    file = discord.File(buf, filename="monopoly_board.png")
    embed = build_board_embed(game)
    embed.set_image(url="attachment://monopoly_board.png")
    await ctx.send(embed=embed, file=file)

# ---------------------------------------------------------------------------
# Keep-alive web server (required by Render; pinged by UptimeRobot)
# ---------------------------------------------------------------------------
async def health_check(request):
    return web.Response(text="Bot is alive!")

async def run_webserver():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Keep-alive server running on port {port}")

async def main():
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("ERROR: DISCORD_TOKEN environment variable is not set.")
        return
    # Start the web server and the Discord bot concurrently
    await run_webserver()
    await bot.start(token)

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"⚠️ Error: {error}")
    print(f"Command error: {error}")

if __name__ == "__main__":
    asyncio.run(main())

