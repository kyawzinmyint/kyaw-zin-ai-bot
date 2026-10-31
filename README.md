# Kyaw Zin AI Bot

A production-ready AI Telegram bot with multi-language support, OCR, voice processing, and payment integration.

## Features

- AI Chat — Groq 120B, Groq 20B, Gemini 3.8-Flash (auto fallback)
- 7 Built-in Tools — Weather, News (RSS), Translation, Currency, Wikipedia, Maps, Calculator
- Multi-language — Burmese, English, Japanese, Arabic, French, German
- OCR — Image text extraction
- Voice — Speech-to-text (Whisper local)
- PDF Processing — Document analysis
- Tier System — Free (20/day), Premium (unlimited), Admin
- Web Dashboard — Gradio 6.x (real-time stats, users, logs)
- Security — Prompt injection defense (8 patterns), input validation, admin-only commands
- GDPR — Privacy consent flow, /forget all data deletion
- 24/7 Uptime — Auto-restart on Termux

## Tech Stack

- Python 3.13
- python-telegram-bot v20+
- Groq API (openai/gpt-oss-120b, openai/gpt-oss-20b)
- Google Gemini API (gemini-3.8-flash)
- SQLite (memory, usage, cache)
- Gradio 6.x (web dashboard)
- Playwright (web scraping)
- asyncio (non-blocking operations)

## Architecture

Telegram User sends message
→ handle_message (18-step pipeline)
→ validate input, rate limit, daily limit
→ auto register, extract facts, detect tool
→ math check, cache check
→ weather/news auto, RAG search, web search
→ build messages, call LLM (Groq then Gemini)
→ cache set, log usage, log message
→ reply to user

## Setup

1. Install dependencies:
pip install python-telegram-bot groq google-generativeai gradio playwright requests numpy
python -m playwright install chromium

2. Add API keys in home directory:
echo "TOKEN" > ~/.telegram_key
echo "KEY" > ~/.groq_key
echo "KEY" > ~/.gemini_key
echo "KEY" > ~/.openweather_key
echo "KEY" > ~/.newsapi_key
echo "ADMIN_ID" > ~/.admin_id
echo "groq" > ~/.ai_priority
chmod 600 ~/.telegram_key ~/.groq_key ~/.gemini_key

3. Run the bot:
cd ~/aiproject && python3 telegram_full_bot.py

4. Run web dashboard (optional):
cd ~/aiproject && python3 webui.py
Open http://127.0.0.1:7860

## Commands (42 total)

AI Chat: /start, /demo, /stats, /clear, /providers
Tools: /weather, /news, /tr, /fx, /wiki, /map, /calc
Tier: /tier, /upgrade, /pay
Admin: /admin_stats, /broadcast, /cache_clear, /list_users, /revenue
Privacy: /privacy, /forget all
Media: Photos (OCR), Voice (STT), PDFs

## Security

- Prompt Injection Defense — 8 regex patterns, blocks jailbreak attempts
- Input Validation — Length limits, spam detection, injection check
- Admin-Only Commands — 8 sensitive commands restricted
- GDPR — Privacy consent, full data deletion via /forget all
- File Permissions — API keys chmod 600

## Privacy

- Data stored: chat messages, usage stats, user tier
- Data NOT sold or shared with third parties
- Full deletion available via /forget all
- Admin forward disabled by default (requires explicit user consent)

## License

MIT

## Author

Kyaw Zin Myint
Fiverr: https://fiverr.com/users/mkyawzin_bot
Email: mkyawzin84@gmail.com
GitHub: https://github.com/kyawzinmyint

Built with love in Myanmar (UTC+6:30)
