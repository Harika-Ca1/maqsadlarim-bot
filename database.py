"""
database.py
SQLite ma'lumotlar bazasi bilan ishlash uchun barcha funksiyalar.
aiosqlite orqali to'liq async tarzda ishlaydi.
"""
import datetime
import aiosqlite

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    last_active TEXT,
    morning_time TEXT DEFAULT '08:00',
    evening_time TEXT DEFAULT '21:00',
    reminders_on INTEGER DEFAULT 1,
    inactivity_stage INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    why TEXT,
    deadline TEXT,
    expected_result TEXT,
    status TEXT DEFAULT 'active',
    progress INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS stages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    order_num INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(goal_id) REFERENCES goals(id)
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL,
    stage_id INTEGER,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    task_date TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    fail_reason TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(goal_id) REFERENCES goals(id),
    FOREIGN KEY(stage_id) REFERENCES stages(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    checkin_date TEXT NOT NULL,
    tasks_done INTEGER DEFAULT 0,
    tasks_total INTEGER DEFAULT 0,
    notes TEXT,
    tomorrow_change TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS streaks (
    user_id INTEGER PRIMARY KEY,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_checkin_date TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
"""


async def init_db():
    """Bazani va jadvallarni yaratish (dastur ishga tushganda bir marta chaqiriladi)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


def _row_to_dict(cursor, row):
    if row is None:
        return None
    return {d[0]: v for d, v in zip(cursor.description, row)}


async def _fetchone(query, params=()):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query, params)
        row = await cursor.fetchone()
        return _row_to_dict(cursor, row)


async def _fetchall(query, params=()):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [_row_to_dict(cursor, r) for r in rows]


async def _execute(query, params=()):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query, params)
        await db.commit()
        return cursor.lastrowid


# ---------------------------------------------------------------------------
# USERS
# ---------------------------------------------------------------------------

