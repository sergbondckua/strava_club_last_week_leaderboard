import asyncio
import config
from main import main


def start_scheduler() -> None:
    """Start scheduler and add tasks to apscheduler"""

    def run_main():
        asyncio.run(main())

    config.scheduler.add_job(
        name="leaderboard_start_process",
        func=run_main,
        trigger="cron",
        second=0,
        minute=0,
        hour=10,
        day_of_week="mon",
    )

    # Start the scheduler
    config.scheduler.start()


if __name__ == "__main__":
    start_scheduler()
