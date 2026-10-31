import os
import requests


def tool_weather(city):
    key_file = os.path.expanduser("~/.openweather_key")
    if not os.path.exists(key_file):
        return "Weather API key not configured"

    # Actual Burmese city name spellings
    city_map = {
        "ရန်ကုန်": "Yangon", "ရန်ကုန်မြို့": "Yangon",
        "မန္တလေး": "Mandalay", "မန်းတလေး": "Mandalay", "မန္တလေးမြို့": "Mandalay",
        "နေပြည်တော်": "Naypyidaw",
        "ပြင်ဦးလွင်": "Pyin Oo Lwin", "ပြင်ဦးလွင်မြို့": "Pyin Oo Lwin",
        "တောင်ကြီး": "Taunggyi",
        "မော်လမြိုင်": "Mawlamyine",
        "ပုသိမ်": "Pathein",
        "စစ်တွေ": "Sittwe",
        "မြစ်ကြီးနား": "Myitkyina"
    }
    
    # Find city name in user text and replace with English
    for mm_city, en_city in city_map.items():
        if mm_city in city:
            city = en_city
            break

    try:
        with open(key_file, "r", encoding="utf-8") as f:
            api_key = f.read().strip()

        if not api_key:
            return "Weather API key not configured"

        data = None
        response = None
        # Try city, then city,MM (Myanmar)
        for _q in [city, f"{city},MM", f"{city},US", f"{city},GB"]:
            response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": _q,
                    "appid": api_key,
                    "units": "metric",
                    "lang": "en",
                },
                timeout=10,
            )
            data = response.json()
            if response.status_code == 200:
                break

        if response.status_code != 200:
            return "Weather: " + str(data.get("message", "not found"))

        description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        return f"🌤 {city.title()}: {description}, {temperature}°C"

    except requests.Timeout:
        return "Weather service timed out"
    except Exception as error:
        return "Weather error: " + str(error)[:80]


def tool_translate(text, target_language="en"):
    try:
        response = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx",
                "sl": "auto",
                "tl": target_language,
                "dt": "t",
                "q": text,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return data[0][0][0]

    except requests.Timeout:
        return "Translation service timed out"
    except Exception as error:
        return "Translation error: " + str(error)[:80]


def tool_currency(from_currency, to_currency, amount=1):
    try:
        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()
        amount = float(amount)

        response = requests.get(
            "https://api.exchangerate-api.com/v4/latest/" + from_currency,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        rate = data.get("rates", {}).get(to_currency)
        if rate is None:
            return f"Invalid currency code: {from_currency} or {to_currency}"

        result = amount * float(rate)
        return f"💱 {amount:g} {from_currency} = {result:,.2f} {to_currency}"

    except ValueError:
        return "Usage: /fx USD MMK 1"
    except requests.Timeout:
        return "Currency service timed out"
    except Exception as error:
        return "Currency error: " + str(error)[:80]


def _wikipedia_extract(api_url, query):
    response = requests.get(
        api_url,
        params={
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "exintro": 1,
            "explaintext": 1,
            "titles": query,
            "redirects": 1,
        },
        headers={"User-Agent": "KyawZinBot/1.0"},
        timeout=10,
    )
    response.raise_for_status()

    pages = response.json().get("query", {}).get("pages", {})
    for page_id, page in pages.items():
        extract = (page.get("extract") or "").strip()
        if page_id != "-1" and extract:
            title = page.get("title", query)
            return f"📖 {title}: {extract[:600]}"

    return None


def tool_wikipedia(query):
    try:
        answer = _wikipedia_extract("https://en.wikipedia.org/w/api.php", query)
        if answer:
            return answer

        answer = _wikipedia_extract("https://my.wikipedia.org/w/api.php", query)
        if answer:
            return answer

        return f"Wikipedia: {query} not found"

    except requests.Timeout:
        return "Wikipedia service timed out"
    except Exception as error:
        return "Wikipedia error: " + str(error)[:80]


def tool_maps(place):
    """Map search: place names (English) + Google Maps link."""
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": place, "format": "json", "limit": 3, "accept-language": "en"},
            headers={"User-Agent": "KyawZinBot/1.0"},
            timeout=10,
        )
        response.raise_for_status()
        places = response.json()
        
        gmaps_url = "https://www.google.com/maps/search/" + place.replace(" ", "+")
        
        if not places:
            return f"No location found for '{place}'.\n🗺 Google Maps: {gmaps_url}"
        
        lines_out = [f"🗺 **Map: {place.upper() if len(place) <= 3 else place.title()}**", ""]
        for i, item in enumerate(places[:3], 1):
            name = item.get("display_name", place)
            lines_out.append(f"{i}. {name}")
        lines_out.append("")
        lines_out.append(f"🔗 Google Maps: {gmaps_url}")
        
        return "\n".join(lines_out)
        
    except requests.Timeout:
        return "Map search timed out. Please try again."
    except Exception as error:
        return "Map error: " + str(error)[:80]


def detect_tool(text):
    text = (text or "").strip()
    if not text:
        return None, None

    first_word = text.split()[0]
    command = first_word.split("@")[0].lower()
    arguments = text[len(first_word):].strip()

    if command == "/weather":
        if not arguments:
            return "weather", "❓ Please specify a city.\nUsage: /weather <city>\nExample: /weather London"
        return "weather", tool_weather(arguments)

    if command == "/tr":
        if not arguments:
            return None, None
        # Support /tr <lang> <text> OR /tr <text>
        LANG_CODES = {"en","my","ja","zh","ko","fr","de","es","it","pt","ru","ar","hi","th","vi","id","ms"}
        _parts = arguments.split(maxsplit=1)
        if len(_parts) == 2 and _parts[0].lower() in LANG_CODES:
            _target = _parts[0].lower()
            _src = _parts[1]
        else:
            _target = "en"
            _src = arguments
        return "translate", tool_translate(_src, _target)

    if command == "/fx":
        parts = arguments.split()
        if len(parts) < 2:
            return None, None
        amount = parts[2] if len(parts) >= 3 else 1
        return "currency", tool_currency(parts[0], parts[1], amount)

    if command == "/wiki":
        if not arguments:
            return None, None
        return "wiki", tool_wikipedia(arguments)

    if command == "/map":
        if not arguments:
            return None, None
        return "map", tool_maps(arguments)

    return None, None
