import json, os, pathlib
from flask import Flask, request, Response, jsonify
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from news_fetcher import fetch_headlines, get_default_feeds, format_sms

load_dotenv()
DATA_FILE = pathlib.Path(__file__).parent / "subscribers.json"

app = Flask(__name__)

def load_subscribers():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_subscribers(subs):
    DATA_FILE.write_text(json.dumps(subs, ensure_ascii=False, indent=2), encoding="utf-8")

def is_subscribed(subs, phone):
    return any(s.get("phone") == phone and s.get("active", True) for s in subs)

def subscribe(subs, phone):
    for s in subs:
        if s.get("phone") == phone:
            s["active"] = True
            return subs
    subs.append({"phone": phone, "active": True})
    return subs

def unsubscribe(subs, phone):
    for s in subs:
        if s.get("phone") == phone:
            s["active"] = False
    return subs

@app.route("/")
def home():
    return "Offline News SMS Bot is running!"

@app.route("/api/news")
def api_news():
    feeds = get_default_feeds()
    headlines = fetch_headlines(feeds, max_items=int(os.environ.get("MAX_HEADLINES", "5")))
    return jsonify({"headlines": headlines})

@app.route("/api/send", methods=["POST"])
def api_send():
    feeds = get_default_feeds()
    headlines = fetch_headlines(feeds, max_items=int(os.environ.get("MAX_HEADLINES", "5")))
    if not headlines:
        headlines = ["No news available"]

    body = "Top News:\n" + "\n".join([f"- {h}" for h in headlines])

    
    MAX_SEGMENTS = 2
    MAX_CHARS = 70 * MAX_SEGMENTS  
    if len(body) > MAX_CHARS:
        body = body[:MAX_CHARS - 3] + "..."

    client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    msg = client.messages.create(
        body=body,
        from_=os.getenv("TWILIO_PHONE"),
        to=os.getenv("USER_PHONE")
    )
    return jsonify({"status": "sent", "sid": msg.sid, "headlines": headlines})

@app.post("/sms")
def sms_webhook():
    incoming = request.form.get("Body", "").strip()
    from_phone = request.form.get("From", "")
    subs = load_subscribers()
    resp = MessagingResponse()

    cmd = incoming.upper()
    if cmd.startswith("START"):
        subs = subscribe(subs, from_phone)
        save_subscribers(subs)
        resp.message("Subscribed! You'll get daily headlines. Reply STOP to unsubscribe. Send NEWS anytime for instant headlines.")
    elif cmd.startswith("STOP"):
        subs = unsubscribe(subs, from_phone)
        save_subscribers(subs)
        resp.message("Unsubscribed. Reply START to re-subscribe.")
    elif cmd.startswith("NEWS"):
        feeds = get_default_feeds()
        headlines = fetch_headlines(feeds, max_items=int(os.environ.get("MAX_HEADLINES", "5")))
        if headlines:
            body = "Top News:\n" + "\n".join([f"- {h}" for h in headlines])
            # Trim
            MAX_SEGMENTS = 2
            MAX_CHARS = 70 * MAX_SEGMENTS
            if len(body) > MAX_CHARS:
                body = body[:MAX_CHARS - 3] + "..."
        else:
            body = "No headlines found right now. Try again later."
        resp.message(body)
    else:
        resp.message("Hi! Reply START to subscribe, STOP to unsubscribe, or NEWS for latest headlines.")

    return Response(str(resp), mimetype="application/xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
