import streamlit as st
import jwt, datetime, json, os, re
from hashlib import sha256
from collections import defaultdict, Counter
import pandas as pd
import plotly.express as px # Import Plotly for Pie Chart

# --- CONFIGURATION ---
SECRET_KEY = "mysecretkey"
DB_FILE = "users.json"
KB_FILE = "kb.json" # KB is now external
LOG_FILE = "chat_logs.json" # For feedback and analytics
ADMIN_EMAIL = "admin@app.com" # Designate your admin email

# Use wide layout for dashboard
st.set_page_config(page_title="Health Wellness Chatbot", layout="wide")

# --- NEW THEME: Red / Dark Blue / Light Blue / White ---
st.markdown("""
<style>
/* Base UI Styling */
body { background: ##f3f8fe; } /* Dark Blue */
.stApp { background-color: ##f3f8fe; color: ##000000; } /* White Text */

/* Headings and Labels */
h1, h2, h3, h4, h5, h6, label,
.stSidebar h1, .stSidebar h2, .stSidebar h3 {
    color: #80BFFF !important; /* Light Blue Accent */
}
h1 { color: ##000000 !important; text-align: center; } /* Main Title White */
h2, h3 { /* Subheaders */
     border-bottom: 2px solid #003366; /* Mid Blue */
     padding-bottom: 5px;
     color: ##000000 !important; /* White */
     margin-top: 1.5rem; /* Add space above subheaders */
}

/* Sidebar */
.stSidebar { background-color: #001024 !important; border-right: 1px solid #003366; } /* Even Darker Blue */
.stSidebar .stButton>button {
    background-color: #003366; /* Mid Blue */
    color: ##000000; /* White Text */
    border: 1px solid #80BFFF; /* Light Blue Border */
    width: 100%; margin-bottom: 5px; border-radius: 4px;
}
.stSidebar .stButton>button:hover {
    background-color: #80BFFF; /* Light Blue */
    color: #001A3A; /* Dark Blue Text */
    border-color: ##000000;
}

/* Input Boxes (Forms, Chat Input) */
.stTextInput>div>div>input,
div[data-testid="stForm"] input[type="text"],
div[data-testid="stForm"] input[type="password"],
div[data-testid="stForm"] textarea {
    background-color: #003366; /* Mid Blue */
    color: #FFFFFF; /* White Text */
    border: 1px solid #80BFFF; /* Light Blue Border */
    border-radius: 4px; padding: 10px;
}
div[data-testid="stForm"] div[data-testid="stTextInput"] > div:nth-child(2) > div:nth-child(1) > input { height: 48px; } /* Chat Input */
.stTextInput>div>div>input:focus, /* Focus effect */
div[data-testid="stForm"] input[type="text"]:focus,
div[data-testid="stForm"] input[type="password"]:focus,
div[data-testid="stForm"] textarea:focus { border-color: #FFFFFF; box-shadow: 0 0 0 1px #FFFFFF; }

/* General Buttons (Main Area) */
.stButton>button {
    background-color: #003366; color: #FFFFFF; font-weight: bold; border-radius: 4px;
    border: 1px solid #80BFFF; padding: 8px 18px; height: 38px; line-height: 20px;
}
.stButton>button:hover { background-color: #80BFFF; color: #001A3A; border-color: #FFFFFF; }

/* Primary Button (Admin Save, Profile Save) */
.stButton>button[kind="primary"], div[data-testid="stForm"] button.st-emotion-cache-19rxjzo {
     background-color: #80BFFF !important; color: #001A3A !important; border: 1px solid #80BFFF !important;
}
.stButton>button[kind="primary"]:hover, div[data-testid="stForm"] button.st-emotion-cache-19rxjzo:hover {
      background-color: #AAD4FF !important; border-color: #FFFFFF !important; color: #001A3A !important;
}
/* Danger Button (Admin Delete) */
button.st-emotion-cache-1uj9mc { background-color: #DC3545 !important; color: #FFFFFF !important; border: none !important; }
button.st-emotion-cache-1uj9mc:hover { background-color: #F87979 !important; }

/* Chat Bubbles */
.chat-bubble { padding: 10px 15px; margin: 8px 0; border-radius: 15px; max-width: 80%; word-wrap: break-word; font-size: 16px; line-height: 1.5; }
.bot-msg { background-color: #003366; color: #FFFFFF; border-top-left-radius: 0; float: left; clear: both; }
.user-msg { background-color: #80BFFF; color: #001A3A; border-top-right-radius: 0; float: right; clear: both; }

/* Chat Send Button */
div[data-testid="stForm"] button.st-emotion-cache-uss2im { /* More specific selector for send */
    background-color: #003366 !important; color: #FFFFFF !important; height: 48px !important; width: 100% !important;
    border-radius: 4px !important; border: 1px solid #80BFFF !important; font-size: 20px !important; padding: 0 !important; margin-top: -1px;
}
div[data-testid="stForm"] button.st-emotion-cache-uss2im:hover { background-color: #80BFFF !important; border-color: #FFFFFF !important; color: #001A3A !important; }

/* Alignment & Spacing */
div[data-testid="stExpander"] div[role="button"] { padding-left: 0; } /* Align expander header */
.stTabs [data-baseweb="tab-list"] { background-color: #001A3A; } /* Dark blue tab header */
.stTabs [data-baseweb="tab"] { background-color: #003366; color: ##000000; border-radius: 4px 4px 0 0; }
.stTabs [data-baseweb="tab--selected"] { background-color: #001A3A; color: #80BFFF; }
hr { border-top: 1px solid #003366; margin: 1rem 0; } /* Divider color */
div[data-testid="stVerticalBlock"] > div { margin-bottom: 1rem; } /* Consistent vertical spacing */

/* BOT ONLINE/OFFLINE STATUS */
.status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
.status-online { background-color: #80BFFF !important; } /* Light Blue online */
.status-offline { background-color: #DC3545 !important; } /* Red offline */
.bot-header { font-size: 1.5rem; font-weight: 600; color: ##000000 !important; display: flex; align-items: center; margin-bottom: 1rem; }

/* Keyword Buttons - ensure they fill columns */
div[data-testid="stHorizontalBlock"] .stButton>button {
    background-color: #003366; color: ##000000; border: 1px solid #80BFFF; height: 40px; font-weight: normal; width: 100%;
}
div[data-testid="stHorizontalBlock"] .stButton>button:hover { background-color: #80BFFF; color: #001A3A; border: 1px solid #000000; }

/* Feedback Buttons */
div.feedback-button-container { margin-top: -10px; margin-left: 10px; margin-bottom: 10px; float: left; clear: both; }
div.feedback-button-container .stButton>button {
    background-color: transparent; border: none; height: 30px; width: 30px; font-weight: bold; padding: 0; font-size: 1.3em;
}
/* Green Thumb */
div.feedback-button-container .stButton:nth-child(1)>button { color: #28a745 !important; }
div.feedback-button-container .stButton:nth-child(1)>button:hover { color: #34D399 !important; } /* Lighter green */
/* Red Thumb */
div.feedback-button-container .stButton:nth-child(2)>button { color: #DC3545 !important; }
div.feedback-button-container .stButton:nth-child(2)>button:hover { color: #F87979 !important; } /* Lighter red */

span.feedback-received { color: #AAAAAA; font-size: 0.8em; float: left; clear: both; margin-left: 10px; margin-top: 5px; }

/* Admin Dashboard Specific Styles */
div[data-testid="stMetric"] { background-color: #003366; border-radius: 8px; padding: 1rem; border: 1px solid #80BFFF; }
div[data-testid="stMetric"] label { color: #AAAAAA !important; }
div[data-testid="stMetric"] div.st-emotion-cache-1gfitym { color: ##000000 !important; }
div[data-testid="stMetric"] div.st-emotion-cache-1gfitym > div { color: #000000 !important; }
div.admin-list-container { background-color: #003366; padding: 1rem; border-radius: 8px; border: 1px solid #80BFFF; max-height: 250px; overflow-y: auto; }
div.admin-list-container h3 { margin-top: 0; margin-bottom: 0.5rem; color: #000000 !important; }
div.admin-list-container ul { list-style: none; padding: 0; margin: 0; }
div.admin-list-container li { padding: 0.3rem 0; border-bottom: 1px solid #001A3A; display: flex; justify-content: space-between; align-items: center; color: #FFFFFF; }
div.admin-list-container li:last-child { border-bottom: none; }
div.admin-list-container span.feedback-icon-up { color: #28a745; font-weight: bold; } /* Green thumb */
div.admin-list_container span.feedback_icon_down { color: #DC3545; font_weight: bold; } /* Red thumb */
div.admin_list_container button { margin_top: 10px; }

/* Plotly Pie Chart Background */
.plotly-graph-div { background: transparent !important; }
/* Ensure JSON text is readable */
div[data-testid="stJson"] pre code { color: #000000 !important; } /* White Text */

</style>
""", unsafe_allow_html=True)


