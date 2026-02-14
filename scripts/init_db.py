"""One-time script to create all tables (dev only). Use Alembic for production."""

import asyncio

from app.db.base import Base
from app.db.session import engine

# Import models so they register with Base
from app.models import career, job, resume, roadmap, user  # noqa: F401


async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")


if __name__ == "__main__":
    asyncio.run(init())
