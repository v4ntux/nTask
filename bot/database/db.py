import aiosqlite
from pathlib import Path


class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.connection: aiosqlite.Connection | None = None

    async def setup(self) -> None:
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        self.connection = await aiosqlite.connect(self.db_path)
        await self.connection.execute("PRAGMA foreign_keys = ON")
        await self.create_tables()

    async def create_tables(self) -> None:
        assert self.connection is not None
        await self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language TEXT NOT NULL DEFAULT 'ru',
                notify_3_day INTEGER NOT NULL DEFAULT 1,
                notify_14_day INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS concrete_batches (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                grade TEXT NOT NULL,
                location TEXT NOT NULL,
                picket TEXT NOT NULL,
                volume REAL NOT NULL,
                remaining_volume REAL NOT NULL DEFAULT 0.0,
                poured_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                notify_3_day INTEGER NOT NULL DEFAULT 0,
                notify_7_day INTEGER NOT NULL DEFAULT 1,
                notify_14_day INTEGER NOT NULL DEFAULT 0,
                notify_28_day INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS test_schedules (
                id INTEGER PRIMARY KEY,
                batch_id INTEGER NOT NULL,
                days INTEGER NOT NULL,
                volume REAL NOT NULL,
                scheduled_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                notify INTEGER NOT NULL DEFAULT 1,
                UNIQUE(batch_id, days),
                FOREIGN KEY(batch_id) REFERENCES concrete_batches(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY,
                schedule_id INTEGER NOT NULL,
                completed_at TEXT NOT NULL,
                result TEXT NOT NULL,
                comment TEXT,
                tested_volume REAL,
                FOREIGN KEY(schedule_id) REFERENCES test_schedules(id) ON DELETE CASCADE
            );
            """
        )
        await self.connection.commit()
        # Ensure columns exist for older databases
        try:
            await self.connection.execute("ALTER TABLE concrete_batches ADD COLUMN remaining_volume REAL DEFAULT 0.0")
        except Exception:
            pass
        try:
            await self.connection.execute("ALTER TABLE concrete_batches ADD COLUMN notify_3_day INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        try:
            await self.connection.execute("ALTER TABLE concrete_batches ADD COLUMN notify_7_day INTEGER NOT NULL DEFAULT 1")
        except Exception:
            pass
        try:
            await self.connection.execute("ALTER TABLE concrete_batches ADD COLUMN notify_14_day INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        try:
            await self.connection.execute("ALTER TABLE concrete_batches ADD COLUMN notify_28_day INTEGER NOT NULL DEFAULT 1")
        except Exception:
            pass
        try:
            await self.connection.execute("ALTER TABLE test_results ADD COLUMN tested_volume REAL")
        except Exception:
            pass
        try:
            await self.connection.execute("ALTER TABLE test_schedules ADD COLUMN notify INTEGER NOT NULL DEFAULT 1")
        except Exception:
            pass
        try:
            await self.connection.execute("ALTER TABLE users ADD COLUMN language TEXT NOT NULL DEFAULT 'ru'")
        except Exception:
            pass
        try:
            await self.connection.execute("ALTER TABLE users ADD COLUMN notify_3_day INTEGER NOT NULL DEFAULT 1")
        except Exception:
            pass
        try:
            await self.connection.execute("ALTER TABLE users ADD COLUMN notify_14_day INTEGER NOT NULL DEFAULT 1")
        except Exception:
            pass
        # initialize remaining_volume for rows where it's zero or null
        try:
            await self.connection.execute("UPDATE concrete_batches SET remaining_volume = volume WHERE remaining_volume IS NULL OR remaining_volume = 0.0")
        except Exception:
            pass
        await self.connection.commit()

    async def execute(self, query: str, params: tuple | None = None) -> aiosqlite.Cursor:
        assert self.connection is not None
        if params is None:
            return await self.connection.execute(query)
        return await self.connection.execute(query, params)

    async def fetchone(self, query: str, params: tuple | None = None):
        cursor = await self.execute(query, params)
        return await cursor.fetchone()

    async def fetchall(self, query: str, params: tuple | None = None):
        cursor = await self.execute(query, params)
        return await cursor.fetchall()

    async def commit(self) -> None:
        assert self.connection is not None
        await self.connection.commit()

    async def close(self) -> None:
        if self.connection is not None:
            await self.connection.close()
