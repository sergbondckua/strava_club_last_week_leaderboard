import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from environs import Env

# Read environment variables
env = Env()
env.read_env()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Create a scheduler
scheduler = BlockingScheduler(timezone=env.str("TZ"))
