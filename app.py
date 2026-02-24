import feedparser
import os
import config  # <--- This connects to your new config.py
from flask import Flask, jsonify
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from difflib import SequenceMatcher
from flask import request, abort


@app.route('/fetch', methods=['GET'])
def run_pipeline():
    # 1. Check for the secret key in the header
    api_key = request.headers.get('X-API-Key')
    if api_key != "MySecretProjectKey2026":  # Use your own secret string here
        abort(401)  # If it doesn't match, tell them "Unauthorized"

    # ... rest of your code ...
app = Flask(__name__)


def is_similar(a, b, threshold=0.7):
    """Prevents duplicate stories (Intern A requirement)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > threshold


def clean_html(raw_html):
    """Cleans up summaries for Gemini."""
    if not raw_html: return ""
    return BeautifulSoup(raw_html, "html.parser").get_text()[:400].strip()


@app.route('/fetch', methods=['GET'])
def run_pipeline():
    try:
        master_data = []
        seen_titles = []

        # Pulling SOURCES directly from config.py
        for domain, urls in config.SOURCES.items():
            selected_url = random.choice(urls) if isinstance(urls, list) else urls
            feed = feedparser.parse(selected_url)

            count = 0
            # Set limits per Intern Assignment (A, B, C, D)
            target_limit = 5 if domain == "News" else 1

            for entry in feed.entries:
                title = entry.title
                if any(is_similar(title, seen) for seen in seen_titles):
                    continue

                master_data.append({
                    "domain": domain,
                    "title": title,
                    "summary": clean_html(getattr(entry, 'summary', '')),
                    "link": entry.link,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                seen_titles.append(title)
                count += 1
                if count >= target_limit: break

        return jsonify({"articles": master_data}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)