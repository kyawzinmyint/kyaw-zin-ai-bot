# -*- coding: utf-8 -*-
"""Kyaw Zin AI — Web UI (Dashboard + Chat) — Gradio 6.x"""
import sqlite3, json
from pathlib import Path

import gradio as gr
import requests

HOME = Path.home()
PROJ = HOME / "aiproject"
GEMINI_KEY = (HOME / ".gemini_key").read_text().strip() if (HOME/".gemini_key").exists() else ""
GROQ_KEY = (HOME / ".groq_key").read_text().strip() if (HOME/".groq_key").exists() else ""

_creds_file = HOME / ".webui_creds"
_creds = _creds_file.read_text().strip().splitlines() if _creds_file.exists() else []
WEB_USER = _creds[0] if len(_creds) > 0 else "kz"
WEB_PASS = _creds[1] if len(_creds) > 1 else ""

# ============ DB ============

# Convert list of dicts to Gradio Dataframe format
def to_table(rows):
    if not rows or "error" in rows[0]:
        return {"headers": ["Error"], "data": [[str(rows)]]}
    headers = list(rows[0].keys())
    data = [[str(r.get(h, "")) for h in headers] for r in rows]
    return {"headers": headers, "data": data}


def db_query(db_name, sql, params=()):
    try:
        path = PROJ / db_name
        if not path.exists():
            return []
        c = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)
        c.row_factory = sqlite3.Row
        rows = [dict(r) for r in c.execute(sql, params).fetchall()]
        c.close()
        return rows
    except Exception as e:
        return [{"error": str(e)}]


