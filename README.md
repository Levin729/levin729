# Dota 2 Services Bot

Telegram bot for ordering Dota 2 services including MMR boosting, behavior score improvement, hours played, calibration, coaching, and battle cup participation.

## Features

- 🎯 MMR Boost (Solo/Party)
- 🛡️ Behavior Score Improvement
- ⏱️ Hours Played
- 🎓 Account Calibration
- 👨‍🏫 Coaching Sessions
- 🏆 Battle Cup Participation
- 💰 Multiple Payment Methods
- 📝 Review System
- 👨‍💼 Admin Panel

## Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd levin729
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Create a `config.py` file in the `bot` directory with your configuration:
```python
API_TOKEN = 'your_telegram_bot_token'
ADMIN_ID = your_admin_telegram_id
```

## Running the Bot

1. Make sure your virtual environment is activated:
```bash
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Run the bot:
```bash
python run.py
```

The bot will start and you can interact with it on Telegram.

## Bot Commands

- `/start` - Start the bot and show main menu
- `/admin` - Access admin panel (admin only)

## Available Services

1. **MMR Boost**
   - Solo/Party mode
   - Custom MMR range
   - Double stars support

2. **Behavior Score**
   - Current BS input
   - Price calculation

3. **Hours Played**
   - Custom hours amount
   - Price per hour

4. **Calibration**
   - Current MMR input
   - Confidence percentage
   - Games remaining

5. **Coaching**
   - Custom hours amount
   - Professional coaching

6. **Battle Cup**
   - Solo/Party mode
   - Tier selection (3-8)
   - Price calculation

## Payment Methods

- 🌟 Telegram Stars
- 💳 Bank Card
- 💰 Cryptocurrency (USDT)
- 📱 QIWI
- 🤝 Other methods (via admin)

## Development

The project structure:
```
levin729/
├── bot/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── keyboards.py
│   ├── states.py
│   ├── price.py
│   ├── utils.py
│   └── handlers/
│       ├── __init__.py
│       ├── start.py
│       ├── order.py
│       ├── payment.py
│       ├── review.py
│       └── admin.py
├── requirements.txt
├── run.py
└── README.md
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
