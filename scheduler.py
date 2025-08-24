from datetime import datetime
from zoneinfo import ZoneInfo

from config import SCHEDULE_START_HOUR, SCHEDULE_END_HOUR

BST = ZoneInfo("Europe/London")

def within_bst_window(now=None):
    now = now or datetime.now(BST)
    h = now.hour
    return SCHEDULE_START_HOUR <= h <= SCHEDULE_END_HOUR
