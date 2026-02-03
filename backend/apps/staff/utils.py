from datetime import time, timedelta, datetime

def generate_time_slots(start, end, step_minutes=30):
    slots = []
    cur = datetime.combine(datetime.today(), start)
    end_dt = datetime.combine(datetime.today(), end)

    while cur < end_dt:
        slots.append(cur.time())
        cur += timedelta(minutes=step_minutes)

    return slots