def _to_text(content):
    """Coerce Gradio content to plain string"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            p.get("text", "") if isinstance(p, dict) else str(p)
            for p in content
        )
    return str(content)


# ============ WEATHER TOOL ============
WEATHER_KEY_FILE = HOME / ".openweather_key"

def _extract_city(msg):
    """Extract city name from message"""
    # Common Myanmar cities
    cities = {
        "ရန်ကုန်": "Yangon", "yangon": "Yangon", "rangoon": "Yangon",
        "မန္တလေး": "Mandalay", "mandalay": "Mandalay",
        "နေပြည်တော်": "Naypyidaw", "naypyidaw": "Naypyidaw",
        "ပြင်ဦးလွင်": "Pyin Oo Lwin", "pyin oo lwin": "Pyin Oo Lwin",
        "မေမြို့": "Pyin Oo Lwin",
        "တောင်ကြီး": "Taunggyi", "taunggyi": "Taunggyi",
        "ပုသိမ်": "Pathein", "pathein": "Pathein",
        "မော်လမြိုင်": "Mawlamyine", "mawlamyine": "Mawlamyine",
        "ဗန်းမော်": "Bhamo", "bhamo": "Bhamo",
        "စစ်တွေ": "Sittwe", "sittwe": "Sittwe",
        "မြစ်ကြီးနား": "Myitkyina", "myitkyina": "Myitkyina",
        "ဟားခါး": "Hakha", "hakha": "Hakha",
        "လွိုင်ကော်": "Loikaw", "loikaw": "Loikaw",
        "ကျိုင်းတုံ": "Kengtung", "kengtung": "Kengtung",
        "ပဲခူး": "Bago", "bago": "Bago",
        "မုံရွာ": "Monywa", "monywa": "Monywa",
        "မကွေး": "Magway", "magway": "Magway",
        "ရွှေဘို": "Shwebo", "shwebo": "Shwebo",
        "မိတ္ထီလာ": "Meiktila", "meiktila": "Meiktila",
        "ပြည်": "Pyay", "pyay": "Pyay",
        "ထားဝယ်": "Dawei", "dawei": "Dawei",
        "မြိတ်": "Myeik", "myeik": "Myeik",
    }
    low = msg.lower()
    for k, v in cities.items():
        if k.lower() in low:
            return v
    # Try to find English city (capitalized word)
    import re
    m = re.search(r'\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b', msg)
    if m:
        return m.group(1)
    return None

def _get_weather(city):
    """Get weather from OpenWeatherMap"""
    if not WEATHER_KEY_FILE.exists():
        return None
    key = WEATHER_KEY_FILE.read_text().strip()
    url = ("https://api.openweathermap.org/data/2.5/weather"
           f"?q={city}&appid={key}&units=metric")
    try:
        r = requests.get(url, timeout=15)
        d = r.json()
        if r.status_code != 200:
            return f"❌ {city}: {d.get('message', 'error')}"
        main = d["main"]
        w = d["weather"][0]
        return (f"🌤 {d['name']}: {w['description']}, "
                f"{main['temp']:.0f}°C (feels {main['feels_like']:.0f}°C), "
                f"humidity {main['humidity']}%, wind {d['wind']['speed']} m/s")
    except Exception as e:
        return f"❌ Weather error: {e}"

def is_weather_query(msg):
    kws = ["weather", "ရာသီဥတု", "မိုးလေဝသ", "အပူချိန်",
           "temperature", "rain", "မိုး", "ပူ", "အေး", "climate"]
    low = msg.lower()
    return any(k in low for k in kws)

def get_stats():
    out = {}
    r = db_query("tg_memory.db", "SELECT COUNT(*) as c FROM chat_messages")
    out["total_messages"] = r[0]["c"] if r and "c" in r[0] else 0
    r = db_query("tg_memory.db", "SELECT COUNT(DISTINCT chat_id) as c FROM chat_messages")
    out["total_users"] = r[0]["c"] if r and "c" in r[0] else 0
    r = db_query("usage.db", "SELECT COUNT(*) as c FROM usage")
    out["api_calls"] = r[0]["c"] if r and "c" in r[0] else 0
    r = db_query("usage.db", "SELECT COUNT(*) as c FROM usage WHERE cached=1")
    out["cached"] = r[0]["c"] if r and "c" in r[0] else 0
    r = db_query("cache.db", "SELECT COUNT(*) as c FROM cache")
    out["cache_size"] = r[0]["c"] if r and "c" in r[0] else 0
    r = db_query("usage.db", "SELECT COUNT(*) as c FROM reminders WHERE sent=0")
    out["pending_reminders"] = r[0]["c"] if r and "c" in r[0] else 0
    return out

def get_users():
    return db_query("tg_memory.db", """
        SELECT chat_id, COUNT(*) as msg_count, MAX(created_at) as last_seen
        FROM chat_messages GROUP BY chat_id
        ORDER BY last_seen DESC LIMIT 100
    """)

def get_recent_logs(limit=50):
    return db_query("tg_memory.db", f"""
        SELECT chat_id, role, substr(content,1,80) as preview, created_at
        FROM chat_messages ORDER BY id DESC LIMIT {limit}
    """)

def get_usage_stats():
    return db_query("usage.db", """
        SELECT provider, COUNT(*) as calls, SUM(cached) as cached_calls
        FROM usage GROUP BY provider
    """)

# ============ LLM ============
def ask_gemini(prompt, history=None):
    # Use OpenAI-compatible endpoint (bypasses region block)
    url = ("https://generativelanguage.googleapis.com/v1beta/openai/"
           "chat/completions")
    msgs = [{"role": "system", "content": """You are Kyaw Zin AI Bot — a warm, natural assistant.

## LANGUAGE AUTO-DETECT (CRITICAL)
- ALWAYS reply in the SAME language the user writes in.
- English → English, Burmese → Burmese, French → French, German → German
- NEVER default to Burmese if the user wrote in another language
- NEVER mix scripts (no Korean/Chinese in English reply)

## STYLE
- Warm, natural, like a helpful friend
- Short, clear paragraphs
- Finish every sentence completely

