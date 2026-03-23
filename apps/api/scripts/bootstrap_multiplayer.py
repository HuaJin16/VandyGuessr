"""Create MongoDB indexes required for multiplayer.

Run from apps/api/:
    python -m scripts.bootstrap_multiplayer
"""

import asyncio

from app.container import container
from app.core.db.mongo import close_mongo_connection, connect_to_mongo
from app.domains.multiplayer.repository import IMultiplayerGameRepository


async def bootstrap() -> None:
    await connect_to_mongo()
    try:
        repo = container.resolve(IMultiplayerGameRepository)
        await repo.ensure_indexes()
        print("Multiplayer indexes ensured")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(bootstrap())