async def get_user_by_telegram_id(telegram_id: int):
    return await _fetchone("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))


async def get_or_create_user(telegram_id: int, username: str, first_name: str):
    user = await get_user_by_telegram_id(telegram_id)
    if user:
        return user
    today = datetime.date.today().isoformat()
    await _execute(
        "INSERT INTO users (telegram_id, username, first_name, last_active) "
        "VALUES (?, ?, ?, ?)",
        (telegram_id, username, first_name, today),
    )
    await _execute(
        "INSERT OR IGNORE INTO streaks (user_id, current_streak, longest_streak) "
        "SELECT id, 0, 0 FROM users WHERE telegram_id = ?",
        (telegram_id,),
    )
    return await get_user_by_telegram_id(telegram_id)


async def touch_user(telegram_id: int):
    """Foydalanuvchi faolligini yangilash (har qanday tugma bosilganda chaqiriladi)."""
    today = datetime.date.today().isoformat()
    await _execute(
        "UPDATE users SET last_active = ?, inactivity_stage = 0 WHERE telegram_id = ?",
        (today, telegram_id),
    )


async def update_user_settings(telegram_id: int, morning_time=None, evening_time=None,
                                reminders_on=None):
    fields = []
    params = []
    if morning_time is not None:
        fields.append("morning_time = ?")
        params.append(morning_time)
    if evening_time is not None:
        fields.append("evening_time = ?")
        params.append(evening_time)
    if reminders_on is not None:
        fields.append("reminders_on = ?")
        params.append(1 if reminders_on else 0)
    if not fields:
        return
    params.append(telegram_id)
    await _execute(f"UPDATE users SET {', '.join(fields)} WHERE telegram_id = ?", tuple(params))


async def get_all_users():
    return await _fetchall("SELECT * FROM users")


async def set_inactivity_stage(telegram_id: int, stage: int):
    await _execute(
        "UPDATE users SET inactivity_stage = ? WHERE telegram_id = ?", (stage, telegram_id)
    )


# ---------------------------------------------------------------------------
# GOALS
# ---------------------------------------------------------------------------

async def create_goal(user_id: int, title: str, why: str, deadline: str, expected_result: str):
    return await _execute(
        "INSERT INTO goals (user_id, title, why, deadline, expected_result) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, title, why, deadline, expected_result),
    )


async def get_goals(user_id: int, status: str = "active"):
    if status is None:
        return await _fetchall(
            "SELECT * FROM goals WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        )
    return await _fetchall(
        "SELECT * FROM goals WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
        (user_id, status),
    )


async def get_goal(goal_id: int):
    return await _fetchone("SELECT * FROM goals WHERE id = ?", (goal_id,))


async def delete_goal(goal_id: int):
    await _execute("DELETE FROM tasks WHERE goal_id = ?", (goal_id,))
    await _execute("DELETE FROM stages WHERE goal_id = ?", (goal_id,))
    await _execute("DELETE FROM goals WHERE id = ?", (goal_id,))


async def set_goal_status(goal_id: int, status: str):
    await _execute("UPDATE goals SET status = ? WHERE id = ?", (status, goal_id))


async def set_goal_progress(goal_id: int, progress: int):
    await _execute("UPDATE goals SET progress = ? WHERE id = ?", (progress, goal_id))


async def compute_and_update_goal_progress(goal_id: int) -> int:
    """Vazifalar bajarilish nisbatiga qarab progressni avtomatik hisoblaydi."""
    row = await _fetchone(
        "SELECT COUNT(*) as total, "
        "SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) as done, "
        "SUM(CASE WHEN status='partial' THEN 1 ELSE 0 END) as partial "
        "FROM tasks WHERE goal_id = ?",
        (goal_id,),
    )
    total = row["total"] or 0
    if total == 0:
        return 0
    done = row["done"] or 0
    partial = row["partial"] or 0
    raw = (done + partial * 0.5) / total * 100
    # eng yaqin belgilangan bosqichga yaxlitlash: 0/10/25/50/75/100
    milestones = [0, 10, 25, 50, 75, 100]
    progress = min(milestones, key=lambda m: abs(m - raw))
    if raw > 0 and progress == 0:
        progress = 10
    await set_goal_progress(goal_id, progress)
    return progress


# ---------------------------------------------------------------------------
# STAGES
# ---------------------------------------------------------------------------

async def create_stage(goal_id: int, title: str, order_num: int):
    return await _execute(
        "INSERT INTO stages (goal_id, title, order_num) VALUES (?, ?, ?)",
        (goal_id, title, order_num),
    )


async def get_stages(goal_id: int):
    return await _fetchall(
        "SELECT * FROM stages WHERE goal_id = ? ORDER BY order_num ASC", (goal_id,)
    )


async def get_stage(stage_id: int):
    return await _fetchone("SELECT * FROM stages WHERE id = ?", (stage_id,))


async def set_stage_status(stage_id: int, status: str):
    await _execute("UPDATE stages SET status = ? WHERE id = ?", (status, stage_id))


# ---------------------------------------------------------------------------
# TASKS
# ---------------------------------------------------------------------------

async def create_task(goal_id: int, user_id: int, title: str, task_date: str, stage_id=None):
    return await _execute(
        "INSERT INTO tasks (goal_id, stage_id, user_id, title, task_date) "
        "VALUES (?, ?, ?, ?, ?)",
        (goal_id, stage_id, user_id, title, task_date),
    )


async def get_tasks_by_date(user_id: int, task_date: str):
    return await _fetchall(
        "SELECT tasks.*, goals.title as goal_title FROM tasks "
        "JOIN goals ON goals.id = tasks.goal_id "
        "WHERE tasks.user_id = ? AND tasks.task_date = ? "
        "ORDER BY tasks.id ASC",
        (user_id, task_date),
    )


async def get_task(task_id: int):
    return await _fetchone("SELECT * FROM tasks WHERE id = ?", (task_id,))


async def set_task_status(task_id: int, status: str, fail_reason: str = None):
    await _execute(
        "UPDATE tasks SET status = ?, fail_reason = ? WHERE id = ?",
        (status, fail_reason, task_id),
    )


async def get_tasks_since(user_id: int, since_date: str):
    return await _fetchall(
        "SELECT * FROM tasks WHERE user_id = ? AND task_date >= ? ORDER BY task_date ASC",
        (user_id, since_date),
    )


async def get_tasks_by_goal(goal_id: int):
    return await _fetchall(
        "SELECT * FROM tasks WHERE goal_id = ? ORDER BY task_date ASC", (goal_id,)
    )


# ---------------------------------------------------------------------------
# CHECKINS
# ---------------------------------------------------------------------------

async def get_checkin(user_id: int, checkin_date: str):
    return await _fetchone(
        "SELECT * FROM checkins WHERE user_id = ? AND checkin_date = ?",
        (user_id, checkin_date),
    )


async def create_checkin(user_id: int, checkin_date: str, tasks_done: int, tasks_total: int,
                          notes: str, tomorrow_change: str):
    existing = await get_checkin(user_id, checkin_date)
    if existing:
        await _execute(
            "UPDATE checkins SET tasks_done=?, tasks_total=?, notes=?, tomorrow_change=? "
            "WHERE id = ?",
            (tasks_done, tasks_total, notes, tomorrow_change, existing["id"]),
        )
        return existing["id"]
    return await _execute(
        "INSERT INTO checkins (user_id, checkin_date, tasks_done, tasks_total, notes, "
        "tomorrow_change) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, checkin_date, tasks_done, tasks_total, notes, tomorrow_change),
    )


async def get_checkins_since(user_id: int, since_date: str):
    return await _fetchall(
        "SELECT * FROM checkins WHERE user_id = ? AND checkin_date >= ? "
        "ORDER BY checkin_date ASC",
        (user_id, since_date),
    )


# ---------------------------------------------------------------------------
# STREAKS
# ---------------------------------------------------------------------------

async def get_streak(user_id: int):
    row = await _fetchone("SELECT * FROM streaks WHERE user_id = ?", (user_id,))
    if row is None:
        await _execute(
            "INSERT INTO streaks (user_id, current_streak, longest_streak) VALUES (?, 0, 0)",
            (user_id,),
        )
        row = await _fetchone("SELECT * FROM streaks WHERE user_id = ?", (user_id,))
    return row


async def update_streak_on_checkin(user_id: int, checkin_date_str: str):
    """Check-in bajarilganda streakni hisoblab yangilaydi."""
    streak = await get_streak(user_id)
    checkin_date = datetime.date.fromisoformat(checkin_date_str)
    last = streak["last_checkin_date"]

    if last is None:
        new_current = 1
    else:
        last_date = datetime.date.fromisoformat(last)
        diff = (checkin_date - last_date).days
        if diff == 0:
            new_current = streak["current_streak"] or 1
        elif diff == 1:
            new_current = (streak["current_streak"] or 0) + 1
        else:
            new_current = 1

    new_longest = max(streak["longest_streak"] or 0, new_current)
    await _execute(
        "UPDATE streaks SET current_streak = ?, longest_streak = ?, last_checkin_date = ? "
        "WHERE user_id = ?",
        (new_current, new_longest, checkin_date_str, user_id),
    )
    return new_current, new_longest
