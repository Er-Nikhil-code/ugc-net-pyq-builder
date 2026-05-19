"""
UGC NET Paper 1 — PYQ JSON Builder v3.0 (GitHub Storage)
- All JSON and images saved to GitHub repository (data/ folder)
- Counter stored in data/counter.json
- Session history loaded from GitHub at startup
- Works on Streamlit Cloud (no local file writes)
"""

import streamlit as st
import json
import base64
import requests
from datetime import datetime, timezone

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UGC NET PYQ Builder",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── GitHub API Configuration (from secrets) ───────────────────────────────────
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_OWNER = "Er-Nikhil-code"          # Your GitHub username
REPO_NAME = "ugc-net-pyq-builder"      # Your repository name
DATA_DIR = "data"                      # Folder where all data will be stored

# ── Helper: Upload file to GitHub (from bytes) ───────────────────────────────
def upload_to_github(file_bytes, repo_path, commit_message):
    """Upload a file (bytes) to GitHub repository."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{repo_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    # Get current SHA if file exists (for update)
    sha = None
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        sha = resp.json()["sha"]
    
    content_b64 = base64.b64encode(file_bytes).decode("utf-8")
    payload = {
        "message": commit_message,
        "content": content_b64,
        "branch": "main",
    }
    if sha:
        payload["sha"] = sha
    
    response = requests.put(url, headers=headers, json=payload)
    return response.status_code in [200, 201]

# ── Helper: Read file from GitHub (returns decoded text or None) ─────────────
def read_from_github(repo_path):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{repo_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        content_b64 = resp.json()["content"]
        return base64.b64decode(content_b64).decode("utf-8")
    return None

# ── Helper: List files in a GitHub folder ────────────────────────────────────
def list_files_in_github_folder(folder_path):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{folder_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()  # list of file objects
    return []

# ── Counter management using GitHub (stored in data/counter.json) ────────────
def _read_ctr():
    try:
        content = read_from_github(f"{DATA_DIR}/counter.json")
        if content:
            return int(json.loads(content).get("counter", 0))
    except Exception:
        pass
    return 0

def _write_ctr(n):
    data = json.dumps({"counter": n}, indent=2)
    upload_to_github(data.encode("utf-8"), f"{DATA_DIR}/counter.json", "Update counter")
    return n

def peek_next():
    return _read_ctr() + 1

def incr_ctr():
    n = _read_ctr() + 1
    _write_ctr(n)
    return n

def make_qid(year, session, shift, ctr=None):
    sc = "M" if "M" in shift else ("E" if "E" in shift else "NA")
    base = f"UGCNET_P1_{year}_{session}_{sc}"
    return f"{base}_{int(ctr):04d}" if ctr else base

# ── Load session history from GitHub (all JSON files in data/ except counter) ─
def load_history_from_github():
    history = []
    files = list_files_in_github_folder(DATA_DIR)
    for file in files:
        if file["name"].endswith(".json") and file["name"] != "counter.json":
            resp = requests.get(file["download_url"])
            if resp.status_code == 200:
                data = resp.json()
                history.append({
                    "id": data["question_id"],
                    "type": data["classification"]["question_type"],
                    "difficulty": data["classification"]["difficulty"],
                    "json": data,
                })
    history.sort(key=lambda x: x["id"])
    return history

# ── CSS (unchanged from your design) ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

*, html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}
#MainMenu, footer, header { visibility: hidden; }

.block-container {
    padding: 2.5rem 2rem 5rem !important;
    max-width: 860px !important;
}

/* Page header */
.page-header {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 28px;
    padding-bottom: 18px;
    border-bottom: 2px solid #f0f0f0;
}
.page-title { font-size: 18px; font-weight: 600; color: #1a1a1a; letter-spacing: -0.3px; }
.page-sub   { font-size: 12px; color: #b0b0b0; font-weight: 400; letter-spacing: 0.5px; text-transform: uppercase; }

/* Section labels */
.field-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.7px;
    text-transform: uppercase;
    color: #888;
    margin-bottom: 6px;
    margin-top: 0;
}

/* QID badge */
.qid-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: #6b7280;
    background: #f5f5f5;
    border: 1px solid #e8e8e8;
    border-radius: 6px;
    padding: 5px 12px;
    margin-top: 2px;
    margin-bottom: 4px;
}

/* Dividers */
.section-divider       { border: none; border-top: 1px solid #efefef; margin: 20px 0 16px 0; }
.section-divider-heavy { border: none; border-top: 2px solid #f0f0f0; margin: 24px 0 20px 0; }

/* Option badge (A B C D inline) */
.opt-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 7px;
    font-size: 12px;
    font-weight: 600;
    color: #374151;
    flex-shrink: 0;
}

/* Streamlit widget overrides */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    border-radius: 8px !important;
    border-color: #e5e7eb !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: #9ca3af !important;
    box-shadow: 0 0 0 3px rgba(156,163,175,0.15) !important;
}
div[data-testid="stSelectbox"] > div > div {
    border-radius: 8px !important;
    border-color: #e5e7eb !important;
    font-size: 13px !important;
}
div[data-testid="stButton"] > button {
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
}
div[data-testid="stCheckbox"] label {
    font-size: 12px !important;
    color: #6b7280 !important;
    font-weight: 400 !important;
}
div[data-testid="stRadio"] label { font-size: 13px !important; }

/* Preview empty state */
.preview-empty {
    background: #fafafa;
    border: 1.5px dashed #e5e7eb;
    border-radius: 12px;
    padding: 40px 16px;
    text-align: center;
    color: #c0c0c0;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
UNITS    = ["Teaching Aptitude","Research Aptitude","Comprehension","Communication",
            "Mathematical Reasoning and Aptitude","Logical Reasoning","Data Interpretation",
            "ICT","People and Environment","Higher Education System"]
QTYPES   = ["MCQ","Assertion-Reason","Match the Following","Passage-Based",
            "Numerical","Sequence Arrangement","True/False","Fill in the Blank"]
SESSIONS = ["June","December","July","October"]
SHIFTS   = ["Morning (M)","Evening (E)","NA"]
AR_OPTS  = [
    {"id":"A","text":"Both Assertion (A) and Reason (R) are true and Reason (R) is the correct explanation of Assertion (A)."},
    {"id":"B","text":"Both Assertion (A) and Reason (R) are true but Reason (R) is NOT the correct explanation of Assertion (A)."},
    {"id":"C","text":"Assertion (A) is true but Reason (R) is false."},
    {"id":"D","text":"Assertion (A) is false but Reason (R) is true."},
]

# ── Callbacks (on_click → no scroll-to-top) ──────────────────────────────────
def _reindex_options():
    opts = st.session_state.options
    for i, o in enumerate(opts):
        o["id"] = chr(65+i) if i < 26 else str(i+1)
    ids = [o["id"] for o in opts]
    if st.session_state.current_correct not in ids:
        st.session_state.current_correct = ids[0] if ids else "A"

def cb_add_option():
    idx = len(st.session_state.options)
    st.session_state.options.append({
        "id": chr(65+idx) if idx < 26 else str(idx+1),
        "text":"","eq":"","eq_on":False,"img_on":False,"img":None
    })

def cb_remove_option(idx):
    if len(st.session_state.options) > 2:
        st.session_state.options.pop(idx)
        _reindex_options()

def cb_add_match_row():
    if st.session_state.match_rows < 8: st.session_state.match_rows += 1

def cb_remove_match_row():
    if st.session_state.match_rows > 2: st.session_state.match_rows -= 1

def cb_add_seq_item():
    if st.session_state.seq_items < 8: st.session_state.seq_items += 1

def cb_remove_seq_item():
    if st.session_state.seq_items > 2: st.session_state.seq_items -= 1

def cb_clear_history():
    st.session_state.history = []

# ── Session state init ────────────────────────────────────────────────────────
def _ss(k, v):
    if k not in st.session_state: st.session_state[k] = v

_ss("match_rows", 4)
_ss("seq_items",  4)
_ss("history",    load_history_from_github())   # Load from GitHub on start
_ss("options", [
    {"id":"A","text":"","eq":"","eq_on":False,"img_on":False,"img":None},
    {"id":"B","text":"","eq":"","eq_on":False,"img_on":False,"img":None},
    {"id":"C","text":"","eq":"","eq_on":False,"img_on":False,"img":None},
    {"id":"D","text":"","eq":"","eq_on":False,"img_on":False,"img":None},
])
_ss("prev_qtype",      None)
_ss("current_correct", "A")
_ss("_last_saved_id",  None)

def maybe_reset_options(qtype):
    if st.session_state.prev_qtype != qtype:
        st.session_state.options = [
            {"id":"A","text":"","eq":"","eq_on":False,"img_on":False,"img":None},
            {"id":"B","text":"","eq":"","eq_on":False,"img_on":False,"img":None},
            {"id":"C","text":"","eq":"","eq_on":False,"img_on":False,"img":None},
            {"id":"D","text":"","eq":"","eq_on":False,"img_on":False,"img":None},
        ]
        st.session_state.match_rows     = 4
        st.session_state.seq_items      = 4
        st.session_state.prev_qtype     = qtype
        st.session_state.current_correct = "A"

# ─────────────────────────────────────────────────────────────────────────────
# PAGE HEADER
st.markdown("""
<div class="page-header">
  <span class="page-title">📚 UGC NET Paper 1</span>
  <span class="page-sub">PYQ JSON Builder</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — Exam Meta