## TRUTH
- Never fabricate facts, phone numbers, emails, URLs
- If you don't know, say "I don't know" / "ကျွန်တော် သေချာမသိပါ"
"""}]
    if history:
        for h in history[-10:]:
            role = "assistant" if h["role"] == "assistant" else h["role"]
            txt = _to_text(h.get("content", ""))
            if txt.strip():
                msgs.append({"role": role, "content": txt})
    msgs.append({"role": "user", "content": prompt})

    try:
        r = requests.post(url,
            headers={
                "Authorization": f"Bearer {GEMINI_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": "gemini-2.5-flash", "messages": msgs,
                  "temperature": 0.7, "max_tokens": 2000},
            timeout=60)
        d = r.json()
        if "choices" in d:
            return d["choices"][0]["message"]["content"]
        else:
            return f"[API] {json.dumps(d, ensure_ascii=False)[:300]}"
    except Exception as e:
        return f"[Req error] {type(e).__name__}: {e}"

def ask_groq(prompt, history=None):
    url = "https://api.groq.com/openai/v1/chat/completions"
    msgs = [{"role": "system", "content": """You are Kyaw Zin AI Bot — a warm, natural assistant.

## LANGUAGE AUTO-DETECT (CRITICAL)
- ALWAYS reply in the SAME language the user writes in.
- English → reply in English
- Burmese → reply in Burmese
- French → French, German → German, Spanish → Spanish, Thai → Thai
- Chinese → Chinese, Japanese → Japanese, Korean → Korean
- NEVER default to Burmese if the user wrote in another language
- NEVER mix scripts (no Korean/Chinese characters in English reply)

## STYLE
- Warm, natural, like a helpful friend
- Short, clear paragraphs
- Do not use tables unless comparing items
- Finish every sentence completely

