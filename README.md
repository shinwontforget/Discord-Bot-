# 🎲 South Park Monopoly Discord Bot

A feature-rich, interactive Discord bot that lets server members play a custom **South Park Edition Monopoly game** directly inside Discord channels! Built with Python and `discord.py` using modern Discord UI components (Buttons & Embeds).

---

## 📑 Table of Contents
- [✨ Features](#-features)
- [🎮 Commands](#-commands)
- [🛠️ Tech Stack & Requirements](#️-tech-stack--requirements)
- [🚀 Quick Start & Installation](#-quick-start--installation)
- [☁️ Hosting & Deployment](#️-hosting--deployment)
- [📜 Terms of Service (ToS)](#-terms-of-service-tos)
- [🔒 Privacy Policy](#-privacy-policy)
- [📄 License](#-license)

---

## ✨ Features

- **Interactive UI**: Buttons for rolling dice, buying properties, and ending turns—no messy text commands mid-game!
- **South Park Theme**: Custom board with iconic locations (e.g., *Kyle's Toilet*, *Gooback Tax*, *Cheesy Poofs*, *Tynacorp*, *Mephesto's Genetic Engineering Ranch*, *Aaaaand, It's Gone!*).
- **Turn-based 2-Player Gameplay**: Mention a friend to initiate a 1v1 Monopoly battle.
- **Dynamic Board Mechanics**:
  - Roll double dice and move across 40 board tiles.
  - Buy properties, utilities, and railroads.
  - Automatic rent calculation when landing on opponent-owned properties.
  - Passing GO rewards $200.
  - Go To Jail & Tax tiles handled automatically.
- **Clean In-Memory Session Management**: Isolated games per channel with clean state teardown.

---

## 🎮 Commands

| Command | Usage | Description |
| :--- | :--- | :--- |
| `!start_monopoly` | `!start_monopoly @User` | Starts a new 2-player South Park Monopoly game against the tagged opponent in the current channel. |
| `!end_monopoly` | `!end_monopoly` | Ends and cleans up any active Monopoly game running in the current channel. |

---

## 🛠️ Tech Stack & Requirements

- **Language**: Python 3.11+
- **Library**: `discord.py` 2.0+
- **Configuration**: `python-dotenv`
- **Hosting Target**: Compatible with [Discloud](https://discloudbot.com/), VPS, or local hosting.

---

## 🚀 Quick Start & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/southpark-monopoly-bot.git
cd southpark-monopoly-bot
```

### 2. Set Up Virtual Environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:
```env
DISCORD_TOKEN=your_discord_bot_token_here
```

### 5. Run the Bot
```bash
python bot.py
```

---

## ☁️ Hosting & Deployment

This project includes a `discloud.config` file pre-configured for deployment on **Discloud**:

```ini
NAME=MonopolyBot
TYPE=bot
MAIN=bot.py
RAM=100
AUTORESTART=false
VERSION=3.11
APT=tools
```

Simply zip `bot.py`, `game.py`, `requirements.txt`, and `discloud.config` and upload via the Discloud Dashboard or CLI.

---

## 📜 Terms of Service (ToS)

**Last Updated:** July 28, 2026

By inviting or using **MonopolyBot** ("the Bot") on Discord, you agree to the following Terms of Service.

### 1. Acceptance of Terms
By using the Bot, you acknowledge that you have read, understood, and agree to be bound by these terms. If you do not agree, please remove the Bot from your Discord server.

### 2. Description of Service
MonopolyBot is a free, non-commercial entertainment bot provided for Discord users to play custom-themed Monopoly games within Discord channels.

### 3. User Conduct & Fair Use
- Users agree not to abuse, exploit, or flood the Bot with automated requests or attempt to disrupt its functionality.
- Users agree not to use the Bot for any unlawful purpose or in violation of Discord's Terms of Service and Community Guidelines.

### 4. Intellectual Property Disclaimer
Monopoly is a trademark of Hasbro, Inc. South Park is owned by Comedy Partners / Paramount Global. MonopolyBot is an unofficial, fan-made educational project and is **not affiliated with, endorsed by, or sponsored by Hasbro or Paramount**.

### 5. Limitation of Liability & Warranty
The Bot is provided **"AS IS"** and **"AS AVAILABLE"** without warranties of any kind. The bot developer is not responsible for service interruptions, server downtime, or loss of game state data.

### 6. Termination of Access
The bot developer reserves the right to restrict or terminate access to the Bot for any user or Discord server that violates these Terms of Service.

---

## 🔒 Privacy Policy

**Last Updated:** July 28, 2026

This Privacy Policy explains how **MonopolyBot** ("the Bot") handles user data when operating on Discord.

### 1. Information Collected
MonopolyBot collects minimal data required exclusively for gameplay functionality:
- **Discord User ID & Username/Display Name**: Used to identify players, manage turns, track in-game balances, and display scores in Discord UI embeds.
- **Discord Channel & Guild IDs**: Used to isolate active game instances per channel.

### 2. How Data is Used
Collected data is used strictly to run the interactive board game session in real-time. Data is **never** used for marketing, user profiling, advertising, or commercial purposes.

### 3. Data Storage & Retention
- **In-Memory Storage**: All active game data (player money, position, properties owned) is stored exclusively in RAM during an active game session.
- **No Persistent Database**: The Bot does **not** write or store user data to external databases, logs, or persistent file storage.
- **Automatic Deletion**: All session data is immediately deleted when a game ends (`!end_monopoly`), when a game completes, or when the Bot restarts.

### 4. Third-Party Sharing
We **do not** sell, rent, trade, or share any user data with third parties.

### 5. User Rights & Data Removal
Because no data is stored permanently, simply ending the game session (`!end_monopoly`) removes all associated session data. If you have questions or concerns regarding your privacy, you may contact the bot developer via the contact info below or through GitHub issues.

### 6. Contact Information
For questions regarding the Terms of Service or Privacy Policy, please open an issue in this repository or contact the bot developer:
- **GitHub**: [Create an Issue](https://github.com/your-username/southpark-monopoly-bot/issues)
- **Discord Support**: Contact server administrator / bot host.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
