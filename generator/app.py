import os
import time
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone

import psycopg2


@dataclass
class UserProfile:
    weight_kg: float = 72.0


ACTIVITIES = ("sleep", "rest", "walk", "run", "bike", "strength")
MET = {
    "sleep": 0.95,
    "rest": 1.3,
    "walk": 3.3,
    "run": 8.0,
    "bike": 6.8,
    "strength": 5.0,
}
STEP_RATE_PER_MIN = {
    "sleep": (0, 0),
    "rest": (0, 10),
    "walk": (80, 130),
    "run": (150, 190),
    "bike": (0, 15),
    "strength": (0, 30),
}


def clamp(x: float, lo: float, hi: float):
    return max(lo, min(hi, x))


def now_utc():
    return datetime.now(timezone.utc)


def local_hour():
    lt = datetime.now()
    return lt.hour + lt.minute / 60.0 + lt.second / 3600.0


def circadian_activity_level(hour: float):
    g1 = math.exp(-0.5 * ((hour - 11.0) / 2.0) ** 2)
    g2 = math.exp(-0.5 * ((hour - 18.0) / 2.5) ** 2)
    night = 1.0 - math.exp(-0.5 * ((hour - 3.0) / 2.2) ** 2)
    return clamp((0.7 * g1 + 0.9 * g2) * night, 0.0, 1.0)


def choose_activity(hour: float, prev: str):
    day = circadian_activity_level(hour)
    is_night = hour < 6.0 or hour >= 23.0
    weights = {
        "sleep": 0.85 if is_night else 0.05,
        "rest": 0.15 if is_night else 0.55,
        "walk": 0.35 + 1.6 * day,
        "run": 0.05 + 0.35 * day,
        "bike": 0.04 + 0.25 * day,
        "strength": 0.04 + 0.20 * day,
    }
    if prev in weights:
        weights[prev] *= 2.2
    acts = list(weights.keys())
    ws = [weights[a] for a in acts]
    s = sum(ws)
    r = random.random()
    acc = 0.0
    for a, w in zip(acts, ws):
        acc += w / s
        if r <= acc:
            return a
    return acts[-1]


def heart_rate(activity: str):
    base = 62 + random.randint(-4, 8)
    hour = local_hour()
    circ = 3.0 * math.sin((hour - 8.0) * math.pi / 12.0)
    add = {
        "sleep": -10,
        "rest": 0,
        "walk": 25,
        "run": 70,
        "bike": 55,
        "strength": 45,
    }[activity]
    noise_sd = {
        "sleep": 2,
        "rest": 4,
        "walk": 6,
        "run": 10,
        "bike": 9,
        "strength": 8,
    }[activity]
    hr = base + circ + add + random.gauss(0, noise_sd)
    return int(round(clamp(hr, 35, 205)))


def steps(activity: str, interval_s: int):
    lo, hi = STEP_RATE_PER_MIN[activity]
    if hi <= 0:
        return 0
    cadence = random.uniform(lo, hi)
    if activity in ("walk", "strength") and random.random() < 0.10:
        cadence *= random.uniform(0.0, 0.30)
    expected = (cadence / 60.0) * interval_s
    lam = max(0.0, expected)
    noisy = random.gauss(lam, max(1.0, math.sqrt(lam)))
    return int(max(0, round(noisy)))


def calories(activity: str, user: UserProfile, interval_s: int, hr: int) -> float:
    minutes = interval_s / 60.0
    kcal = (MET[activity] * 3.5 * user.weight_kg / 200.0) * minutes
    hr_factor = 1.0 + clamp((hr - 70) / 200.0, -0.1, 0.35)
    kcal *= hr_factor
    kcal *= random.uniform(0.92, 1.08)
    return round(max(0.0, kcal), 2)


def connect_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "appdb"),
        user=os.getenv("DB_USER", "appuser"),
        password=os.getenv("DB_PASSWORD", "apppassword"),
    )


def main():
    interval_s = int(os.getenv("GEN_INTERVAL_SECONDS", "10"))
    user = UserProfile(weight_kg=float(os.getenv("USER_WEIGHT_KG", "72")))
    prev_activity = "rest"
    while True:
        try:
            conn = connect_db()
            conn.autocommit = False
            break
        except Exception as e:
            print(f"[generator] DB not ready yet: {e}")
            time.sleep(2)
    try:
        with conn:
            with conn.cursor() as cur:
                print("[generator] started, writing one row every", interval_s, "seconds")
                while True:
                    ts = now_utc()
                    hour = local_hour()
                    activity = choose_activity(hour, prev_activity)
                    hr = heart_rate(activity)
                    st = steps(activity, interval_s)
                    kcal = calories(activity, user, interval_s, hr)
                    cur.execute(
                        """
                        INSERT INTO fitness_events (ts, activity, steps, heart_rate, calories)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (ts, activity, st, hr, kcal),
                    )
                    conn.commit()
                    print(f"{ts.isoformat()} | {activity:8} | steps={st:4d} | hr={hr:3d} | kcal={kcal:6.2f}")
                    prev_activity = activity
                    time.sleep(interval_s)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