## TRUTH
- Never fabricate facts, phone numbers, emails, or URLs
- If you don't know, say "I don't know" / "ကျွန်တော် သေချာမသိပါ"
"""}]
    if history:
        for h in history[-10:]:
            msgs.append({"role": h["role"], "content": h["content"]})
    msgs.append({"role": "user", "content": prompt})
    try:
        r = requests.post(url, headers={"Authorization": f"Bearer {GROQ_KEY}"},
            json={"model": "openai/gpt-oss-120b", "messages": msgs}, timeout=60)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[Groq error] {e}"

def chat_reply(message, history):
    # Weather check
    if is_weather_query(message):
        city = _extract_city(message)
        if city:
            w = _get_weather(city)
            if w:
                return w

    # Groq only (Gemini is region-blocked in Myanmar)
    reply = ask_groq(message, history)
    if "[Groq error]" in reply:
        return "တောင်းပန်ပါတယ်။ AI service ခေတ္တ မရပါ။ ခဏနေ ပြန်စမ်းပါ။"
    return reply


# ============ ADMIN DASHBOARD ============
def get_admin_stats():
    """Admin overview stats"""
    out = {}
    # Total users
    r = db_query("usage.db", "SELECT COUNT(*) as c FROM users")
    out["total_users"] = r[0]["c"] if r and "c" in r[0] else 0

    # By tier
    r = db_query("usage.db",
        "SELECT tier, COUNT(*) as c FROM users GROUP BY tier")
    tiers = {"free": 0, "premium": 0, "admin": 0}
    for row in r:
        if "tier" in row and "c" in row:
            tiers[row["tier"]] = row["c"]
    out["free_users"] = tiers.get("free", 0)
    out["premium_users"] = tiers.get("premium", 0)
    out["admin_users"] = tiers.get("admin", 0)

    # Revenue estimate (5000 MMK × premium users)
    out["revenue_mmk"] = tiers.get("premium", 0) * 5000

    # Total messages
    r = db_query("usage.db", "SELECT COUNT(*) as c FROM usage")
    out["total_messages"] = r[0]["c"] if r and "c" in r[0] else 0

    # Today messages
    from datetime import datetime as _dt
    today = _dt.now().strftime("%Y-%m-%d")
    r = db_query("usage.db",
        "SELECT COUNT(*) as c FROM usage WHERE timestamp LIKE ?",
        (today + "%",))
    out["today_messages"] = r[0]["c"] if r and "c" in r[0] else 0

    return out

def get_all_users_detailed():
    """All users with details"""
    return db_query("usage.db", """
        SELECT 
            u.user_id,
            u.username,
            u.tier,
            u.tier_expires,
            u.created_at,
            u.last_seen,
            (SELECT COUNT(*) FROM usage WHERE user_id = u.user_id) as total_msgs
        FROM users u
        ORDER BY 
            CASE u.tier 
                WHEN 'admin' THEN 1 
                WHEN 'premium' THEN 2 
                ELSE 3 
            END,
            u.last_seen DESC
    """)

def get_premium_users():
    """Premium users only"""
    return db_query("usage.db", """
        SELECT user_id, username, tier_expires, last_seen
        FROM users WHERE tier = 'premium'
        ORDER BY tier_expires DESC
    """)

def get_top_users(limit=20):
    """Top users by message count"""
    return db_query("usage.db", f"""
        SELECT 
            user_id,
            COUNT(*) as msg_count,
            MAX(timestamp) as last_seen
        FROM usage
        GROUP BY user_id
        ORDER BY msg_count DESC
        LIMIT {limit}
    """)

# ============ UI ============
with gr.Blocks(title="Kyaw Zin AI") as demo:
    gr.Markdown("# 🤖 Kyaw Zin AI — Web Console")
    gr.Markdown("@kz_helper_2026_bot | Gemini + Groq")

    with gr.Tabs():
        with gr.Tab("📊 Dashboard"):
            refresh_btn = gr.Button("🔄 Refresh", variant="primary")
            stats_box = gr.JSON(label="Stats")
            gr.Markdown("### 📈 Provider Usage")
            usage_table = gr.Dataframe(label="By Provider")
            gr.Markdown("### 👥 Users")
            users_table = gr.Dataframe(label="User list")
            gr.Markdown("### 📝 Recent Messages")
            logs_table = gr.Dataframe(label="Logs (last 50)")

            def load_dash():
                return (get_stats(),
                        to_table(get_usage_stats()),
                        to_table(get_users()),
                        to_table(get_recent_logs()))

            refresh_btn.click(load_dash, outputs=[stats_box, usage_table, users_table, logs_table])
            demo.load(load_dash, outputs=[stats_box, usage_table, users_table, logs_table])

        with gr.Tab("💬 Chat"):
            chatbot = gr.Chatbot(height=500, label="Kyaw Zin AI")
            msg_box = gr.Textbox(placeholder="မေးခွန်း ရေးပါ...", label="Message", lines=2)
            with gr.Row():
                send_btn = gr.Button("📤 Send", variant="primary")
                clear_btn = gr.Button("🗑 Clear")

            def user_submit(msg, hist):
                if not msg.strip():
                    return hist, ""
                hist = hist or []
                hist.append({"role": "user", "content": msg})
                reply = chat_reply(msg, hist)
                hist.append({"role": "assistant", "content": reply})
                return hist, ""

            send_btn.click(user_submit, [msg_box, chatbot], [chatbot, msg_box])
            msg_box.submit(user_submit, [msg_box, chatbot], [chatbot, msg_box])
            clear_btn.click(lambda: (None, ""), None, [chatbot, msg_box])


        with gr.Tab("👑 Admin"):
            gr.Markdown("### 👑 Admin Dashboard")
            gr.Markdown("*Kyaw Zin အတွက် သာ*")

            admin_refresh = gr.Button("🔄 Refresh", variant="primary")

            gr.Markdown("### 📊 Overview")
            admin_stats = gr.JSON(label="Stats")

            gr.Markdown("### 👥 All Users")
            all_users_table = gr.Dataframe(label="Users")

            gr.Markdown("### 💎 Premium Users")
            premium_table = gr.Dataframe(label="Premium")

            gr.Markdown("### 🏆 Top Users (by messages)")
            top_users_table = gr.Dataframe(label="Top 20")

            def load_admin():
                return (
                    get_admin_stats(),
                    to_table(get_all_users_detailed()),
                    to_table(get_premium_users()),
                    to_table(get_top_users())
                )

            admin_refresh.click(load_admin,
                outputs=[admin_stats, all_users_table, premium_table, top_users_table])
            demo.load(load_admin,
                outputs=[admin_stats, all_users_table, premium_table, top_users_table])

if __name__ == "__main__":
    print("🌐 Web UI: http://127.0.0.1:7860")
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        auth=("kz", "KyawZin2026!"),
        
        theme=gr.themes.Soft(),
        share=False,
        show_error=True,
    )
