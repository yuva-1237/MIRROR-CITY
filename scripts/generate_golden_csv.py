import os
import csv
import math
from datetime import datetime, timedelta, timezone

fixtures_dir = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures")
os.makedirs(fixtures_dir, exist_ok=True)
csv_path = os.path.join(fixtures_dir, "golden_corridor_week.csv")

corridors = {
    "omr_it_expressway": {"free_flow": 58.0, "peak_speed": 22.0, "base_cong": 68.0},
    "anna_salai": {"free_flow": 48.0, "peak_speed": 19.5, "base_cong": 65.0},
    "gst_road": {"free_flow": 55.0, "peak_speed": 24.5, "base_cong": 62.0},
    "poonamallee_high_road": {"free_flow": 45.0, "peak_speed": 18.0, "base_cong": 58.0},
    "marina_coast_road": {"free_flow": 46.0, "peak_speed": 29.0, "base_cong": 38.0},
}

start_time = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
rows = []

# 7 days, 96 intervals of 15 min per day = 672 points per corridor
for day in range(7):
    for interval in range(96):
        curr_time = start_time + timedelta(days=day, minutes=15 * interval)
        time_str = curr_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        hour = interval / 4.0

        morning_peak = math.exp(-((hour - 9.2) ** 2) / 2.5)
        evening_peak = math.exp(-((hour - 18.5) ** 2) / 3.0)
        commute_factor = max(morning_peak, evening_peak)

        for corr_name, params in corridors.items():
            free_flow = params["free_flow"]
            peak_speed = params["peak_speed"]
            speed = free_flow - (free_flow - peak_speed) * commute_factor
            noise = 1.2 * math.sin(interval * 0.4)
            speed = max(10.0, min(free_flow, round(speed + noise, 1)))
            cong = max(5.0, min(95.0, round((1.0 - speed / free_flow) * 100.0, 1)))

            rows.append({
                "city_code": "chennai",
                "corridor": corr_name,
                "observed_at": time_str,
                "speed_kmh": speed,
                "congestion_pct": cong,
                "source": "calibrated"
            })

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["city_code", "corridor", "observed_at", "speed_kmh", "congestion_pct", "source"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} golden corridor observations into {csv_path}")