st.markdown('<p class="field-label">Exam Details</p>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
year    = c1.selectbox("Year",    list(range(2005, 2026)), index=14, label_visibility="collapsed")
session = c2.selectbox("Session", SESSIONS, label_visibility="collapsed")
shift   = c3.selectbox("Shift",   SHIFTS,   label_visibility="collapsed")

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
st.markdown('<p class="field-label">Classification</p>', unsafe_allow_html=True)
r2c1, r2c2, r2c3, r2c4 = st.columns(4)
unit     = r2c1.selectbox("Unit",     UNITS,  label_visibility="collapsed")
topic    = r2c2.text_input("Topic",   placeholder="Topic",    label_visibility="collapsed")
subtopic = r2c3.text_input("Subtopic",placeholder="Subtopic", label_visibility="collapsed")
qtype    = r2c4.selectbox("Q Type",   QTYPES, label_visibility="collapsed")

maybe_reset_options(qtype)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
difficulty = st.radio("Difficulty", ["Easy","Medium","Hard"], horizontal=True, index=1, label_visibility="collapsed")
st.markdown(
    f'<div class="qid-badge">🔑 {make_qid(year, session, shift, peek_next())}</div>',
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
def render_q_toggles(eq_key, img_key):
    """Equation + Image toggles for question. Returns (eq_on, eq_val, img_on, img_file_bytes)."""
    tq1, tq2 = st.columns([1, 5])
    eq_on  = tq1.checkbox("＋ Equation", key=f"q_eq_toggle_{eq_key}")
    img_on = tq2.checkbox("＋ Image",    key=f"q_img_toggle_{img_key}")
    eq_val = ""; img_bytes = None
    if eq_on:
        eq_val = st.text_input("LaTeX equation", placeholder=r"\frac{a+b}{c}", key=f"q_eq_val_{eq_key}")
        if eq_val.strip(): st.latex(eq_val)
    if img_on:
        uploaded = st.file_uploader("Question image", type=["png","jpg","jpeg"], key=f"q_img_{img_key}")
        if uploaded:
            img_bytes = uploaded.getvalue()
            st.image(uploaded, width=300)
    return eq_on, eq_val, img_on, img_bytes

def render_options_grid(opts, qtype_key):
    """Each option row: [badge A] [text input] [Eq ☐] [Img ☐] [✕]"""
    for idx, opt in enumerate(opts):
        col_badge, col_input, col_eq, col_img, col_rm = st.columns([0.5, 6, 1.2, 1.2, 0.7])

        col_badge.markdown(
            f"<div style='padding-top:7px'>"
            f"<span class='opt-badge'>{opt['id']}</span></div>",
            unsafe_allow_html=True,
        )
        opt["text"] = col_input.text_input(
            f"opt_{qtype_key}_{idx}",
            value=opt["text"],
            placeholder=f"Option {opt['id']}…",
            label_visibility="collapsed",
            key=f"opt_t_{qtype_key}_{idx}",
        )
        opt["eq_on"]  = col_eq.checkbox("Eq",  key=f"opt_eq_on_{qtype_key}_{idx}",  value=opt.get("eq_on",  False))
        opt["img_on"] = col_img.checkbox("Img", key=f"opt_img_on_{qtype_key}_{idx}", value=opt.get("img_on", False))

        if len(opts) > 2:
            col_rm.button("✕", key=f"opt_rm_{qtype_key}_{idx}",
                          on_click=cb_remove_option, args=(idx,))

        if opt["eq_on"]:
            opt["eq"] = st.text_input(
                f"LaTeX for {opt['id']}", placeholder="e.g. x^2",
                value=opt.get("eq",""), key=f"opt_eq_v_{qtype_key}_{idx}",
            )
            if opt["eq"].strip(): st.latex(opt["eq"])
        if opt["img_on"]:
            uploaded = st.file_uploader(
                f"Image for {opt['id']}", type=["png","jpg","jpeg"],
                key=f"opt_img_{qtype_key}_{idx}",
            )
            if uploaded:
                opt["img_bytes"] = uploaded.getvalue()
                st.image(uploaded, width=120)
            else:
                opt["img_bytes"] = None

        st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Question
st.markdown('<hr class="section-divider-heavy">', unsafe_allow_html=True)

question_text = ""
passage_text  = ""
q_eq_on = q_img_on = False
q_eq_val = ""; q_img_bytes = None
extra_data    = {}
options_final = []

if qtype == "MCQ":
    st.markdown('<p class="field-label">Question</p>', unsafe_allow_html=True)
    question_text = st.text_area("Question text", height=90, placeholder="Enter your question here…",
                                 label_visibility="collapsed", key="q_text_mcq")
    q_eq_on, q_eq_val, q_img_on, q_img_bytes = render_q_toggles("mcq","mcq")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<p class="field-label">Options</p>', unsafe_allow_html=True)
    render_options_grid(st.session_state.options, "mcq")
    st.button("＋  Add Option", key="add_opt_mcq", on_click=cb_add_option, use_container_width=True)

    options_final = [
        {"id":o["id"],"text":o["text"],"equation":o.get("eq",""),"has_image":o.get("img_bytes") is not None}
        for o in st.session_state.options
    ]

elif qtype == "Assertion-Reason":
    st.info("ℹ️ Standard A–D options are auto-generated for Assertion-Reason questions.")
    st.markdown('<p class="field-label">Assertion (A)</p>', unsafe_allow_html=True)
    ar_a = st.text_area("Assertion (A)", height=80, placeholder="Write the assertion…", label_visibility="collapsed", key="ar_a")
    st.markdown('<p class="field-label">Reason (R)</p>', unsafe_allow_html=True)
    ar_r = st.text_area("Reason (R)",    height=80, placeholder="Write the reason…",    label_visibility="collapsed", key="ar_r")
    question_text = f"Assertion (A): {ar_a}\nReason (R): {ar_r}"
    q_eq_on, q_eq_val, q_img_on, q_img_bytes = render_q_toggles("ar","ar")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<p class="field-label">Options (standard)</p>', unsafe_allow_html=True)
    for opt in AR_OPTS:
        st.markdown(
            f"<div style='display:flex;align-items:flex-start;gap:10px;margin-bottom:8px'>"
            f"<span class='opt-badge'>{opt['id']}</span>"
            f"<span style='font-size:13px;color:#374151;padding-top:5px'>{opt['text']}</span></div>",
            unsafe_allow_html=True
        )
    options_final = AR_OPTS
    extra_data = {"assertion": ar_a, "reason": ar_r}

elif qtype == "Match the Following":
    st.markdown('<p class="field-label">Question Stem</p>', unsafe_allow_html=True)
    question_text = st.text_input(
        "Question stem", value="Match the items in Column A with Column B:",
        label_visibility="collapsed", key="q_match_stem"
    )
    q_eq_on, q_eq_val, q_img_on, q_img_bytes = render_q_toggles("match","match")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<p class="field-label">Match Table</p>', unsafe_allow_html=True)
    ar_col, rm_col, _ = st.columns([1,1,4])
    ar_col.button("➕ Add row",    key="match_add", on_click=cb_add_match_row)
    rm_col.button("➖ Remove row", key="match_rm",  on_click=cb_remove_match_row)

    hc1, hc2, hc3 = st.columns([5,0.5,5])
    hc1.markdown("<span style='font-size:11px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.5px'>Column A</span>", unsafe_allow_html=True)
    hc3.markdown("<span style='font-size:11px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.5px'>Column B</span>", unsafe_allow_html=True)
    match_left, match_right = [], []
    for i in range(st.session_state.match_rows):
        mc1, mc2, mc3 = st.columns([5,0.5,5])
        lv = mc1.text_input(f"ColA_{i}", placeholder=f"Item {chr(65+i)}", label_visibility="collapsed", key=f"ml_{i}")
        mc2.markdown("<div style='text-align:center;padding-top:6px;color:#ccc;font-size:16px'>→</div>", unsafe_allow_html=True)
        rv = mc3.text_input(f"ColB_{i}", placeholder=f"Item {i+1}",       label_visibility="collapsed", key=f"mr_{i}")
        match_left.append({"id":chr(65+i),"text":lv})
        match_right.append({"id":str(i+1),"text":rv})

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<p class="field-label">Options (matching combinations)</p>', unsafe_allow_html=True)
    for i, opt in enumerate(st.session_state.options):
        cb, ci, cr = st.columns([0.5,8,0.7])
        cb.markdown(
            f"<div style='padding-top:7px'><span class='opt-badge'>{opt['id']}</span></div>",
            unsafe_allow_html=True
        )
        opt["text"] = ci.text_input(
            f"mopt_{i}", value=opt["text"],
            placeholder="e.g. A–3, B–1, C–2, D–4",
            label_visibility="collapsed", key=f"mopt_t_{i}"
        )
        if len(st.session_state.options) > 2:
            cr.button("✕", key=f"mopt_rm_{i}", on_click=cb_remove_option, args=(i,))
    st.button("＋  Add Option", key="add_opt_match", on_click=cb_add_option, use_container_width=True)
    options_final = [{"id":o["id"],"text":o["text"]} for o in st.session_state.options]
    extra_data = {"column_a":match_left,"column_b":match_right}

elif qtype == "Passage-Based":
    st.markdown('<p class="field-label">Passage</p>', unsafe_allow_html=True)
    passage_text = st.text_area("Passage", height=150, placeholder="Paste the passage here…",
                                label_visibility="collapsed", key="pb_passage")
    st.markdown('<p class="field-label">Question</p>', unsafe_allow_html=True)
    question_text = st.text_area("Question", height=90, placeholder="Question based on the passage…",
                                 label_visibility="collapsed", key="pb_qtext")
    q_eq_on, q_eq_val, q_img_on, q_img_bytes = render_q_toggles("pb","pb")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<p class="field-label">Options</p>', unsafe_allow_html=True)
    render_options_grid(st.session_state.options, "pb")
    st.button("＋  Add Option", key="add_opt_pb", on_click=cb_add_option, use_container_width=True)
    options_final = [{"id":o["id"],"text":o["text"],"equation":o.get("eq","")} for o in st.session_state.options]
    extra_data = {"passage": passage_text}

elif qtype == "Numerical":
    st.markdown('<p class="field-label">Question</p>', unsafe_allow_html=True)
    question_text = st.text_area("Numerical question", height=110, placeholder="Enter the numerical question here…",
                                 label_visibility="collapsed", key="q_text_num")
    q_eq_on, q_eq_val, q_img_on, q_img_bytes = render_q_toggles("num","num")
    options_final = []

elif qtype == "Sequence Arrangement":
    st.markdown('<p class="field-label">Question Stem</p>', unsafe_allow_html=True)
    question_text = st.text_input("Question stem", value="Arrange the following in the correct sequence:",
                                  label_visibility="collapsed", key="q_seq_stem")
    q_eq_on, q_eq_val, q_img_on, q_img_bytes = render_q_toggles("seq","seq")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<p class="field-label">Sequence Items</p>', unsafe_allow_html=True)
    sa_col, sr_col, _ = st.columns([1,1,4])
    sa_col.button("➕ Add item",    key="seq_add", on_click=cb_add_seq_item)
    sr_col.button("➖ Remove item", key="seq_rm",  on_click=cb_remove_seq_item)
    seq_items = []
    for i in range(st.session_state.seq_items):
        sc1, sc2 = st.columns([0.5,8])
        sc1.markdown(
            f"<div style='padding-top:7px'><span class='opt-badge'>{chr(65+i)}</span></div>",
            unsafe_allow_html=True
        )
        val = sc2.text_input(f"seq_item_{i}", placeholder=f"Item {chr(65+i)}…",
                             label_visibility="collapsed", key=f"seq_{i}")
        seq_items.append({"id":chr(65+i),"text":val})

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<p class="field-label">Options (correct sequences)</p>', unsafe_allow_html=True)
    for i, opt in enumerate(st.session_state.options):
        cb, ci, cr = st.columns([0.5,8,0.7])
        cb.markdown(
            f"<div style='padding-top:7px'><span class='opt-badge'>{opt['id']}</span></div>",
            unsafe_allow_html=True
        )
        opt["text"] = ci.text_input(
            f"sopt_{i}", value=opt["text"],
            placeholder="e.g. A → C → B → D",
            label_visibility="collapsed", key=f"sopt_t_{i}"
        )
        if len(st.session_state.options) > 2:
            cr.button("✕", key=f"sopt_rm_{i}", on_click=cb_remove_option, args=(i,))
    st.button("＋  Add Option", key="add_opt_seq", on_click=cb_add_option, use_container_width=True)
    options_final = [{"id":o["id"],"text":o["text"]} for o in st.session_state.options]
    extra_data = {"items": seq_items}

elif qtype == "True/False":
    st.markdown('<p class="field-label">Question</p>', unsafe_allow_html=True)
    question_text = st.text_area("True/False statement", height=110, placeholder="Write the statement to evaluate…",
                                 label_visibility="collapsed", key="q_text_tf")
    q_eq_on, q_eq_val, q_img_on, q_img_bytes = render_q_toggles("tf","tf")
    options_final = [{"id":"A","text":"True"},{"id":"B","text":"False"}]

elif qtype == "Fill in the Blank":
    st.markdown('<p class="field-label">Question</p>', unsafe_allow_html=True)
    question_text = st.text_input("Fill in the blank", placeholder="The _____ method involves learning by doing.",
                                  label_visibility="collapsed", key="q_text_fib")
    q_eq_on, q_eq_val, q_img_on, q_img_bytes = render_q_toggles("fib","fib")
    options_final = []

else:
    st.markdown('<p class="field-label">Question</p>', unsafe_allow_html=True)
    question_text = st.text_area("Question", height=110, label_visibility="collapsed", key="q_text_fallback")
    options_final = []

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — Correct Answer + Explanation
st.markdown('<hr class="section-divider-heavy">', unsafe_allow_html=True)
exp_col1, exp_col2 = st.columns([1,3])

with exp_col1:
    st.markdown('<p class="field-label">Correct Answer</p>', unsafe_allow_html=True)
    if qtype in ("MCQ","Match the Following","Passage-Based","Sequence Arrangement"):
        opt_ids = [o["id"] for o in options_final] if options_final else ["A","B","C","D"]
        if st.session_state.current_correct not in opt_ids:
            st.session_state.current_correct = opt_ids[0] if opt_ids else "A"
        correct_answer = st.selectbox(
            "Correct answer", opt_ids, index=opt_ids.index(st.session_state.current_correct),
            label_visibility="collapsed", key="ca_main"
        )
        st.session_state.current_correct = correct_answer
    elif qtype == "Assertion-Reason":
        ar_ids = ["A","B","C","D"]
        idx_ar = ar_ids.index(st.session_state.current_correct) if st.session_state.current_correct in ar_ids else 0
        correct_answer = st.selectbox("Correct answer", ar_ids, index=idx_ar,
                                      label_visibility="collapsed", key="ca_ar_main")
        st.session_state.current_correct = correct_answer
    elif qtype == "True/False":
        tf_map  = {"True":"A","False":"B"}
        cur_tf  = [k for k,v in tf_map.items() if v == st.session_state.current_correct]
        tf_val  = cur_tf[0] if cur_tf else "True"
        tf_ans  = st.radio("Correct answer", ["True","False"], horizontal=True,
                           index=0 if tf_val=="True" else 1,
                           label_visibility="collapsed", key="ca_tf_main")
        correct_answer = "A" if tf_ans=="True" else "B"
        st.session_state.current_correct = correct_answer
    elif qtype in ("Numerical","Fill in the Blank"):
        correct_answer = st.text_input(
            "Correct answer", value=st.session_state.current_correct,
            placeholder="Answer…", label_visibility="collapsed", key="ca_text_main"
        )
        st.session_state.current_correct = correct_answer
    else:
        correct_answer = st.text_input(
            "Correct answer", value=st.session_state.current_correct,
            label_visibility="collapsed", key="ca_fallback_main"
        )
        st.session_state.current_correct = correct_answer

with exp_col2:
    st.markdown('<p class="field-label">Explanation</p>', unsafe_allow_html=True)
    explanation = st.text_area("Explanation", height=100, placeholder="Enter explanation here…",
                               label_visibility="collapsed", key="expl_text")
    te1, te2 = st.columns(2)
    expl_eq_on  = te1.checkbox("＋ Equation", key="expl_eq_toggle")
    expl_img_on = te2.checkbox("＋ Image",    key="expl_img_toggle")
    expl_eq_val = ""; expl_img_bytes = None
    if expl_eq_on:
        expl_eq_val = st.text_input("Explanation equation", placeholder=r"\sum_{i=1}^{n}i", key="expl_eq_val")
        if expl_eq_val.strip(): st.latex(expl_eq_val)
    if expl_img_on:
        uploaded = st.file_uploader("Explanation image", type=["png","jpg","jpeg"], key="expl_img_file")
        if uploaded:
            expl_img_bytes = uploaded.getvalue()
            st.image(uploaded, width=300)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — Metadata
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
mc1, mc2 = st.columns(2)
tags_raw     = mc1.text_input("Tags",     placeholder="teaching, aptitude", key="tags")
keywords_raw = mc2.text_input("Keywords", placeholder="lecture, deductive", key="keywords")
tags_list     = [t.strip() for t in tags_raw.split(",")     if t.strip()]
keywords_list = [k.strip() for k in keywords_raw.split(",") if k.strip()]

# ─────────────────────────────────────────────────────────────────────────────
# BUILD JSON PREVIEW (using timezone-aware datetime)
temp_qid        = make_qid(year, session, shift, peek_next())
q_block_preview = {"text": question_text}
if q_eq_on and q_eq_val.strip(): q_block_preview["equation"] = q_eq_val

if   qtype == "Assertion-Reason":    q_block_preview.update(extra_data); q_block_preview["options"]=options_final; q_block_preview["correct_answer"]=correct_answer
elif qtype == "Match the Following": q_block_preview.update(extra_data); q_block_preview["options"]=options_final; q_block_preview["correct_answer"]=correct_answer
elif qtype == "Passage-Based":       q_block_preview["passage"]=passage_text; q_block_preview["options"]=options_final; q_block_preview["correct_answer"]=correct_answer
elif qtype == "Numerical":           q_block_preview["correct_answer"]=correct_answer; q_block_preview["answer_type"]="numerical"
elif qtype == "Sequence Arrangement":q_block_preview.update(extra_data); q_block_preview["options"]=options_final; q_block_preview["correct_answer"]=correct_answer
elif qtype == "True/False":          q_block_preview["options"]=options_final; q_block_preview["correct_answer"]=correct_answer
elif qtype == "Fill in the Blank":   q_block_preview["correct_answer"]=correct_answer; q_block_preview["answer_type"]="text"
else:                                q_block_preview["options"]=options_final; q_block_preview["correct_answer"]=correct_answer

expl_block_preview = {"text": explanation}
if expl_eq_on and expl_eq_val.strip(): expl_block_preview["equation"] = expl_eq_val

now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

json_preview_data = {
    "question_id": temp_qid,
    "exam": {"year":int(year),"session":session,"shift":shift.split(" ")[0]},
    "classification": {"unit":unit,"topic":topic,"subtopic":subtopic,"question_type":qtype,"difficulty":difficulty},
    "question": q_block_preview,
    "solution": expl_block_preview,
    "concepts": {"tags":tags_list,"keywords":keywords_list},
    "retrieval": {"embedding_text":question_text},
    "meta": {"created_at":now_utc,"version":"3.0"},
}
json_preview_str = json.dumps(json_preview_data, indent=2, ensure_ascii=False)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — Question Preview
st.markdown('<hr class="section-divider-heavy">', unsafe_allow_html=True)
st.markdown('<p class="field-label">Question Preview</p>', unsafe_allow_html=True)

has_content = bool(question_text.strip() or passage_text.strip())
if not has_content:
    st.markdown(
        '<div class="preview-empty">👁 Preview will appear here once you start typing</div>',
        unsafe_allow_html=True
    )
else:
    if passage_text.strip():
        st.markdown(
            f'<div style="background:#f8faff;border-left:3px solid #6366f1;border-radius:8px;'
            f'padding:12px 16px;margin-bottom:14px;font-size:13.5px;color:#374151;">'
            f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.6px;color:#6366f1;margin-bottom:6px">📖 Passage</div>'
            f'{passage_text}</div>',
            unsafe_allow_html=True
        )
    if qtype == "Assertion-Reason":
        for part in question_text.split("\n"):
            st.markdown(f"<div style='font-size:14px;font-weight:500;color:#111;margin-bottom:5px'>{part}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='font-size:15px;font-weight:500;color:#111;margin-bottom:12px;line-height:1.6'>{question_text}</div>", unsafe_allow_html=True)

    if q_eq_on  and q_eq_val.strip():  st.latex(q_eq_val)
    if q_img_on and q_img_bytes:       st.image(q_img_bytes, width=300)

    if qtype == "Match the Following" and extra_data.get("column_a"):
        c1, c2 = st.columns(2)
        c1.markdown("<div style='font-size:11px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px'>Column A</div>", unsafe_allow_html=True)
        c2.markdown("<div style='font-size:11px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px'>Column B</div>", unsafe_allow_html=True)
        for la, lb in zip(extra_data["column_a"], extra_data["column_b"]):
            c1.markdown(f"<div style='font-size:13.5px;margin-bottom:4px'>({la['id']}) {la['text']}</div>", unsafe_allow_html=True)
            c2.markdown(f"<div style='font-size:13.5px;margin-bottom:4px'>({lb['id']}) {lb['text']}</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if options_final and qtype not in ("Numerical","Fill in the Blank"):
        for opt in options_final:
            is_correct = opt["id"] == correct_answer
            bg     = "#f0fdf4" if is_correct else "#fafafa"
            border = "#86efac" if is_correct else "#f0f0f0"
            color  = "#15803d" if is_correct else "#374151"
            bb     = "#16a34a" if is_correct else "#e5e7eb"
            bc     = "#fff"    if is_correct else "#6b7280"
            tick   = '<span style="margin-left:auto;font-size:11px;color:#16a34a;font-weight:600">✓</span>' if is_correct else ""
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:10px;padding:8px 12px;"
                f"background:{bg};border:1px solid {border};border-radius:8px;margin-bottom:6px;'>"
                f"<span style='display:inline-flex;align-items:center;justify-content:center;"
                f"width:24px;height:24px;background:{bb};border-radius:6px;"
                f"font-size:11px;font-weight:700;color:{bc};flex-shrink:0'>{opt['id']}</span>"
                f"<span style='font-size:13.5px;color:{color};font-weight:{'500' if is_correct else '400'}'>{opt['text']}</span>"
                f"{tick}</div>",
                unsafe_allow_html=True,
            )
            if opt.get("equation") and opt["equation"].strip(): st.latex(opt["equation"])
            # Show option image if present (from session state)
            mo = next((o for o in st.session_state.options if o["id"]==opt["id"]), None)
            if mo and mo.get("img_bytes"):
                st.image(mo["img_bytes"], width=150)

    if explanation.strip():
        st.markdown(
            f"<div style='margin-top:12px;padding:10px 14px;background:#fffbeb;"
            f"border:1px solid #fde68a;border-radius:8px;font-size:13px;color:#92400e;'>"
            f"<div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px'>💡 Explanation</div>"
            f"{explanation}</div>",
            unsafe_allow_html=True
        )
    if expl_eq_on  and expl_eq_val.strip(): st.latex(expl_eq_val)
    if expl_img_on and expl_img_bytes:       st.image(expl_img_bytes, width=300)

with st.expander("View JSON", expanded=False):
    st.code(json_preview_str, language="json")

# ─────────────────────────────────────────────────────────────────────────────
# SAVE BUTTON (upload to GitHub)
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

def do_save():
    # Increment counter and create final QID
    ctr = incr_ctr()
    saved_id = make_qid(year, session, shift, ctr)
    
    # Prepare image list for upload
    images_to_upload = []
    
    # Helper to add image to list if bytes exist
    def add_image(image_bytes, filename):
        if image_bytes:
            images_to_upload.append({"filename": filename, "bytes": image_bytes})
    
    # 1. Question image
    if q_img_on and q_img_bytes:
        add_image(q_img_bytes, f"{saved_id}_q.jpg")
    
    # 2. Option images
    if options_final and qtype not in ("Numerical","Fill in the Blank","Assertion-Reason"):
        for opt in st.session_state.options:
            if opt.get("img_bytes"):
                add_image(opt["img_bytes"], f"{saved_id}_opt_{opt['id']}.jpg")
    
    # 3. Explanation image
    if expl_img_on and expl_img_bytes:
        add_image(expl_img_bytes, f"{saved_id}_expl.jpg")
    
    # Build final JSON data
    final_q_block = {"text": question_text}
    if q_eq_on and q_eq_val.strip():
        final_q_block["equation"] = q_eq_val
    # Note: image paths in JSON will be relative to data/images/ folder
    if q_img_on and q_img_bytes:
        final_q_block["image"] = f"images/{saved_id}_q.jpg"
    
    if qtype == "Assertion-Reason":
        final_q_block.update(extra_data)
        final_q_block["options"] = options_final
        final_q_block["correct_answer"] = correct_answer
    elif qtype == "Match the Following":
        final_q_block.update(extra_data)
        final_q_block["options"] = options_final
        final_q_block["correct_answer"] = correct_answer
    elif qtype == "Passage-Based":
        final_q_block["passage"] = passage_text
        final_q_block["options"] = options_final
        final_q_block["correct_answer"] = correct_answer
    elif qtype == "Numerical":
        final_q_block["correct_answer"] = correct_answer
        final_q_block["answer_type"] = "numerical"
    elif qtype == "Sequence Arrangement":
        final_q_block.update(extra_data)
        final_q_block["options"] = options_final
        final_q_block["correct_answer"] = correct_answer
    elif qtype == "True/False":
        final_q_block["options"] = options_final
        final_q_block["correct_answer"] = correct_answer
    elif qtype == "Fill in the Blank":
        final_q_block["correct_answer"] = correct_answer
        final_q_block["answer_type"] = "text"
    else:
        final_q_block["options"] = options_final
        final_q_block["correct_answer"] = correct_answer
    
    # Add option image paths to options_final
    if options_final and qtype not in ("Numerical","Fill in the Blank","Assertion-Reason"):
        for opt in st.session_state.options:
            if opt.get("img_bytes"):
                for of in final_q_block.get("options", []):
                    if of["id"] == opt["id"]:
                        of["image"] = f"images/{saved_id}_opt_{opt['id']}.jpg"
                        break
    
    final_expl_block = {"text": explanation}
    if expl_eq_on and expl_eq_val.strip():
        final_expl_block["equation"] = expl_eq_val
    if expl_img_on and expl_img_bytes:
        final_expl_block["image"] = f"images/{saved_id}_expl.jpg"
    
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    final_data = {
        "question_id": saved_id,
        "exam": {"year": int(year), "session": session, "shift": shift.split(" ")[0]},
        "classification": {"unit": unit, "topic": topic, "subtopic": subtopic,
                           "question_type": qtype, "difficulty": difficulty},
        "question": final_q_block,
        "solution": final_expl_block,
        "concepts": {"tags": tags_list, "keywords": keywords_list},
        "retrieval": {"embedding_text": question_text},
        "meta": {"created_at": now_utc, "version": "3.0"},
    }
    
    # Upload JSON and images to GitHub
    json_bytes = json.dumps(final_data, indent=2, ensure_ascii=False).encode("utf-8")
    json_path = f"{DATA_DIR}/{saved_id}.json"
    success = upload_to_github(json_bytes, json_path, f"Add JSON for {saved_id}")
    if success:
        for img in images_to_upload:
            img_path = f"{DATA_DIR}/images/{img['filename']}"
            upload_to_github(img["bytes"], img_path, f"Add image for {saved_id}")
        st.session_state.history.append({
            "id": saved_id,
            "type": qtype,
            "difficulty": difficulty,
            "json": final_data,
        })
        st.success(f"✅ Saved — {saved_id}")
    else:
        st.error("❌ Failed to save to GitHub. Check token and repository settings.")
    
    st.rerun()

# Stash current values for callback (not really needed now, but kept for consistency)
_, save_col = st.columns([5,1])
with save_col:
    st.button("💾  Save", key="save_btn", on_click=do_save, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION HISTORY
if st.session_state.history:
    st.markdown('<hr class="section-divider-heavy">', unsafe_allow_html=True)
    hdr_col, clr_col = st.columns([4,1])
    hdr_col.markdown(
        f"<p class='field-label'>Session History "
        f"<span style='font-weight:400;color:#b0b0b0;text-transform:none;letter-spacing:0'>"
        f"({len(st.session_state.history)} saved)</span></p>",
        unsafe_allow_html=True,
    )
    clr_col.button("🗑 Clear", key="clear_hist", on_click=cb_clear_history)
    for idx, item in enumerate(reversed(st.session_state.history)):
        num = len(st.session_state.history) - idx
        with st.expander(f"#{num} · {item['id']}"):
            col1, col2 = st.columns(2)
            col1.markdown(f"**File:** `{item['id']}.json`")
            col2.markdown(f"**Type:** {item['type']}  ·  **Difficulty:** {item['difficulty']}")

st.markdown(
    "<div style='margin-top:40px;text-align:center;font-size:11px;color:#d1d5db;letter-spacing:0.5px'>"
    "UGC NET Paper 1 · PYQ JSON Builder developed by Nikhil</div>",
    unsafe_allow_html=True,
)
