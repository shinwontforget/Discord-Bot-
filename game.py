import random

# The Board Array
BOARD = [
    {"name": "GO", "type": "go"},
    {"name": "Mediterranean Avenue", "type": "property", "color": "brown", "price": 60, "rent": [2, 10, 30, 90, 160, 250]},
    {"name": "SNACKY S'MORES", "type": "community_chest"},
    {"name": "Baltic Avenue", "type": "property", "color": "brown", "price": 60, "rent": [4, 20, 60, 180, 320, 450]},
    {"name": "GOOBACK TAX", "type": "tax", "amount": 200},
    {"name": "SEVEN-TURDY-SEVEN", "type": "railroad", "price": 200},
    {"name": "Oriental Avenue", "type": "property", "color": "light_blue", "price": 100, "rent": [6, 30, 90, 270, 400, 550]},
    {"name": "CHEESY POOFS", "type": "chance"},
    {"name": "Vermont Avenue", "type": "property", "color": "light_blue", "price": 100, "rent": [6, 30, 90, 270, 400, 550]},
    {"name": "Connecticut Avenue", "type": "property", "color": "light_blue", "price": 120, "rent": [8, 40, 100, 300, 450, 600]},
    {"name": "Just Visiting / In Jail", "type": "jail"},
    {"name": "St. Charles Place", "type": "property", "color": "pink", "price": 140, "rent": [10, 50, 150, 450, 625, 750]},
    {"name": "Mephesto's Genetic Engineering Ranch", "type": "utility", "price": 150},
    {"name": "States Avenue", "type": "property", "color": "pink", "price": 140, "rent": [10, 50, 150, 450, 625, 750]},
    {"name": "Virginia Avenue", "type": "property", "color": "pink", "price": 160, "rent": [12, 60, 180, 500, 700, 900]},
    {"name": "HELICRAPTER", "type": "railroad", "price": 200},
    {"name": "St. James Place", "type": "property", "color": "orange", "price": 180, "rent": [14, 70, 200, 550, 750, 950]},
    {"name": "SNACKY S'MORES", "type": "community_chest"},
    {"name": "Tennessee Avenue", "type": "property", "color": "orange", "price": 180, "rent": [14, 70, 200, 550, 750, 950]},
    {"name": "New York Avenue", "type": "property", "color": "orange", "price": 200, "rent": [16, 80, 220, 600, 800, 1000]},
    {"name": "Free Parking", "type": "free_parking"},
    {"name": "Kentucky Avenue", "type": "property", "color": "red", "price": 220, "rent": [18, 90, 250, 700, 875, 1050]},
    {"name": "CHEESY POOFS", "type": "chance"},
    {"name": "Indiana Avenue", "type": "property", "color": "red", "price": 220, "rent": [18, 90, 250, 700, 875, 1050]},
    {"name": "Illinois Avenue", "type": "property", "color": "red", "price": 240, "rent": [20, 100, 300, 750, 925, 1100]},
    {"name": "POO CHOO EXPRESS", "type": "railroad", "price": 200},
    {"name": "Atlantic Avenue", "type": "property", "color": "yellow", "price": 260, "rent": [22, 110, 330, 800, 975, 1150]},
    {"name": "Ventnor Avenue", "type": "property", "color": "yellow", "price": 260, "rent": [22, 110, 330, 800, 975, 1150]},
    {"name": "Tynacorp", "type": "utility", "price": 150},
    {"name": "Marvin Gardens", "type": "property", "color": "yellow", "price": 280, "rent": [24, 120, 360, 850, 1025, 1200]},
    {"name": "Go To Jail", "type": "go_to_jail"},
    {"name": "Pacific Avenue", "type": "property", "color": "green", "price": 300, "rent": [26, 130, 390, 900, 1100, 1275]},
    {"name": "North Carolina Avenue", "type": "property", "color": "green", "price": 300, "rent": [26, 130, 390, 900, 1100, 1275]},
    {"name": "SNACKY S'MORES", "type": "community_chest"},
    {"name": "Pennsylvania Avenue", "type": "property", "color": "green", "price": 320, "rent": [28, 150, 450, 1000, 1200, 1400]},
    {"name": "KYLE'S TOILET", "type": "railroad", "price": 200},
    {"name": "CHEESY POOFS", "type": "chance"},
    {"name": "Park Place", "type": "property", "color": "dark_blue", "price": 350, "rent": [35, 175, 500, 1100, 1300, 1500]},
    {"name": "AAAAAND, IT'S GONE!", "type": "tax", "amount": 100},
    {"name": "Boardwalk", "type": "property", "color": "dark_blue", "price": 400, "rent": [50, 200, 600, 1400, 1700, 2000]}
]

