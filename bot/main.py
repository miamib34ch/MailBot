import asyncio

from mail_manager import check_email
from config import CHECK_TIMING_SECONDS


async def main():
    while True:
        await check_email()
        await asyncio.sleep(CHECK_TIMING_SECONDS)

if __name__ == '__main__':
    asyncio.run(main())