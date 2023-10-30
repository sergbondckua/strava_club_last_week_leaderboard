import asyncio
import config
from main import main


async def start_scheduler() -> None:
    """Start scheduler and add tasks to apscheduler"""

    def run_main():
        asyncio.run(main())

    config.scheduler.add_job(
        func=run_main,  # Use the wrapper function that awaits 'main'
        trigger="cron",
        second=0,
        minute=28,
        hour=18,
        day_of_week="mon",
    )

    # Start the scheduler
    config.scheduler.start()


if __name__ == "__main__":
    asyncio.run(start_scheduler())
