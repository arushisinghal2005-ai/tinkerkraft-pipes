import feedparser
import requests
import random
import os
from flask import Flask, jsonify
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from difflib import SequenceMatcher

app = Flask(__name__)

# --- CONFIGURATION (Zero-Touch Design) ---
SOURCES = {
    "News": [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://www.artificialintelligence-news.com/feed/"
    ],
    "Research": ["http://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=10"],
    "Jargon": ["https://machinelearningmastery.com/blog/feed/"],
    "Tools": ["https://venturebeat.com/category/ai/feed/"]  # Intern D Vertical Added
}


def is_similar(a, b, threshold=0.7):
    """Checks if two headlines are semantically similar (Deduplication)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > threshold


def clean_html(raw_html):
    """Removes HTML tags and trims text."""
    if not raw_html: return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text()[:400].replace('\n', ' ').strip()


@app.route('/fetch', methods=['GET'])
def run_pipeline():
    try:
        master_data = []
        seen_titles = []

        for domain, urls in SOURCES.items():
            selected_url = random.choice(urls)
            feed = feedparser.parse(selected_url)

            count = 0
            # NEWS gets 5 slots; Research, Jargon, and Tools get 1 each
            target_limit = 5 if domain == "News" else 1

            for entry in feed.entries:
                title = entry.title

                # --- DEDUPLICATION ---
                if any(is_similar(title, seen) for seen in seen_titles):
                    print(f"Skipping duplicate: {title}")  # Console log for your debugging
                    continue

                content = {
                    "domain": domain,
                    "title": title,
                    "summary": clean_html(getattr(entry, 'summary', '')),
                    "link": entry.link,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                master_data.append(content)
                seen_titles.append(title)
                count += 1

                if count >= target_limit:
                    break

        return jsonify({"articles": master_data}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)