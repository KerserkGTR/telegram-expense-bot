# Telegram expense tracker bot

aiogram 3 + SQLite. Per-user data, no external services.

| Command | What it does |
|---|---|
| `/add 12.5 food lunch` | add an expense |
| `/today` | today's breakdown by category |
| `/month` | current month by category |
| `/export` | CSV of all expenses |
| `/undo` | remove the last entry |

```bash
pip install aiogram
export BOT_TOKEN=<token from @BotFather>
python bot.py
```

Extensible: budgets and alerts, multi-currency, Google Sheets sync, inline buttons.
