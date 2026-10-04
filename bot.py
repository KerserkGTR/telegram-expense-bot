"""Telegram expense tracker bot (aiogram 3 + SQLite).

Commands:
    /add <amount> <category> [note]   add an expense
    /today                            today's total and breakdown
    /month                            current month by category
    /export                           CSV of all expenses
    /undo                             delete the last expense

Usage:
    BOT_TOKEN=123:abc python bot.py
"""
import asyncio
import csv
import io
import os
import sqlite3
from datetime import date

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, Message

DB_PATH = os.getenv("DB_PATH", "expenses.db")
dp = Dispatcher()


def db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT ''
        )"""
    )
    return con


def breakdown(rows: list[tuple[str, float]]) -> str:
    if not rows:
        return "No expenses yet."
    total = sum(a for _, a in rows)
    lines = [f"{c}: {a:.2f}" for c, a in rows]
    return "\n".join(lines) + f"\n-----\nTotal: {total:.2f}"


@dp.message(Command("start", "help"))
async def start(m: Message) -> None:
    await m.answer(
        "Expense tracker.\n/add 12.5 food lunch\n/today\n/month\n/export\n/undo"
    )


@dp.message(Command("add"))
async def add(m: Message, command: CommandObject) -> None:
    parts = (command.args or "").split(maxsplit=2)
    try:
        amount = float(parts[0].replace(",", "."))
        category = parts[1].lower()
    except (IndexError, ValueError):
        await m.answer("Format: /add <amount> <category> [note]")
        return
    if amount <= 0:
        await m.answer("Amount must be positive.")
        return
    note = parts[2] if len(parts) > 2 else ""
    with db() as con:
        con.execute(
            "INSERT INTO expenses (user_id, day, amount, category, note) VALUES (?,?,?,?,?)",
            (m.from_user.id, date.today().isoformat(), amount, category, note),
        )
    await m.answer(f"Added: {amount:.2f} / {category}")


@dp.message(Command("today"))
async def today(m: Message) -> None:
    with db() as con:
        rows = con.execute(
            "SELECT category, SUM(amount) FROM expenses WHERE user_id=? AND day=? "
            "GROUP BY category ORDER BY 2 DESC",
            (m.from_user.id, date.today().isoformat()),
        ).fetchall()
    await m.answer(breakdown(rows))


@dp.message(Command("month"))
async def month(m: Message) -> None:
    with db() as con:
        rows = con.execute(
            "SELECT category, SUM(amount) FROM expenses WHERE user_id=? AND day LIKE ? "
            "GROUP BY category ORDER BY 2 DESC",
            (m.from_user.id, date.today().strftime("%Y-%m") + "%"),
        ).fetchall()
    await m.answer(breakdown(rows))


@dp.message(Command("undo"))
async def undo(m: Message) -> None:
    with db() as con:
        row = con.execute(
            "SELECT id, amount, category FROM expenses WHERE user_id=? ORDER BY id DESC LIMIT 1",
            (m.from_user.id,),
        ).fetchone()
        if not row:
            await m.answer("Nothing to undo.")
            return
        con.execute("DELETE FROM expenses WHERE id=?", (row[0],))
    await m.answer(f"Removed: {row[1]:.2f} / {row[2]}")


@dp.message(Command("export"))
async def export(m: Message) -> None:
    with db() as con:
        rows = con.execute(
            "SELECT day, amount, category, note FROM expenses WHERE user_id=? ORDER BY id",
            (m.from_user.id,),
        ).fetchall()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "amount", "category", "note"])
    w.writerows(rows)
    await m.answer_document(BufferedInputFile(buf.getvalue().encode("utf-8-sig"), "expenses.csv"))


async def main() -> None:
    bot = Bot(os.environ["BOT_TOKEN"])
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
