"""
VIRAL RADAR — Backend Script
=============================
Maqsad: Duniya bhar mein pichle 30 din ke andar bane naye YouTube channels
dhoondhna jo fast viral/trend ho rahe hain — Long-form aur Shorts alag alag,
aur har channel ka asal SEO data (title patterns, tags, hashtags, description
keywords) nikalna — taake pata chale wo channels SEO ke liye kya use kar rahe hain.

ZAROORI: Isko chalane se pehle aapko FREE YouTube Data API v3 key chahiye.
Kaise banayen:
  1. https://console.cloud.google.com par jayein
  2. Naya project banayein
  3. "YouTube Data API v3" enable karein
  4. Credentials > API Key banayein
  5. Neeche API_KEY variable mein paste karein

Install (ek dafa):
    pip install google-api-python-client python-dateutil

Chalane ka tareeka:
    python viral_radar.py
"""

import os
import re
import json
import datetime
from dateutil import parser as date_parser
from googleapiclient.discovery import build

# ---------------------------------------------------------------------
# CONFIG — yahan apni values daalein
# ---------------------------------------------------------------------
API_KEY = os.environ.get("YOUTUBE_API_KEY", "YAHAN_APNI_API_KEY_DAALEIN")

# Jitni niches track karni hain (aap is list ko jitna chahein utna bara kar sakte hain)
NICHES = [
    "psychology", "stoicism", "storytelling", "true crime", "relationship advice",
    "personal finance", "crypto", "ai tools", "gaming", "fitness", "skincare",
    "mukbang", "travel vlog", "comedy sketch", "science facts", "digital art",
    "cricket highlights", "asmr", "faceless youtube channel", "astrology",
    # ... aap yahan jitni chahein niches add kar sakte hain (1000 tak bhi)
]

COUNTRIES = ["US", "CA", "GB", "DE", "FR", "PK", "IN", "BR", "ID", "NG",
             "SA", "JP", "KR", "TR", "PH", "ZA", "AU", "ES", "IT", "PL"]

MAX_CHANNEL_AGE_DAYS = 30
RESULTS_PER_NICHE = 5           # har niche se kitne channels lene hain
OUTPUT_FILE = "viral_radar_output.json"
PROGRESS_FILE = "scan_progress.json"

# Free API quota roz ~10,000 units hoti hai. Har niche+country combo scan
# karne mein takreeban 100-150 units lagti hain — is liye hum ek scan mein
# sirf itni combos scan karte hain jitni quota mein aa jayein, aur agli
# baar chalane par WAHIN se aage shuru karte hain (progress file se).
COMBOS_PER_RUN = 60

# ---------------------------------------------------------------------
# BATCH / PROGRESS TRACKING (quota bachane ke liye)
# ---------------------------------------------------------------------