class MonopolyGame:
    def __init__(self, players):
        # Initialize players with starting money and board position (0 is GO)
        # We store discord.Member objects in player_list but keyed by ID in players dict
        self.players = {
            player.id: {
                "member": player,
                "money": 1500, 
                "position": 0,
                "in_jail": False,
                "jail_turns": 0,
                "properties": [], # list of indices of owned properties
                "has_rolled": False
            } for player in players
        }
        self.turn_index = 0
        self.player_list = players
        self.properties_owned = {} # Maps board index to owner's player ID
        self.log = [] # Game log to show what happened
        
    def get_current_player(self):
        return self.player_list[self.turn_index]
        
    def get_player_state(self, player_id):
        return self.players[player_id]

    def log_event(self, message):
        self.log.append(message)

    def next_turn(self):
        current_player_id = self.get_current_player().id
        self.players[current_player_id]["has_rolled"] = False
        self.turn_index = (self.turn_index + 1) % len(self.player_list)
        
    def roll_dice(self):
        return random.randint(1, 6), random.randint(1, 6)

    def move_player(self, player_id, steps):
        player = self.players[player_id]
        if player["in_jail"]:
            return # Handled separately

        old_pos = player["position"]
        new_pos = (old_pos + steps) % 40
        player["position"] = new_pos
        
        # Check for passing GO
        if new_pos < old_pos:
            player["money"] += 200
            self.log_event(f"{player['member'].display_name} passed GO and collected $200.")

        self.log_event(f"{player['member'].display_name} moved to {BOARD[new_pos]['name']}.")
        
        # Handle landing
        self.handle_landing(player_id, new_pos)
        
    def handle_landing(self, player_id, pos):
        tile = BOARD[pos]
        player = self.players[player_id]
        
        if tile["type"] == "tax":
            player["money"] -= tile["amount"]
            self.log_event(f"{player['member'].display_name} paid {tile['name']} of ${tile['amount']}.")
        elif tile["type"] == "go_to_jail":
            player["position"] = 10 # Jail index
            player["in_jail"] = True
            player["jail_turns"] = 0
            self.log_event(f"{player['member'].display_name} was sent to Jail!")
        elif tile["type"] in ["property", "railroad", "utility"]:
            if pos in self.properties_owned:
                owner_id = self.properties_owned[pos]
                if owner_id != player_id:
                    # Pay rent
                    rent = self.calculate_rent(pos)
                    player["money"] -= rent
                    self.players[owner_id]["money"] += rent
                    self.log_event(f"{player['member'].display_name} paid ${rent} rent to {self.players[owner_id]['member'].display_name}.")
            else:
                self.log_event(f"{tile['name']} is unowned. {player['member'].display_name} can buy it for ${tile['price']}.")

    def calculate_rent(self, pos):
        tile = BOARD[pos]
        if tile["type"] == "property":
            return tile["rent"][0]
        elif tile["type"] == "railroad":
            owner_id = self.properties_owned[pos]
            owner = self.players[owner_id]
            count = sum(1 for p in owner["properties"] if BOARD[p]["type"] == "railroad")
            return 25 * (2 ** (count - 1)) if count > 0 else 25
        elif tile["type"] == "utility":
            return 20 # Simplified utility rent for now
        return 0

    def buy_property(self, player_id, pos):
        tile = BOARD[pos]
        player = self.players[player_id]
        if pos not in self.properties_owned and player["money"] >= tile["price"]:
            player["money"] -= tile["price"]
            self.properties_owned[pos] = player_id
            player["properties"].append(pos)
            self.log_event(f"{player['member'].display_name} bought {tile['name']} for ${tile['price']}.")
            return True
        return False