# --- PROFILE SCHEMA (Unchanged) ---
PROFILE_SCHEMA = { "name": {"type": "text", "label": "Full Name", "default": ""}, "age": {"type": "select", "label": "Age Group", "options": ["18–25", "25–35", "35–45", "45+"], "default": "18–25"}, "gender": {"type": "select", "label": "Gender", "options": ["Male", "Female", "Other"], "default": "Male"}, "language": {"type": "select", "label": "Preferred Language", "options": ["English", "Hindi"], "default": "English"}, }

# --- KNOWLEDGE BASE (External) ---
def load_kb():
    if not os.path.exists(KB_FILE): st.error(f"{KB_FILE} not found!"); return {}
    try:
        with open(KB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception as e: st.error(f"Error loading KB: {e}."); return {}
def save_kb(kb_data):
    global KB  # Correctly declare global at the start
    global ENTITY_MAP # Also declare ENTITY_MAP global here
    try:
        with open(KB_FILE, 'w', encoding='utf-8') as f: json.dump(kb_data, f, indent=4, ensure_ascii=False)
        # Update ENTITY_MAP after saving KB
        ENTITY_MAP = defaultdict(list)
        for c, d in KB.items():
            for s in d.get("symptoms", []): ENTITY_MAP["symptom"].append(s)
            for p in d.get("body_parts", []): ENTITY_MAP["body_part"].append(p)
        return True
    except Exception as e: st.error(f"Failed to save KB: {e}"); return False
KB = load_kb()
ENTITY_MAP = defaultdict(list)
if KB:
    for cond, data in KB.items():
        for sym in data.get("symptoms", []): ENTITY_MAP["symptom"].append(sym)
        for part in data.get("body_parts", []): ENTITY_MAP["body_part"].append(part)
else: st.warning("Knowledge Base empty/not loaded.")

# --- LOGGING & ANALYTICS ---
def load_logs():
    if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0: return []
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except json.JSONDecodeError: st.warning(f"Bad {LOG_FILE}. Starting empty."); return []
def save_logs(logs):
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f: json.dump(logs, f, indent=4, ensure_ascii=False)
    except Exception as e: st.error(f"Failed to save logs: {e}")
def log_chat(email, query, response, resp_id):
    logs = load_logs(); main_resp = response.split("<br><br>---<br>")[0]
    logs.append({"id": resp_id, "email": email, "query": query, "response": main_resp, "feedback": "none", "comment": "", "timestamp": datetime.datetime.utcnow().isoformat()})
    save_logs(logs)
def log_feedback(resp_id, fb_type, comment=""):
    logs = load_logs(); found = False
    for log in logs:
        if log.get("id") == resp_id: log["feedback"] = fb_type; log["comment"] = comment if comment else log["comment"]; found = True; break
    if found: save_logs(logs)
    else: st.error("Error logging feedback: Log ID not found.")
def get_frequent_keywords(email):
    logs = load_logs(); queries = [log['query'] for log in logs if log['email'] == email]
    defaults = ["🤒 Headache", "🤢 Flu", "🔥 Burns", "😴 Sleep", "🧘 Anxiety"]
    if not queries: return defaults
    words = [w for q in queries for w in re.findall(r'\b\w{4,}\b', q.lower())]
    stops = {"what", "when", "tell", "about", "have", "with", "from", "mein", "kya", "kaise", "this", "that"}
    filtered = [w for w in words if w not in stops]
    if not filtered: return defaults
    top_5 = [w for w, c in Counter(filtered).most_common(5)]
    emojis = {"headache": "🤒", "flu": "🤢", "burns": "🔥", "sleep": "😴", "anxiety": "🧘", "cough": "💨", "cold": "🤧", "fever": "🌡", "pain": "💥", "cut": "🩹"}
    formatted = [f"{emojis.get(w, '🔍')} {w.title()}" for w in top_5]
    if len(formatted) < 5:
        existing = {kw.split(" ", 1)[-1].lower() for kw in formatted}
        needed = 5 - len(formatted); added = 0
        for d_kw in defaults:
             if added >= needed: break
             if d_kw.split(" ", 1)[-1].lower() not in existing: formatted.append(d_kw); added += 1
    return formatted[:5]

# --- AUTH & USER HELPERS ---
def load_users():
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        print(f"User file {DB_FILE} not found. Creating admin."); admin_hash = hash_pw("admin123"); prof = {k: v["default"] for k, v in PROFILE_SCHEMA.items()}
        users = {ADMIN_EMAIL: {"password": admin_hash, "profile": prof}}; save_users(users); return users
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except json.JSONDecodeError: st.error("User DB error."); return {}
def save_users(users):
    try:
        with open(DB_FILE, 'w') as f: json.dump(users, f, indent=4)
    except Exception as e: st.error(f"Failed save users: {e}")
def hash_pw(pw): return sha256(pw.encode()).hexdigest()
def create_token(email): payload = {"email": email,"exp": datetime.datetime.utcnow()+datetime.timedelta(hours=8)}; return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
def get_user_from_token():
    token = st.session_state.get("token")
    if not token: return None
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": True}); return decoded["email"]
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        st.error(f"Session Error: {e}. Please log in."); keys = list(st.session_state.keys())
        [st.session_state.pop(k, None) for k in keys]; st.rerun(); return None

# --- NLU & RESPONSE LOGIC ---
def extract_entities(text, msg):
    text_lower = text.lower(); extracted = {"symptom": set(), "body_part": set()}
    global ENTITY_MAP;
    if not ENTITY_MAP: return extracted
    for etype, kwds in ENTITY_MAP.items():
        for kwd in kwds:
            kp = False
            if kwd.isascii():
                if re.search(r'\b' + re.escape(kwd) + r'\b', text_lower): kp = True
            elif kwd in msg: kp = True
            if kp: extracted[etype].add(kwd)
    if not extracted["body_part"]:
        for sym in extracted["symptom"]:
            if sym in ["fever", "dehydration", "insomnia", "bukhar", "paani ki kami", "anidra", "बुखार", "पानी की कमी", "अनिद्रा", "sleep", "नींद", "anxiety", "चिंता", "तनाव"]:
                extracted["body_part"].add("body"); break
    return extracted
def generate_disclaimer(name_en, name_hi, is_hindi):
    hr = "border-top: 1px dashed #80BFFF; margin: 10px 0;" # Light Blue dash
    note_hi = f"Note: यह *{name_hi}* जानकारी केवल बुनियादी मार्गदर्शन के लिए है।<br>यदि लक्षण बने रहते हैं या बिगड़ जाते हैं तो डॉक्टर से सलाह लें."
    note_en = f"Note: This *{name_en.title().replace('/', ' or ')}* information is for basic guidance only.<br>Consult a healthcare provider if symptoms persist or worsen."
    return f"<hr style='{hr}'>{note_hi}" if is_hindi else f"<hr style='{hr}'>{note_en}"
def get_bot_response(msg):
    global KB, ENTITY_MAP
    KB = load_kb();
    if not KB: return "🤖 Sorry, KB unavailable."
    ENTITY_MAP = defaultdict(list)
    for c, d in KB.items():
        for s in d.get("symptoms", []): ENTITY_MAP["symptom"].append(s)
        for p in d.get("body_parts", []): ENTITY_MAP["body_part"].append(p)

    msg_lower = msg.lower()
    HINDI_KW = ["namaste", "hindi", "sir dard", "bukhar", "khansi", "pet", "dard", "moch", "matli", "ulti", "jaln", "kamar", "peeth", "jukaam", "sardi", "gala", "khujli", "dast", "kabz", "pyas", "chot", "sujan", "daant", "tanaav", "chinta", "नमस्ते", "नमस्कार", "हिंदी", "सिरदर्द", "माथा दर्द", "सिर में दर्द", "सिर", "गर्दन", "माइग्रेन", "तेज सिरदर्द", "आंख", "बुखार", "तापमान", "ज्वर", "तेज़ बुखार", "शरीर", "खांसी", "सूखी खांसी", "गीली खांसी", "सर्दी", "जुकाम", "नाक बहना", "बंद नाक", "gala", "सीना", "नाक", "गले में दर्द", "खराश", "गला खराब", "एलर्जी", "छींक", "खुजली", "आंख में खुजली", "त्वचा", "मतली", "उल्टी", "पेट खराब", "जी मचलना", "पेट दर्द", "पेट", "दस्त", "पेट में मरोड़", "लूज मोशन", "कब्ज", "पेट साफ नहीं होना", "प्यास", "पानी की कमी", "सूखा मुंह", "चक्कर", "मुंह", "धूप से जलन", "जलना", "छाले", "लाल त्वचा", "चोट", "ज़ख्म", "खून बहना", "कटना", "उंगली", "हाथ", "पैर", "सिर पर चोट", "चक्कर आना", "दर्द", "मोच", "सूजन", "टखना", "घुटना", "कलाई", "जोड़", "मांसपेशी", "कमर दर्द", "पीठ में दर्द", "कमर", "पीठ", "नींद नहीं आना", "अनिद्रा", "थकान", "daant dard", "masoodon mein dard", "दांत दर्द", "मसूड़ों में दर्द", "दांत", "मसूड़ा", "चकत्ते", "लाल दाने", "कीड़े ने काटा", "मच्छर काटा", "डंक", "कान", "flu", "नींद", "चिंता", "तनाव"]
    is_hindi = any(h in msg_lower for h in HINDI_KW if h.isascii()) or any(h in msg for h in HINDI_KW if not h.isascii())
    greetings = {"नमस्ते", "नमस्कार", "hi", "hello", "hey", "namaste", "start"}; farewells = {"bye", "goodbye", "thanks", "thank you", "dhanyawad", "shukriya", "धन्यवाद", "शुक्रिया"}
    if msg_lower in greetings or any(g in msg for g in greetings if not g.isascii()): return "🤖 नमस्ते! मैं आपका कल्याण सहायक हूँ।" if is_hindi else "🤖 Hello! I’m your Wellness Assistant."
    if msg_lower in farewells or any(f in msg for f in farewells if not f.isascii()): return "🤖 आपका स्वागत है! सुरक्षित रहें!" if is_hindi else "🤖 You're welcome! Stay safe!"

    not_found = "🤖 क्षमा करें, मेरे पास इस बारे में जानकारी नहीं है..." if is_hindi else "🤖 Sorry, I don't have information on that..."
    res_key = "hindi_responses" if is_hindi else "responses"
    entities = extract_entities(msg_lower, msg); found = entities["symptom"].union(entities["body_part"])
    match, score = None, 0
    q_map = {"burns": "sunburn/burn", "sleep": "insomnia", "anxiety": "anxiety", "flu": "cough/cold"}; mapped_key = q_map.get(msg_lower)
    if mapped_key and mapped_key in KB: match, score = mapped_key, 100
    else:
        for c, d in KB.items():
            kwds = set(d.get("symptoms", []) + d.get("body_parts", [])); s = len(found.intersection(kwds))
            if s > score: score, match = s, c
            elif s == score and match:
                if c in ["migraine", "minor head injury"] and match in ["headache", "fever"]: match = c
                elif len(c) > len(match) and match not in ["migraine", "minor head injury"]: match = c
    if match and res_key in KB[match]:
        s_list = list(entities.get('symptoms', []))
        p_list = list(entities.get('body_parts', []))
        nlu_p = f"Part(s): *{', '.join(p for p in p_list if p != 'body')}" if p_list and p_list != ["body"] else "Part(s): *None"
        nlu_s = f"Symptom(s): *{', '.join(s_list)}" if s_list else "Symptom(s): *None"
        nlu = f"<br><br>---<br>🔍 Analysis:<br>{nlu_s}<br>{nlu_p}"
        r_list = KB[match].get(res_key, []); r_txt = r_list[0] if r_list else not_found
        disc = generate_disclaimer(KB[match]["condition_name_en"], KB[match]["condition_name_hi"], is_hindi)
        return r_txt + nlu + disc
    return r_txt + nlu + disc if match else not_found # Return NLU even if no match found

# --- VALIDATION ---
def validate_email(e): return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", e)
def validate_password(p): return len(p) >= 6

# ==================================================================
# --- UPDATED ADMIN DASHBOARD FUNCTION (Multi-column, Pie Chart, Colors, Management Features) ---
# ==================================================================
def show_admin_dashboard():
    st.header("✨ Admin Dashboard")
    if st.button("⬅ Back to Chat"): st.session_state.show_admin = False; st.rerun()

    # Load data
    logs_data = load_logs()
    df = pd.DataFrame(logs_data) if logs_data else pd.DataFrame()
    if not df.empty and 'timestamp' in df.columns:
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df.dropna(subset=['timestamp'], inplace=True)
        except Exception: df = pd.DataFrame()

    # --- Tabs for Dashboard and Management ---
    dashboard_tab, kb_manage_tab, user_manage_tab, feedback_tab = st.tabs(["📊 Dashboard", "📚 Manage KB", "👤 Manage Users", "💬 Feedback"])

    with dashboard_tab:
        # --- Row 1: Metrics & KB Overview ---
        st.subheader("📊 Usage Statistics")
        global KB
        t_queries = len(df); f_counts = df['feedback'].value_counts() if 'feedback' in df.columns else pd.Series()
        pos_fb = f_counts.get('up', 0); neg_fb = f_counts.get('down', 0); t_rated = pos_fb + neg_fb
        fb_score = (pos_fb / t_rated * 100) if t_rated > 0 else 0
        all_users = load_users()
        t_users = len(all_users) - (1 if ADMIN_EMAIL in all_users else 0) # Exclude admin from user count
        t_kb = len(KB)
        m_col1, m_col2, m_col3, m_col4 = st.columns(4) # Added more columns for metrics
        with m_col1: st.metric("Total Users", t_users)
        with m_col2: st.metric("Health Topics (KB)", t_kb)
        with m_col3: st.metric("Queries Handled", t_queries)
        with m_col4: st.metric("Positive Feedback", f"{fb_score:.1f}%", f"{t_rated} rated")

        # --- Row 2: Trends & Recent Feedback ---
        col3, col4 = st.columns([2, 1])
        with col3:
            st.subheader("📈 Query Trends");
            if df.empty or 'timestamp' not in df.columns or df['timestamp'].isnull().all(): st.caption("No trend data.")
            else:
                try:
                     # Group by day and count queries
                     trends = df.set_index('timestamp').resample('D')['query'].count()
                     if not trends.empty: st.line_chart(trends, color="#80BFFF") # Light Blue line
                     else: st.caption("No queries logged.")
                except Exception as e: st.caption(f"Chart error: {e}")
        with col4:
            st.subheader("💬 Recent Feedback"); st.markdown('<div class="admin-list-container">', unsafe_allow_html=True)
            if df.empty or 'feedback' not in df.columns: st.caption("No feedback.")
            else:
                fb_df = df[df['feedback'] != 'none'].sort_values('timestamp', ascending=False).head(5)
                if fb_df.empty: st.caption("No rated feedback.")
                else:
                    st.markdown("<ul>", unsafe_allow_html=True)
                    for i, r in fb_df.iterrows():
                        # Use actual thumbs with color styling
                        icon = "👍" if r['feedback'] == 'up' else "👎";
                        cls = "up" if r['feedback'] == 'up' else "down"
                        q = (r['query'][:30] + '...') if len(r['query']) > 30 else r['query']
                        st.markdown(f"<li><span>'{q}'</span> <span class='feedback-icon-{cls}'>{icon}</span></li>", unsafe_allow_html=True)
                    st.markdown("</ul>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- Row 3: Categories (Pie) & Deployment ---
        col5, col6 = st.columns([2, 1])
        with col5:
            st.subheader("🥧 Query Categories")
            if df.empty or 'query' not in df.columns: st.caption("No category data.")
            else:
                def cat_q(q):
                    q=str(q).lower()
                    if any(s in q for s in ["headache", "fever", "cough", "cold", "pain", "sore", "migraine", "flu", "sir dard", "bukhar", "khansi", "sardi", "jukaam", "gala kharab", "दर्द", "बुखार", "खांसी"]): return "Symptoms"
                    if any(s in q for s in ["cut", "burn", "sprain", "injury", "bite", "chot", "jalna", "moch", "चोट", "जलना", "मोच"]): return "First Aid"
                    if any(s in q for s in ["sleep", "anxiety", "stress", "diet", "hydrate", "constipation", "nausea", "vomiting", "diarrhea", "dehydration", "insomnia", "rashes", "नींद", "चिंता", "तनाव", "कब्ज", "मतली", "उल्टी", "दस्त", "निर्जलीकरण"]): return "Wellness"
                    return "Other"

                df['category'] = df['query'].apply(cat_q) if 'query' in df.columns else 'Other'; cat_counts = df['category'].value_counts()
                if not cat_counts.empty:
                     pie_df = cat_counts.reset_index(); pie_df.columns = ['category', 'count']
                     fig = px.pie(pie_df, names='category', values='count', hole=0.4,
                                  color_discrete_sequence=px.colors.qualitative.Pastel) # Example: Pastel colors
                     fig.update_layout(legend_title_text='Categories', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#FFFFFF", showlegend=False)
                     fig.update_traces(textinfo='percent+label', textfont_size=14, marker=dict(line=dict(color='#001A3A', width=2)))
                     st.plotly_chart(fig, use_container_width=True)
                else: st.caption("Could not categorize.")
        with col6:
            st.subheader("🚀 Deployment Status"); st.markdown('<div class="admin-list-container">', unsafe_allow_html=True)
            st.markdown("<ul><li><span style='color:#28a745;'>✅</span> Docker ready</li><li><span style='color:#28a745;'>✅</span> Cloud ready</li><li><span style='color:#FFA500;'>⏳</span> Docs pending</li></ul>", unsafe_allow_html=True) # Added icons
            st.markdown('</div>', unsafe_allow_html=True)

    # --- KB Management Tab ---
    with kb_manage_tab:
        st.subheader("✍ Knowledge Base Management")
        st.write("Edit the JSON below to update the health knowledge base.")
        kb_edit = load_kb()
        kb_json = json.dumps(kb_edit, indent=4, ensure_ascii=False)
        new_json = st.text_area("Edit KB JSON", value=kb_json, height=600, key="kb_edit_tab")

        col_k1, col_k2 = st.columns([1,5])
        with col_k1:
            if st.button("Save KB", type="primary", key="save_kb_tab", use_container_width=True):
                try:
                    new_kb = json.loads(new_json)
                    if save_kb(new_kb):
                        # global KB; # Removed as it's declared at the start of save_kb
                        # global ENTITY_MAP; # Removed as it's declared at the start of save_kb
                        KB = new_kb
                        ENTITY_MAP = defaultdict(list)
                        for c, d in KB.items():
                            for s in d.get("symptoms", []): ENTITY_MAP["symptom"].append(s)
                            for p in d.get("body_parts", []): ENTITY_MAP["body_part"].append(p)
                        st.success("KB updated!")
                        # st.session_state.admin_tab = "KB" # Stay on this tab after saving
                        st.rerun() # Rerun to refresh display
                    else: st.error("Failed to save KB.")
                except json.JSONDecodeError: st.error("Error: Invalid JSON format.")
                except Exception as e: st.error(f"Error saving KB: {e}")

    # --- User Management Tab ---
    with user_manage_tab:
        st.subheader("👤 User Management")
        st.write("View and manage registered users.")
        all_users_data = load_users()
        users_list = [{"Email": email, **user_data.get("profile", {})} for email, user_data in all_users_data.items() if email != ADMIN_EMAIL]
        users_df = pd.DataFrame(users_list) if users_list else pd.DataFrame()

        if users_df.empty:
            st.caption("No regular users registered.")
        else:
            st.dataframe(users_df, use_container_width=True)

            st.markdown("#### Delete User")
            user_to_delete = st.selectbox("Select User to Delete", options=[""] + list(users_df['Email'].tolist()))
            if st.button("Delete User", disabled=not user_to_delete): # Removed type="danger"
                 if user_to_delete and user_to_delete in all_users_data:
                     del all_users_data[user_to_delete]
                     save_users(all_users_data)
                     st.success(f"User '{user_to_delete}' deleted.")
                     st.rerun()
                 elif user_to_delete: st.error("User not found.")

    # --- Feedback Management Tab ---
    with feedback_tab:
        st.subheader("💬 All Feedback & Comments")
        st.write("Review user feedback and comments.")
        if df.empty or 'feedback' not in df.columns: st.warning("No logs.")
        else:
            # Filter for logs with actual feedback
            fb_all = df[df['feedback'] != 'none'][['timestamp', 'email', 'query', 'feedback', 'comment']].sort_values('timestamp', ascending=False)
            if fb_all.empty: st.caption("No rated feedback available.")
            else:
                # Add index column for display
                fb_all_display = fb_all.reset_index(drop=True)
                fb_all_display.index += 1 # Start index from 1

                st.dataframe(fb_all_display, use_container_width=True,
                             column_config={"timestamp": st.column_config.DatetimeColumn("Time", format="YY-MM-DD HH:mm"),
                                            "email":"User", "query":"Query", "feedback":"Rating", "comment":"Comment"})

# ==================================================================
# --- MAIN APP LOGIC ---
# ==================================================================
st.title("🪄 Health & Wellness Assistant")
users = load_users(); user_email = get_user_from_token()
keys_to_init = {"chat_archive": [], "show_admin": False, "feedback_submitted": {}, "admin_tab": None, "login_type": "user"} # Added login_type

for key, default_val in keys_to_init.items():
    if key not in st.session_state: st.session_state[key] = default_val

# --- LOGGED-IN VIEW ---
if user_email:
    # Set show_admin to True if logged in as admin and either it's the first load or admin dashboard button was clicked
    if user_email == ADMIN_EMAIL and "chat_history" not in st.session_state:
         st.session_state.show_admin = True
         # Don't rerun here, it will be handled below

    with st.sidebar: # Sidebar unchanged
        st.header("Controls & History")
        if user_email == ADMIN_EMAIL:
            st.markdown("---"); st.subheader("👑 Admin")
            if st.button("Admin Dashboard"): st.session_state.show_admin=True; st.session_state.admin_tab=None; st.rerun()
            st.markdown("---")
        is_online = st.toggle("Bot Status", value=True, key="bot_status")
        if st.button("➕ New Chat", key="new_chat"):
            if "chat_history" in st.session_state and len(st.session_state.chat_history)>1: st.session_state.chat_archive.insert(0, st.session_state.chat_history)
            st.session_state.pop("chat_history", None); st.session_state.pop("feedback_submitted", None); st.session_state.show_admin = False; st.rerun() # Ensure admin dashboard is hidden on new chat
        st.markdown("---"); st.subheader("Chat History")
        if st.session_state.chat_archive:
            for i, chat in enumerate(st.session_state.chat_archive[:10]):
                first = next((m for r, m in chat if r == 'user'), "Chat"); title = first[:50] + ("..." if len(first)>50 else "")
                if st.button(f"📜 {title}", key=f"chat_{i}"): st.session_state.chat_history=chat; st.session_state.feedback_submitted={}; st.session_state.show_admin=False; st.rerun()
        else: st.caption("No past chats.")
        st.markdown("---")
        if st.button(" Logout", key="logout"):
            keys = list(st.session_state.keys()); [st.session_state.pop(k, None) for k in keys]; st.success("Logged out."); st.rerun()

    # --- Main Area ---
    if st.session_state.get("show_admin", False) and user_email == ADMIN_EMAIL: show_admin_dashboard()
    else: # --- Standard Chat Interface ---
        if not st.session_state.get("show_admin", False): st.success(f"✅ Logged in as {user_email}")
        profile = users.get(user_email, {}).get("profile", {})

        # --- NEW: Tabbed Profile Section ---
        st.divider()
        with st.expander("👤 User Profile & Settings", expanded=False):
             prof_tab1, prof_tab2 = st.tabs(["View Profile", "⚙ Settings"])
             with prof_tab1:
                  st.markdown("### 📌 Current Profile Data")
                  current_profile_display = users.get(user_email, {}).get("profile", {})
                  st.json({k:v for k,v in current_profile_display.items() if k in PROFILE_SCHEMA}) # Shows profile data
             with prof_tab2:
                 st.markdown("### ⚙ Update Settings")
                 with st.form("profile_form"):
                     new_profile = {} # Holds updated values
                     for key, config in PROFILE_SCHEMA.items():
                         current_value = profile.get(key, config["default"])
                         if config["type"] == "text": new_profile[key] = st.text_input(config["label"], current_value, key=f"profile_{key}")
                         elif config["type"] == "select":
                             options = config["options"]; index = options.index(current_value) if current_value in options else 0
                             new_profile[key] = st.selectbox(config["label"], options, index=index, key=f"profile_{key}")
                     save_prof = st.form_submit_button("💾 Save Settings", type="primary", use_container_width=True)
                     if save_prof:
                         if user_email in users: users[user_email]["profile"] = new_profile; save_users(users); st.success("Settings saved!"); st.rerun()
                         else: st.error("User not found.")
        st.divider()

        # --- CHATBOT INTERFACE ---
        status_class = "status-online" if is_online else "status-offline"; status_text = "Online" if is_online else "Offline"
        st.markdown(f'<div class="bot-header"><span class="status-indicator {status_class}"></span><span>Chatbot ({status_text})</span></div>', unsafe_allow_html=True)
        if "chat_history" not in st.session_state:
            lang = profile.get("language", "English"); init_greet = "🤖 नमस्ते!..." if lang == "Hindi" else "🤖 Hello! Ask me..."
            st.session_state.chat_history = [("bot", init_greet)]

        chat_display_cont = st.container(height=400) # Fixed height chat area
        with chat_display_cont:
            chat_hist = list(st.session_state.chat_history)
            for i, (role, text) in enumerate(chat_hist):
                resp_id = f"msg_{i}_{hash_pw(text)[:8]}"
                if role == "user": st.markdown(f'<div class="chat-bubble user-msg">{text}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-bubble bot-msg">{text}</div>', unsafe_allow_html=True)
                    if i > 0:
                        fb_state = st.session_state.feedback_submitted.get(resp_id)
                        if fb_state is None:
                            st.markdown('<div class="feedback-button-container">', unsafe_allow_html=True)
                            fb_c1, fb_c2, _ = st.columns([1, 1, 10])
                            with fb_c1: # Green Thumb UP
                                if st.button("👍", key=f"up_{resp_id}", help="Helpful"): log_feedback(resp_id, "up"); st.session_state.feedback_submitted[resp_id] = True; st.toast("Thanks! 👍"); st.rerun()
                            with fb_c2: # Red Thumb DOWN
                                if st.button("👎", key=f"down_{resp_id}", help="Not Helpful"): st.session_state.feedback_submitted[resp_id] = "pending"; st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                        elif fb_state == "pending": # Show comment form for DOWN vote
                             st.markdown('<div class="feedback-button-container">', unsafe_allow_html=True)
                             with st.form(key=f"comm_{resp_id}"):
                                comm = st.text_input("Reason (opt):", key=f"comm_{resp_id}")
                                if st.form_submit_button("Submit"): log_feedback(resp_id, "down", comm); st.session_state.feedback_submitted[resp_id] = True; st.toast("Thanks! 👎"); st.rerun()
                             st.markdown('</div>', unsafe_allow_html=True)
                        elif fb_state == True: st.markdown("<span class='feedback-received'>Feedback sent!</span>", unsafe_allow_html=True)
            st.markdown("<div id='end-of-chat'></div>", unsafe_allow_html=True)

        with st.form("chat_form", clear_on_submit=True): # Chat Input Form
            col1, col2 = st.columns([6, 1])
            with col1: user_in = st.text_input("Type...", key="chat_in", label_visibility="collapsed", placeholder="Ask symptoms...")
            with col2: send = st.form_submit_button("➤", help="Send")
            if send and user_in.strip():
                st.session_state.chat_history.append(("user", user_in))
                resp = "🤖 Offline..." if not is_online else get_bot_response(user_in)
                resp_id = f"msg_{len(st.session_state.chat_history)}_{hash_pw(resp)[:8]}"
                log_chat(user_email, user_in, resp, resp_id)
                st.session_state.chat_history.append(("bot", resp))
                st.rerun()
            elif send: st.warning("Please type.")

        st.divider()
        st.write("Or try:")
        dyn_kw = get_frequent_keywords(user_email)
        cols = st.columns(5) # Use exactly 5 columns for keyword buttons
        for i, kw in enumerate(dyn_kw):
            with cols[i]:
                if st.button(kw, use_container_width=True, key=f"kw_{i}"):
                    u_click = kw.split(" ", 1)[-1].strip()
                    st.session_state.chat_history.append(("user", u_click))
                    resp = "🤖 Offline..." if not is_online else get_bot_response(u_click)
                    resp_id = f"msg_{len(st.session_state.chat_history)}_{hash_pw(resp)[:8]}"
                    log_chat(user_email, u_click, resp, resp_id)
                    st.session_state.chat_history.append(("bot", resp))
                    st.rerun()

# --- LOGIN / REGISTER VIEW ---
else:
    st.subheader("Welcome")
    login_options = st.tabs(["User Login/Register", "Admin Login"])
    if st.session_state.login_type == "user":
        with login_options[0]:
            st.markdown("### User Account")
            with st.form("user_login_reg_form"):
                em = st.text_input("Email", key="user_em_in")
                pw = st.text_input("Password", type="password", key="user_pw_in")
                c1, c2 = st.columns(2)
                with c1: reg = st.form_submit_button("Register")
                with c2: log = st.form_submit_button("Login")
                if reg:
                    if not validate_email(em): st.error("Invalid Email")
                    elif not validate_password(pw): st.error("Pwd >= 6 chars")
                    elif em in users: st.error("User exists")
                    else: users[em]={"password":hash_pw(pw),"profile":{k:v["default"] for k,v in PROFILE_SCHEMA.items()}}; save_users(users); st.success("Registered! Please Login."); st.session_state.login_type="user"; st.rerun()
                if log:
                    if not validate_email(em) or not pw: st.error("Email/Pwd required")
                    elif em in users and users[em]["password"] == hash_pw(pw): st.session_state["token"] = create_token(em); st.success("Login ok!"); st.session_state.login_type="user"; st.rerun()
                    else: st.error("Invalid credentials.")
        with login_options[1]:
            st.markdown("### Admin Account")
            st.caption(f"Use email: `{ADMIN_EMAIL}`")
            if st.button("Switch to Admin Login", key="switch_to_admin"): st.session_state.login_type = "admin"; st.rerun()

    elif st.session_state.login_type == "admin":
         with login_options[1]:
            st.markdown("### Admin Account")
            with st.form("admin_login_form"):
                em = st.text_input("Admin Email", value=ADMIN_EMAIL, key="admin_em_in", disabled=True)
                pw = st.text_input("Admin Password", type="password", key="admin_pw_in")
                c1, c2 = st.columns(2)
                with c1: admin_log = st.form_submit_button("Admin Login")
                with c2: switch_to_user = st.form_submit_button("Switch to User Login")
                if admin_log:
                    if not validate_email(em) or not pw: st.error("Email/Pwd required")
                    elif em == ADMIN_EMAIL and em in users and users[em]["password"] == hash_pw(pw):
                        st.session_state["token"] = create_token(em)
                        st.session_state.show_admin = True  # Set show_admin to True for admin login
                        st.success("Admin Login ok!")
                        st.session_state.login_type="admin"
                        st.rerun()
                    else: st.error("Invalid admin credentials.")
                if switch_to_user:
                    st.session_state.login_type = "user"
                    st.session_state.show_admin = False # Ensure admin dashboard is hidden on switch
                    st.rerun()
         with login_options[0]:
             st.markdown("### User Account")
             if st.button("Switch to User Login", key="switch_to_user_2"): st.session_state.login_type = "user"; st.rerun()
