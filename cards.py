import random

# Deck of 12 Chance Cards (Global News Events)
CHANCE_CARDS = [
    {
        "id": "c1",
        "title": "🛫 International Flight",
        "description": "Advance to START/GO. Collect $200.",
        "action": "move_to",
        "target": 0,
        "pass_go": True
    },
    {
        "id": "c2",
        "title": "✈️ Global Transit Pass",
        "description": "Advance to the nearest Airport.",
        "action": "move_to_nearest",
        "tile_type": "railroad"
    },
    {
        "id": "c3",
        "title": "💼 Tariff Dividend",
        "description": "Global trade export bonus! Collect $150.",
        "action": "money",
        "amount": 150
    },
    {
        "id": "c4",
        "title": "📉 Carbon Tax Fine",
        "description": "Pay global emissions penalty of $50.",
        "action": "money",
        "amount": -50
    },
    {
        "id": "c5",
        "title": "🚨 Border Visa Violation",
        "description": "Go directly to Border Control / Jail. Do not pass START, do not collect $200.",
        "action": "go_to_jail"
    },
    {
        "id": "c6",
        "title": "🎟️ Diplomatic Passport",
        "description": "Get Out of Border Control Free. Keep this card until needed.",
        "action": "jail_free"
    },
    {
        "id": "c7",
        "title": "🏠 Property Infrastructure Audit",
        "description": "Pay $25 per house and $100 per skyscraper owned.",
        "action": "repairs",
        "house_cost": 25,
        "skyscraper_cost": 100
    },
    {
        "id": "c8",
        "title": "📈 Stock Market Boom",
        "description": "Your international investments soared! Collect $100.",
        "action": "money",
        "amount": 100
    },
    {
        "id": "c9",
        "title": "🌐 Global Summit Grant",
        "description": "Receive $50 from the United Nations development fund.",
        "action": "money",
        "amount": 50
    },
    {
        "id": "c10",
        "title": "⚡ Utility Infrastructure Fine",
        "description": "Pay $75 for global power grid upgrades.",
        "action": "money",
        "amount": -75
    },
    {
        "id": "c11",
        "title": "🏎️ Fast Travel",
        "description": "Go back 3 tiles.",
        "action": "move_relative",
        "steps": -3
    },
    {
        "id": "c12",
        "title": "💎 Luxury Tax Refund",
        "description": "Collect $100 tax rebate.",
        "action": "money",
        "amount": 100
    }
]

# Deck of 12 Community Chest Cards (World Treasury)
COMMUNITY_CHEST_CARDS = [
    {
        "id": "cc1",
        "title": "🏦 World Treasury Grant",
        "description": "Bank error in your favor! Collect $200.",
        "action": "money",
        "amount": 200
    },
    {
        "id": "cc2",
        "title": "🩺 International Healthcare Fee",
        "description": "Pay medical insurance bill of $50.",
        "action": "money",
        "amount": -50
    },
    {
        "id": "cc3",
        "title": "🎟️ Diplomatic Immunity Pass",
        "description": "Get Out of Border Control Free. Keep this card until needed.",
        "action": "jail_free"
    },
    {
        "id": "cc4",
        "title": "🎁 UNESCO Heritage Prize",
        "description": "Receive $100 for historical site preservation.",
        "action": "money",
        "amount": 100
    },
    {
        "id": "cc5",
        "title": "🎂 Birthday Fundraiser",
        "description": "It's your birthday! Collect $10 from every player.",
        "action": "collect_from_players",
        "amount": 10
    },
    {
        "id": "cc6",
        "title": "🚨 Embassy Security Detention",
        "description": "Go directly to Border Control / Jail. Do not pass START.",
        "action": "go_to_jail"
    },
    {
        "id": "cc7",
        "title": "🎓 International Scholarship",
        "description": "Pay university tuition of $100.",
        "action": "money",
        "amount": -100
    },
    {
        "id": "cc8",
        "title": "💰 Foreign Exchange Profits",
        "description": "Collect $100 currency trading proceeds.",
        "action": "money",
        "amount": 100
    },
    {
        "id": "cc9",
        "title": "📑 Tax Return Bonus",
        "description": "Collect $50 tax refund.",
        "action": "money",
        "amount": 50
    },
    {
        "id": "cc10",
        "title": "🏛️ City Renovation Assessment",
        "description": "Pay $40 per house and $115 per skyscraper owned.",
        "action": "repairs",
        "house_cost": 40,
        "skyscraper_cost": 115
    },
    {
        "id": "cc11",
        "title": "🏥 Red Cross Contribution",
        "description": "Donate $50 to global humanitarian aid.",
        "action": "money",
        "amount": -50
    },
    {
        "id": "cc12",
        "title": "🛫 Flight Refund",
        "description": "Advance to START/GO. Collect $200.",
        "action": "move_to",
        "target": 0,
        "pass_go": True
    }
]

class CardDeck:
    def __init__(self, cards: list[dict]):
        self.original_cards = cards
        self.deck = []
        self.reset_deck()

    def reset_deck(self):
        self.deck = list(self.original_cards)
        random.shuffle(self.deck)

    def draw_card(self) -> dict:
        if not self.deck:
            self.reset_deck()
        return self.deck.pop(0)

# Singletons for games
def get_fresh_chance_deck() -> CardDeck:
    return CardDeck(CHANCE_CARDS)

def get_fresh_treasury_deck() -> CardDeck:
    return CardDeck(COMMUNITY_CHEST_CARDS)
