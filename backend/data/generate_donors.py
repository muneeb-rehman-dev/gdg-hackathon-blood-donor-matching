"""
Run from the backend/ directory:
    python data/generate_donors.py

Generates data/donors.csv with 200 synthetic Karachi blood donors.
"""

import csv
import random
import uuid
from datetime import date, timedelta
from pathlib import Path
from faker import Faker

fake = Faker("en_US")
random.seed(42)

AREAS = {
    "Clifton":          (24.8000, 67.0200, 24.8200, 67.0400),
    "DHA":              (24.7900, 67.0600, 24.8300, 67.0900),
    "Gulshan-e-Iqbal":  (24.9200, 67.0900, 24.9500, 67.1200),
    "Nazimabad":        (24.9000, 67.0200, 24.9300, 67.0500),
    "North Karachi":    (24.9500, 67.0500, 24.9800, 67.0800),
    "Saddar":           (24.8600, 67.0000, 24.8800, 67.0200),
    "Korangi":          (24.8300, 67.1000, 24.8600, 67.1300),
    "Malir":            (24.8700, 67.1800, 24.9100, 67.2100),
    "Lyari":            (24.8600, 66.9800, 24.8900, 67.0100),
}

# Realistic Pakistan blood group distribution
BLOOD_GROUPS = ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"]
BLOOD_WEIGHTS = [38, 27, 20, 5, 4, 3, 2, 1]

URDU_NAMES = [
    "Muhammad Ali", "Ahmed Hassan", "Fatima Zahra", "Ayesha Siddiqui",
    "Omar Farooq", "Zainab Hussain", "Ali Raza", "Khadija Malik",
    "Bilal Khan", "Sara Ahmed", "Hassan Sheikh", "Nadia Iqbal",
    "Tariq Mahmood", "Sana Mirza", "Imran Butt", "Razia Begum",
    "Adnan Qureshi", "Maryam Nawaz", "Faisal Chaudhry", "Amna Baig",
    "Waseem Akram", "Hina Rabbani", "Salman Rashid", "Fozia Wahid",
    "Kamran Akmal", "Shazia Marri", "Danish Kaneria", "Uzma Khan",
]


def random_phone() -> str:
    return f"+923{random.randint(10, 49)}{random.randint(1000000, 9999999)}"


def random_lat_lng(area_name: str) -> tuple[float, float]:
    lat_min, lng_min, lat_max, lng_max = AREAS[area_name]
    return (
        round(random.uniform(lat_min, lat_max), 6),
        round(random.uniform(lng_min, lng_max), 6),
    )


def random_last_donation() -> str | None:
    # ~60% donated sometime in past year, rest never / too old to track
    if random.random() < 0.60:
        days_ago = random.randint(10, 365)
        d = date.today() - timedelta(days=days_ago)
        return d.isoformat()
    return ""


def random_response_rate() -> float:
    # Normal distribution around 0.68
    rate = random.gauss(0.68, 0.18)
    return round(max(0.10, min(0.99, rate)), 2)


def generate() -> list[dict]:
    rows = []
    area_names = list(AREAS.keys())

    for _ in range(200):
        name = random.choice(URDU_NAMES) if random.random() < 0.7 else fake.name()
        area = random.choice(area_names)
        lat, lng = random_lat_lng(area)
        blood_group = random.choices(BLOOD_GROUPS, weights=BLOOD_WEIGHTS, k=1)[0]
        health_status = "available" if random.random() < 0.85 else "unavailable"
        total_donations = random.randint(0, 20)
        last_donation = random_last_donation()

        rows.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "phone": random_phone(),
            "blood_group": blood_group,
            "area": area,
            "lat": lat,
            "lng": lng,
            "last_donation_date": last_donation,
            "health_status": health_status,
            "response_rate": random_response_rate(),
            "total_donations": total_donations,
        })

    return rows


def main() -> None:
    output_path = Path(__file__).parent / "donors.csv"
    rows = generate()

    fieldnames = [
        "id", "name", "phone", "blood_group", "area", "lat", "lng",
        "last_donation_date", "health_status", "response_rate", "total_donations",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} donors -> {output_path}")

    # Print blood group breakdown
    from collections import Counter
    bg_counts = Counter(r["blood_group"] for r in rows)
    for bg, count in sorted(bg_counts.items()):
        print(f"  {bg}: {count}")


if __name__ == "__main__":
    main()
