import asyncio


async def heartbeat(seconds: int = 2):
    while True:
        await asyncio.sleep(seconds)
        yield