def load_progress():
    """Pichli dafa scan kahan tak hua tha, wahan se resume karne ke liye."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {"last_index": 0}


def save_progress(index):
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"last_index": index}, f)

# ---------------------------------------------------------------------
# CORE FUNCTIONS
# ---------------------------------------------------------------------

def get_client():
    """YouTube API client banata hai."""
    return build("youtube", "v3", developerKey=API_KEY)


def search_recent_channels(youtube, niche_keyword, region_code):
    """
    Ek niche/keyword ke liye channels dhoondhta hai jo recently upload kar rahe hain.
    Note: YouTube API channel 'creation date' seedha search se nahi milti —
    isliye hum pehle videos search karte hain, phir un videos ke channels
    ki 'publishedAt' (channel creation) check karte hain.
    """
    search_response = youtube.search().list(
        q=niche_keyword,
        part="snippet",
        type="video",
        order="date",              # sabse naye uploads pehle
        regionCode=region_code,
        maxResults=RESULTS_PER_NICHE,
        publishedAfter=(datetime.datetime.utcnow() -
                        datetime.timedelta(days=MAX_CHANNEL_AGE_DAYS)).isoformat("T") + "Z"
    ).execute()

    channel_ids = list({item["snippet"]["channelId"] for item in search_response.get("items", [])})
    return channel_ids


def get_channel_details(youtube, channel_id):
    """Ek channel ki subscriber count, creation date, views waghera nikalta hai."""
    resp = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    ).execute()

    if not resp.get("items"):
        return None

    item = resp["items"][0]
    created_at = date_parser.parse(item["snippet"]["publishedAt"])
    age_days = (datetime.datetime.now(datetime.timezone.utc) - created_at).days

    if age_days > MAX_CHANNEL_AGE_DAYS:
        return None  # 30 din se purana channel skip karo

    stats = item.get("statistics", {})
    return {
        "channel_id": channel_id,
        "channel_name": item["snippet"]["title"],
        "created_at": created_at.strftime("%Y-%m-%d"),
        "age_days": age_days,
        "subscribers": int(stats.get("subscriberCount", 0)),
        "total_views": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
    }


def extract_seo_data(youtube, video_ids):
    """
    Channel ke recent videos se asal SEO data nikalta hai jo woh use kar rahe hain:
      - title (aur uska pattern, jaise "POV:", "Wait for it", numbers waghera)
      - tags (YouTube 'keywords' field — creator khud manually daalta hai)
      - hashtags (title/description ke andar se #something nikal ke)
      - description ka pehla hissa (jahan SEO keywords stuff hote hain)

    Yeh sab PUBLIC data hai — koi private/copyrighted cheez nahi nikali ja rahi,
    sirf woh info jo channel khud publicly video ke sath post karta hai.
    """
    if not video_ids:
        return {"titles": [], "tags": [], "hashtags": [], "description_snippets": []}

    resp = youtube.videos().list(
        part="snippet",
        id=",".join(video_ids)
    ).execute()

    all_titles, all_tags, all_hashtags, desc_snippets = [], [], [], []

    for item in resp.get("items", []):
        snip = item["snippet"]
        title = snip.get("title", "")
        description = snip.get("description", "")
        tags = snip.get("tags", [])  # creator ke manually daale hue keywords

        all_titles.append(title)
        all_tags.extend(tags)

        # Title aur description dono se hashtags nikalna
        found_hashtags = re.findall(r"#\w+", title + " " + description)
        all_hashtags.extend(found_hashtags)

        desc_snippets.append(description[:150])  # sirf shuru ka hissa (SEO keywords wahan hote hain)

    return {
        "titles": all_titles,
        "tags": list(dict.fromkeys(all_tags)),          # duplicates hata kar
        "hashtags": list(dict.fromkeys(all_hashtags)),   # duplicates hata kar
        "description_snippets": desc_snippets,
    }


def calculate_growth_rate(channel):
    """
    Growth rate ka simple formula:
    (subscribers / age_days) = daily average growth
    Isko aap history data store karke aur behtar bana sakte hain
    (i.e. kal ke subs vs aaj ke subs compare karke asal daily % nikalna).
    """
    if channel["age_days"] == 0:
        channel["age_days"] = 1
    daily_growth = channel["subscribers"] / channel["age_days"]
    channel["daily_growth_avg"] = round(daily_growth, 2)
    return channel


def get_recent_video_ids(youtube, channel_id, max_results=5):
    """Channel ke recent videos ki ID list nikalta hai (ek hi jagah se reuse hota hai)."""
    resp = youtube.search().list(
        part="id",
        channelId=channel_id,
        order="date",
        maxResults=max_results,
        type="video"
    ).execute()
    return [item["id"]["videoId"] for item in resp.get("items", [])]


def classify_long_or_short(youtube, video_ids):
    """
    Video IDs check karke pata lagata hai ke channel mostly Shorts bana raha hai
    ya Long-form. (Heuristic: video duration < 60 sec = Short)
    """
    if not video_ids:
        return "unknown"

    details = youtube.videos().list(part="contentDetails", id=",".join(video_ids)).execute()
    short_count = 0
    for v in details.get("items", []):
        duration = v["contentDetails"]["duration"]  # ISO 8601, e.g. PT45S
        if "M" not in duration and "H" not in duration:
            short_count += 1

    return "short" if short_count >= len(video_ids) / 2 else "long"


def run_full_scan():
    """
    Ek batch scan chalata hai: sirf COMBOS_PER_RUN jitne niche+country
    combinations scan karta hai (quota bachane ke liye), aur agli baar
    wahin se aage badhta hai. Purane results ke sath naye merge karta hai.
    """
    youtube = get_client()

    # Har mumkin niche+country combination ki poori list banao
    all_combos = [(n, c) for n in NICHES for c in COUNTRIES]

    progress = load_progress()
    start = progress["last_index"] % len(all_combos)
    batch = (all_combos[start:] + all_combos[:start])[:COMBOS_PER_RUN]

    # Pichla saved data load karo (agar hai) taake naya data usme merge ho
    existing = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)

    new_results = []

    for niche, country in batch:
        try:
            channel_ids = search_recent_channels(youtube, niche, country)
            for cid in channel_ids:
                details = get_channel_details(youtube, cid)
                if not details:
                    continue
                details["niche"] = niche
                details["country"] = country
                details = calculate_growth_rate(details)

                video_ids = get_recent_video_ids(youtube, cid)
                details["format"] = classify_long_or_short(youtube, video_ids)
                details["seo_data"] = extract_seo_data(youtube, video_ids)

                new_results.append(details)
        except Exception as e:
            print(f"[SKIP] {niche} / {country}: {e}")
            continue

    # Purane aur naye results ko channel_id ke hisaab se merge karo (duplicate hata kar)
    merged = {c["channel_id"]: c for c in existing}
    for c in new_results:
        merged[c["channel_id"]] = c

    combined = list(merged.values())
    combined.sort(key=lambda x: x["daily_growth_avg"], reverse=True)
    top_100 = combined[:100]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(top_100, f, indent=2, ensure_ascii=False)

    # Progress aage badhao taake agli dafa naye combos scan hon
    next_index = (start + COMBOS_PER_RUN) % len(all_combos)
    save_progress(next_index)

    print(f"Batch scan complete: {len(batch)} combos scanned "
          f"({start} to {start + len(batch)} of {len(all_combos)}).")
    print(f"Total unique channels saved: {len(top_100)} → {OUTPUT_FILE}")
    print(f"Agli baar scan {next_index}th combo se shuru hoga.")
    return top_100


if __name__ == "__main__":
    if API_KEY == "YAHAN_APNI_API_KEY_DAALEIN":
        print("⚠️  Pehle apni YouTube API key daalein (upar API_KEY variable mein).")
    else:
        run_full_scan()
