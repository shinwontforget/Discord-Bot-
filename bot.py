import os
import discord
from discord.ext import commands
from game import MonopolyGame, BOARD
from dotenv import load_dotenv

load_dotenv()

# 2. The Discord Interface
class TurnView(discord.ui.View):
    def __init__(self, game, channel_id):
        super().__init__(timeout=None)
        self.game = game
        self.channel_id = channel_id
        self.setup_buttons()

    def setup_buttons(self):
        self.clear_items()
        
        current_player = self.game.get_current_player()
        player_state = self.game.get_player_state(current_player.id)
        
        if not player_state["has_rolled"]:
            roll_btn = discord.ui.Button(label="Roll Dice", style=discord.ButtonStyle.blurple, custom_id="roll")
            roll_btn.callback = self.roll_callback
            self.add_item(roll_btn)
        else:
            pos = player_state["position"]
            tile = BOARD[pos]
            
            # Can they buy it?
            if tile["type"] in ["property", "railroad", "utility"] and pos not in self.game.properties_owned:
                buy_btn = discord.ui.Button(label=f"Buy for ${tile['price']}", style=discord.ButtonStyle.green, custom_id="buy")
                buy_btn.callback = self.buy_callback
                self.add_item(buy_btn)
                
            end_btn = discord.ui.Button(label="End Turn", style=discord.ButtonStyle.red, custom_id="end")
            end_btn.callback = self.end_callback
            self.add_item(end_btn)

    async def roll_callback(self, interaction: discord.Interaction):
        current_player_member = self.game.get_current_player()
        
        if interaction.user.id != current_player_member.id:
            await interaction.response.send_message("Hold on, it's not your turn!", ephemeral=True)
            return
            
        d1, d2 = self.game.roll_dice()
        total = d1 + d2
        self.game.log_event(f"{current_player_member.display_name} rolled {d1} and {d2} (Total: {total})")
        
        self.game.move_player(current_player_member.id, total)
        
        player_state = self.game.get_player_state(current_player_member.id)
        player_state["has_rolled"] = True
        
        current_tile = BOARD[player_state["position"]]
        
        embed = discord.Embed(
            title=f"🎲 {current_player_member.display_name} Rolled {total}!",
            description=f"Landed on **{current_tile['name']}**.\n\n" + "\n".join(self.game.log[-3:]),
            color=discord.Color.blue()
        )
        embed.add_field(name="Balance", value=f"${player_state['money']}")
        
        self.setup_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    async def buy_callback(self, interaction: discord.Interaction):
        current_player_member = self.game.get_current_player()
        if interaction.user.id != current_player_member.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
            
        player_state = self.game.get_player_state(current_player_member.id)
        pos = player_state["position"]
        success = self.game.buy_property(current_player_member.id, pos)
        
        if success:
            self.setup_buttons()
            current_tile = BOARD[pos]
            embed = discord.Embed(
                title="🏠 Property Purchased!",
                description=f"Bought **{current_tile['name']}**.\n\n" + "\n".join(self.game.log[-3:]),
                color=discord.Color.green()
            )
            embed.add_field(name="Balance", value=f"${player_state['money']}")
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("You don't have enough money!", ephemeral=True)
            
    async def end_callback(self, interaction: discord.Interaction):
        current_player_member = self.game.get_current_player()
        if interaction.user.id != current_player_member.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
            
        self.game.next_turn()
        
        next_player = self.game.get_current_player()
        player_state = self.game.get_player_state(next_player.id)
        current_tile = BOARD[player_state["position"]]
        
        self.setup_buttons()
        embed = discord.Embed(
            title=f"It is now {next_player.display_name}'s turn.",
            description=f"Current position: **{current_tile['name']}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Balance", value=f"${player_state['money']}")
        
        await interaction.response.edit_message(embed=embed, view=self)

# 3. The Bot Command
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary to store active games by channel ID
active_games = {} 

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.command()
async def start_monopoly(ctx, opponent: discord.Member = None):
    if opponent is None:
        await ctx.send("Please mention an opponent to play against! Example: `!start_monopoly @User`")
        return

    if ctx.channel.id in active_games:
        await ctx.send("A game is already running in this channel!")
        return

    if opponent.bot:
        await ctx.send("You cannot play against a bot!")
        return

    # Initialize a 2-player game
    players = [ctx.author, opponent]
    game = MonopolyGame(players)
    active_games[ctx.channel.id] = game
    
    # Create the visual representation
    embed = discord.Embed(
        title="🎲 Monopoly: South Park Edition Started!", 
        description=f"Welcome to Monopoly! It is currently {game.get_current_player().mention}'s turn.", 
        color=discord.Color.green()
    )
    view = TurnView(game, ctx.channel.id)
    
    await ctx.send(embed=embed, view=view)

@bot.command()
async def end_monopoly(ctx):
    if ctx.channel.id in active_games:
        del active_games[ctx.channel.id]
        await ctx.send("The Monopoly game in this channel has been ended.")
    else:
        await ctx.send("There is no active Monopoly game in this channel.")

if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("Please set the DISCORD_TOKEN environment variable.")
    else:
        bot.run(token)