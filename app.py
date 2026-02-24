import feedparser
import os
import config  # Ensure your file is named config.py
import random  # <--- Added this to fix the random.choice error
from flask import Flask, jsonify, request, abort
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from difflib import SequenceMatcher

app = Flask(__name__)


# --- HELPER FUNCTIONS ---

def is_similar(a, b, threshold=0.7):
    """Prevents duplicate stories."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > threshold


def clean_html(raw_html):
    """Cleans up summaries for Gemini."""
    if not raw_html: return ""
    return BeautifulSoup(raw_html, "html.parser").get_text()[:400].strip()


# --- MAIN ROUTE ---

@app.route('/fetch', methods=['GET'])
def run_pipeline():
    # 1. SECURITY CHECK (Must match your Make.com header)
    api_key = request.headers.get('X-API-Key')
    if api_key != "MySecretProjectKey2026":
        abort(401)

        # 2. SCRAPING LOGIC
    try:
        master_data = []
        seen_titles = []

        for domain, urls in config.SOURCES.items():
            # Handle both single strings and lists of URLs
            selected_url = random.choice(urls) if isinstance(urls, list) else urls
            feed = feedparser.parse(selected_url)

            count = 0
            # Limits: 5 for News, 1 for others
            target_limit = 5 if domain == "News" else 1

            for entry in feed.entries:
                title = getattr(entry, 'title', 'No Title')

                # Deduplication check
                if any(is_similar(title, seen) for seen in seen_titles):
                    continue

                master_data.append({
                    "domain": domain,
                    "title": title,
                    "summary": clean_html(getattr(entry, 'summary', '')),
                    "link": getattr(entry, 'link', ''),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

                seen_titles.append(title)
                count += 1
                if count >= target_limit:
                    break

        return jsonify({"articles": master_data}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- RUNNER ---

if __name__ == "__main__":
    # Use port 5000 for local, or the environment port for Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)