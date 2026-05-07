"""
app.py  —  AgroSmart AI  |  Streamlit Frontend
It runs with:  streamlit run frontend/app.py
Set AGROSMART_API_BASE_URL to backend API origin.
"""

import streamlit as st
import time, math

from mock_data import PRESETS
from services.api_client import ApiClientError, chat, predict_crop

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title  = "AgroSmart AI",
    page_icon   = "🌾",
    layout      = "wide",
    initial_sidebar_state = "expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS  —  Dark earthy-green theme, premium feel
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* ── Root palette ── */
:root {
  --bg:          #0d1117;
  --surface:     #161c24;
  --surface2:    #1e2a1e;
  --green:       #4ade80;
  --green-dim:   #166534;
  --amber:       #fbbf24;
  --sky:         #38bdf8;
  --red:         #f87171;
  --text:        #e2e8f0;
  --text-muted:  #64748b;
  --border:      #2d3748;
  --radius:      14px;
}

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stHeader"] { background: transparent !important; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

/* ── Sidebar labels ── */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p {
  color: #94a3b8 !important;
  font-size: 0.78rem !important;
  letter-spacing: 0.08em !important;
  text-transform: uppercase !important;
  font-weight: 500 !important;
}

/* ── Sliders ── */
[data-testid="stSlider"] > div > div > div > div {
  background: var(--green) !important;
}
[data-testid="stSlider"] [data-testid="stTickBar"] { display: none; }

/* ── Select boxes ── */
[data-testid="stSelectbox"] > div > div {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  border-radius: 8px !important;
}

/* ── Primary button ── */
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #16a34a, #4ade80) !important;
  color: #0d1117 !important;
  font-family: 'Bebas Neue', sans-serif !important;
  font-size: 1.1rem !important;
  letter-spacing: 0.1em !important;
  border: none !important;
  border-radius: 10px !important;
  padding: 0.6rem 2rem !important;
  width: 100% !important;
  transition: transform 0.15s, box-shadow 0.15s !important;
}
.stButton > button[kind="primary"]:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 24px rgba(74,222,128,0.35) !important;
}

/* ── Secondary button ── */
.stButton > button:not([kind="primary"]) {
  background: var(--surface) !important;
  color: var(--green) !important;
  border: 1px solid var(--green-dim) !important;
  border-radius: 8px !important;
  font-family: 'DM Mono', monospace !important;
  font-size: 0.8rem !important;
}

/* ── Chat input ── */
[data-testid="stChatInput"] textarea {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  border-radius: 12px !important;
  font-family: 'DM Sans', sans-serif !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  margin-bottom: 0.5rem !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--green-dim); border-radius: 99px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPER COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────

def card(content_html: str, accent: str = "#4ade80", padding: str = "1.4rem"):
    st.markdown(f"""
    <div style="
        background:var(--surface);
        border:1px solid var(--border);
        border-top:3px solid {accent};
        border-radius:var(--radius);
        padding:{padding};
        margin-bottom:0.8rem;
    ">{content_html}</div>""", unsafe_allow_html=True)

def stat_block(label, value, unit="", color="#4ade80", icon=""):
    st.markdown(f"""
    <div style="
        background:var(--surface2);
        border:1px solid var(--border);
        border-radius:10px;
        padding:1rem 1.2rem;
        text-align:center;
        height:100%;
    ">
      <div style="font-size:1.6rem;margin-bottom:4px">{icon}</div>
      <div style="font-family:'Bebas Neue';font-size:2rem;color:{color};
                  line-height:1;letter-spacing:0.05em">{value}</div>
      <div style="font-size:0.65rem;color:#64748b;text-transform:uppercase;
                  letter-spacing:0.1em;margin-top:4px">{unit}</div>
      <div style="font-size:0.75rem;color:#94a3b8;margin-top:2px">{label}</div>
    </div>""", unsafe_allow_html=True)

def gis_gauge(score: float):
    score = max(0, min(100, score))
    color = "#4ade80" if score >= 70 else "#fbbf24" if score >= 40 else "#f87171"
    label = "EXCELLENT" if score >= 70 else "GOOD" if score >= 40 else "LOW"
    fill = score * 1.8

    st.markdown(f"""
    <div style="width:100%;display:flex;justify-content:center;margin-top:0.4rem">
      <div style="position:relative;width:240px;height:132px;overflow:hidden">
        <div style="
          width:240px;height:240px;border-radius:50%;
          background:conic-gradient(from 270deg, {color} 0deg {fill:.1f}deg,
                     #2d3748 {fill:.1f}deg 180deg, transparent 180deg 360deg);
          filter:drop-shadow(0 0 8px {color}60);
        "></div>
        <div style="
          position:absolute;left:18px;top:18px;width:204px;height:204px;
          border-radius:50%;background:var(--surface);
        "></div>
        <div style="
          position:absolute;left:0;right:0;top:62px;text-align:center;
          font-family:'Bebas Neue',sans-serif;font-size:2.4rem;color:{color};
          letter-spacing:0.04em;line-height:1;
        ">{score:.1f}</div>
        <div style="
          position:absolute;left:0;right:0;top:102px;text-align:center;
          font-size:0.68rem;color:#94a3b8;letter-spacing:0.12em;
          text-transform:uppercase;
        ">/ 100 · {label}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def confidence_bars(top_crops):
    bars_html = ""
    colors = ["#4ade80", "#38bdf8", "#fbbf24"]
    for i, crop in enumerate(top_crops):
        pct   = crop['confidence']
        color = colors[i]
        bars_html += f"""
        <div style="margin-bottom:10px">
          <div style="display:flex;justify-content:space-between;
                      font-size:0.78rem;margin-bottom:4px">
            <span style="color:#e2e8f0;text-transform:capitalize;
                         font-weight:{'600' if i==0 else '400'}">
              {'👑 ' if i==0 else ''}{crop['crop']}
            </span>
            <span style="color:{color};font-family:'DM Mono',monospace">{pct:.1f}%</span>
          </div>
          <div style="background:#2d3748;border-radius:99px;height:6px;overflow:hidden">
            <div style="width:{pct}%;height:100%;background:{color};border-radius:99px;
                        box-shadow:0 0 6px {color}80;
                        transition:width 0.8s ease"></div>
          </div>
        </div>"""
    return bars_html

def feature_importance_chart(fi: dict):
    labels = {"N":"Nitrogen","P":"Phosphorus","K":"Potassium",
              "temperature":"Temperature","humidity":"Humidity",
              "ph":"Soil pH","rainfall":"Rainfall"}
    sorted_fi = sorted(fi.items(), key=lambda x: x[1], reverse=True)
    max_val   = sorted_fi[0][1]
    bars_html = ""
    for key, val in sorted_fi:
        pct   = (val / max_val) * 100
        label = labels.get(key, key)
        bars_html += f"""
        <div style="margin-bottom:8px">
          <div style="display:flex;justify-content:space-between;font-size:0.75rem;
                      margin-bottom:3px">
            <span style="color:#94a3b8">{label}</span>
            <span style="color:#38bdf8;font-family:'DM Mono',monospace">{val:.3f}</span>
          </div>
          <div style="background:#1e2a1e;border-radius:99px;height:5px">
            <div style="width:{pct:.1f}%;height:100%;border-radius:99px;
                        background:linear-gradient(90deg,#16a34a,#38bdf8)"></div>
          </div>
        </div>"""
    return bars_html

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
if "result"   not in st.session_state: st.session_state.result   = None
if "messages" not in st.session_state: st.session_state.messages = []
if "analyzed" not in st.session_state: st.session_state.analyzed = False

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="
  display:flex; align-items:center; gap:16px;
  padding:1.2rem 0 0.6rem 0; border-bottom:1px solid #2d3748;
  margin-bottom:1.4rem;
">
  <div style="
    background:linear-gradient(135deg,#166534,#4ade80);
    border-radius:14px; width:52px; height:52px;
    display:flex; align-items:center; justify-content:center;
    font-size:1.6rem; flex-shrink:0;
    box-shadow: 0 0 20px rgba(74,222,128,0.3);
  ">🌾</div>
  <div>
    <div style="
      font-family:'Bebas Neue',sans-serif; font-size:2.2rem;
      color:#4ade80; letter-spacing:0.08em; line-height:1;
    ">AgroSmart AI</div>
    <div style="font-size:0.75rem; color:#64748b; letter-spacing:0.15em;
                text-transform:uppercase; margin-top:1px">
      Climate-Smart Agriculture Assistant  ·  Predict · Optimize · Sustain
    </div>
  </div>
  <div style="margin-left:auto; text-align:right">
    <div style="
      background:#1e2a1e; border:1px solid #166534;
      border-radius:99px; padding:4px 14px;
      font-size:0.7rem; color:#4ade80;
      font-family:'DM Mono',monospace; letter-spacing:0.08em;
    ">● LIVE</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR  —  Input Form
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="
      font-family:'Bebas Neue',sans-serif; font-size:1.4rem;
      color:#4ade80; letter-spacing:0.1em; padding:0.4rem 0 1rem 0;
      border-bottom:1px solid #2d3748; margin-bottom:1rem;
    ">⚗️ Farm Parameters</div>
    """, unsafe_allow_html=True)

    st.markdown("<p style='color:#64748b;font-size:0.7rem;margin-bottom:1rem'>SOIL NUTRIENTS (kg/ha)</p>", unsafe_allow_html=True)
    N = st.slider("Nitrogen (N)",        0,   200, 90,  help="Nitrogen content in soil")
    P = st.slider("Phosphorus (P)",      5,   145, 42,  help="Phosphorus content in soil")
    K = st.slider("Potassium (K)",       5,   205, 43,  help="Potassium content in soil")

    st.markdown("<p style='color:#64748b;font-size:0.7rem;margin:1rem 0 0.5rem'>WEATHER CONDITIONS</p>", unsafe_allow_html=True)
    temperature = st.slider("Temperature (°C)", 8.0,  44.0, 25.0, 0.1)
    humidity    = st.slider("Humidity (%)",     14.0, 100.0, 82.0, 0.1)
    rainfall    = st.slider("Rainfall (mm)",    20.0, 300.0, 200.0, 1.0)

    st.markdown("<p style='color:#64748b;font-size:0.7rem;margin:1rem 0 0.5rem'>SOIL CHEMISTRY</p>", unsafe_allow_html=True)
    ph = st.slider("Soil pH",               3.5, 9.5, 6.5, 0.1)

    st.markdown("<p style='color:#64748b;font-size:0.7rem;margin:1rem 0 0.5rem'>LOCATION</p>", unsafe_allow_html=True)
    region = st.selectbox("Region", ["Punjab","Uttar Pradesh","Maharashtra",
                                     "Karnataka","Tamil Nadu","West Bengal",
                                     "Rajasthan","Madhya Pradesh","Andhra Pradesh","Bihar"])
    season = st.selectbox("Season", ["Kharif (June–Oct)","Rabi (Nov–Mar)","Zaid (Mar–Jun)"])

    st.markdown("<br>", unsafe_allow_html=True)
    analyze_btn = st.button("🔍  ANALYZE MY FARM", type="primary")

    # Quick presets
    st.markdown("<p style='color:#64748b;font-size:0.7rem;margin:1.2rem 0 0.4rem'>QUICK PRESETS</p>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    rice_preset  = col_a.button("🌾 Rice",   use_container_width=True)
    wheat_preset = col_b.button("🌿 Wheat",  use_container_width=True)
    col_c, col_d = st.columns(2)
    mango_preset  = col_c.button("🥭 Mango",  use_container_width=True)
    maize_preset  = col_d.button("🌽 Maize",  use_container_width=True)

# Apply preset (rebuild sidebar values via session state workaround — use API call directly)
preset_data = None
if rice_preset:  preset_data = PRESETS["rice"]
if wheat_preset: preset_data = PRESETS["wheat"]
if mango_preset: preset_data = PRESETS["mango"]
if maize_preset: preset_data = PRESETS["maize"]

# ─────────────────────────────────────────────────────────────────────────────
# BACKEND CALL
# ─────────────────────────────────────────────────────────────────────────────
def call_predict(payload: dict):
    try:
        return predict_crop(payload), None
    except ApiClientError as e:
        return None, f"Error: {e}"

if analyze_btn or preset_data is not None:
    if preset_data:
        payload = {**preset_data, "region": region, "season": season}
    else:
        payload = dict(N=N, P=P, K=K, temperature=temperature,
                       humidity=humidity, ph=ph, rainfall=rainfall,
                       region=region, season=season)

    with st.spinner("🤖 AI is analyzing your farm data…"):
        time.sleep(0.4)  # small UX pause feels more "thoughtful"
        result, err = call_predict(payload)

    if err:
        st.error(err)
    else:
        st.session_state.result   = result
        st.session_state.analyzed = True
        st.session_state.payload  = payload

# ─────────────────────────────────────────────────────────────────────────────
# MAIN  —  Results Dashboard
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.analyzed:
    # ── Welcome / empty state ──
    st.markdown("""
    <div style="
      text-align:center; padding:4rem 2rem;
      border:1px dashed #2d3748; border-radius:20px;
      background:radial-gradient(ellipse at center,
        rgba(22,101,52,0.08) 0%, transparent 70%);
    ">
      <div style="font-size:4rem;margin-bottom:1rem">🌱</div>
      <div style="font-family:'Bebas Neue';font-size:2rem;color:#4ade80;
                  letter-spacing:0.1em">READY TO ANALYZE</div>
      <div style="color:#64748b;font-size:0.9rem;margin-top:0.5rem;max-width:420px;
                  margin-left:auto;margin-right:auto">
        Enter your farm parameters in the sidebar and click
        <strong style='color:#94a3b8'>Analyze My Farm</strong> to get
        AI-powered crop recommendations with sustainability impact scores.
      </div>
      <div style="margin-top:2rem;display:flex;justify-content:center;gap:2rem;
                  flex-wrap:wrap">
        <div style="text-align:center;color:#64748b;font-size:0.8rem">
          <div style="font-size:1.5rem">🤖</div>XGBoost ML Model<br>98.66% Accuracy
        </div>
        <div style="text-align:center;color:#64748b;font-size:0.8rem">
          <div style="font-size:1.5rem">💧</div>Water Efficiency<br>Tracking
        </div>
        <div style="text-align:center;color:#64748b;font-size:0.8rem">
          <div style="font-size:1.5rem">🌿</div>Carbon Footprint<br>Calculator
        </div>
        <div style="text-align:center;color:#64748b;font-size:0.8rem">
          <div style="font-size:1.5rem">💬</div>AI Chatbot<br>Advisor
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

else:
    r = st.session_state.result

    # ── TOP ROW: 4 quick stats ────────────────────────────────────────────────
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        stat_block("Recommended Crop", r["recommended_crop"].upper(),
                   icon="🌾", color="#4ade80")
    with q2:
        stat_block("ML Confidence",    f"{r['confidence']:.1f}",
                   unit="percent", icon="🎯", color="#38bdf8")
    with q3:
        stat_block("Water Saved",
                   f"{r['water_saved_liters_ha']:,}",
                   unit="liters / hectare", icon="💧", color="#38bdf8")
    with q4:
        stat_block("Green Impact Score",
                   f"{r['green_impact_score']}",
                   unit="out of 100", icon="🏆",
                   color="#4ade80" if r["green_impact_score"]>=70
                          else "#fbbf24" if r["green_impact_score"]>=40
                          else "#f87171")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── MAIN ROW: 3 columns ───────────────────────────────────────────────────
    left, mid, right = st.columns([1.1, 1.2, 1.0])

    # ────────── LEFT: Crop Prediction ────────────────────────────────────────
    with left:
        st.markdown(f"""
        <div style="
            background:var(--surface);
            border:1px solid var(--border);
            border-top:3px solid #4ade80;
            border-radius:var(--radius);
            padding:1.4rem;
            margin-bottom:0.8rem;
        ">
          <div style="font-size:0.65rem;color:#64748b;letter-spacing:0.15em;
                      text-transform:uppercase;margin-bottom:10px">
            🤖 ML Prediction  ·  XGBoost
          </div>
          <div style="font-family:'Bebas Neue';font-size:2.4rem;color:#4ade80;
                      letter-spacing:0.06em;line-height:1;margin-bottom:4px">
            {r['recommended_crop'].upper()}
          </div>
          <div style="font-size:0.8rem;color:#94a3b8;margin-bottom:16px">
            {r['crop_description']}
          </div>
          <div style="font-size:0.65rem;color:#64748b;letter-spacing:0.1em;
                      text-transform:uppercase;margin-bottom:8px">TOP 3 CANDIDATES</div>
          {confidence_bars(r['top_crops'])}
        </div>
        """, unsafe_allow_html=True)

        card(f"""
        <div style="font-size:0.65rem;color:#64748b;letter-spacing:0.15em;
                    text-transform:uppercase;margin-bottom:10px">
          🔄 Crop Rotation Advice
        </div>
        <div style="font-size:0.85rem;color:#e2e8f0;margin-bottom:6px">
          <span style="color:#94a3b8">Next season, grow:</span>
          <strong style="color:#fbbf24;text-transform:capitalize">
            &nbsp;{r['next_crop_rotation']}
          </strong>
        </div>
        <div style="font-size:0.75rem;color:#64748b">{r['rotation_reason']}</div>
        """, accent="#fbbf24")

    # ────────── MIDDLE: Sustainability Dashboard ──────────────────────────────
    with mid:
        st.markdown("""
        <div style="
            background:var(--surface);
            border:1px solid var(--border);
            border-top:3px solid #fbbf24;
            border-radius:var(--radius);
            padding:1.4rem;
            margin-bottom:0.8rem;
        ">
          <div style="font-size:0.65rem;color:#64748b;letter-spacing:0.15em;
                      text-transform:uppercase;margin-bottom:8px">
            🏆 Green Impact Score
          </div>
        """, unsafe_allow_html=True)
        gis_gauge(r["green_impact_score"])
        st.markdown("</div>", unsafe_allow_html=True)

        # Water + Carbon split
        w_col, c_col = st.columns(2)
        with w_col:
            stat_block("Water Saved",
                       f"{r['water_saved_pct']}%",
                       unit=f"{r['bathtubs_saved']:,} bathtubs",
                       icon="💧", color="#38bdf8")
        with c_col:
            stat_block("CO₂ Reduced",
                       f"{r['carbon_reduced_kg_ha']}",
                       unit=f"kg/ha  ·  {r['km_not_driven']:,} km",
                       icon="🌿", color="#4ade80")

        # Irrigation technique badge
        st.markdown(f"""
        <div style="
          background:linear-gradient(135deg,#1e2a1e,#0f1f0f);
          border:1px solid #166534; border-radius:10px;
          padding:1rem 1.2rem; margin-top:0.8rem;
          display:flex; align-items:center; gap:12px;
        ">
          <div style="font-size:1.6rem">💧</div>
          <div>
            <div style="font-size:0.65rem;color:#64748b;letter-spacing:0.1em;
                        text-transform:uppercase">Recommended Irrigation</div>
            <div style="font-size:0.95rem;color:#4ade80;font-weight:600;
                        margin-top:2px">{r['irrigation_technique']}</div>
            <div style="font-size:0.72rem;color:#64748b;margin-top:1px">
              Saves {r['water_saved_pct']}% water vs flood irrigation
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ────────── RIGHT: Practices + Explainability ─────────────────────────────
    with right:
        practices_html = "".join([
            f'<div style="display:flex;align-items:flex-start;gap:8px;'
            f'margin-bottom:10px;padding:8px 10px;background:#1e2a1e;'
            f'border-radius:8px;border-left:3px solid #166534">'
            f'<span style="color:#4ade80;margin-top:1px">✓</span>'
            f'<span style="font-size:0.78rem;color:#94a3b8;line-height:1.4">{p}</span>'
            f'</div>'
            for p in r["sustainable_practices"]
        ])
        card(f"""
        <div style="font-size:0.65rem;color:#64748b;letter-spacing:0.15em;
                    text-transform:uppercase;margin-bottom:10px">
          🌱 Sustainable Practices
        </div>
        {practices_html}
        """, accent="#166534")

        st.markdown(f"""
        <div style="
            background:var(--surface);
            border:1px solid var(--border);
            border-top:3px solid #38bdf8;
            border-radius:var(--radius);
            padding:1.4rem;
            margin-bottom:0.8rem;
        ">
          <div style="font-size:0.65rem;color:#64748b;letter-spacing:0.15em;
                      text-transform:uppercase;margin-bottom:10px">
            📊 Feature Importance
            <span style="color:#2d3748;margin-left:6px">— why this crop?</span>
          </div>
          {feature_importance_chart(r['feature_importances'])}
          <div style="font-size:0.65rem;color:#2d3748;margin-top:8px;text-align:right">
            Model accuracy: {r['model_accuracy_pct']}%
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # INPUT SUMMARY STRIP
    # ─────────────────────────────────────────────────────────────────────────
    p = st.session_state.payload
    st.markdown(f"""
    <div style="
      background:var(--surface); border:1px solid var(--border);
      border-radius:10px; padding:0.8rem 1.4rem;
      display:flex; flex-wrap:wrap; gap:1.5rem; align-items:center;
      margin:0.6rem 0 1.2rem;
    ">
      <span style="font-size:0.65rem;color:#64748b;letter-spacing:0.1em;
                   text-transform:uppercase">Your Inputs</span>
      {''.join([
        f'<span style="font-family:DM Mono,monospace;font-size:0.72rem;'
        f'color:#94a3b8"><span style="color:#4ade80">{k.upper()}</span> {v}</span>'
        for k, v in [("N",p["N"]),("P",p["P"]),("K",p["K"]),
                     ("Temp",f"{p['temperature']}°C"),
                     ("Humidity",f"{p['humidity']}%"),
                     ("pH",p["ph"]),
                     ("Rainfall",f"{p['rainfall']}mm"),
                     ("Region",p["region"]),
                     ("Season",p["season"])]
      ])}
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CHATBOT SECTION
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="
  font-family:'Bebas Neue',sans-serif; font-size:1.5rem; color:#4ade80;
  letter-spacing:0.1em; padding:0.6rem 0 0.3rem;
  border-top:1px solid #2d3748; margin-top:0.4rem;
">💬 AgroBot — AI Farming Advisor</div>
<div style="font-size:0.75rem;color:#64748b;margin-bottom:1rem">
  Ask about irrigation, fertilizers, crop rotation, pests, sustainability…
</div>
""", unsafe_allow_html=True)

chat_col, tip_col = st.columns([2.2, 1])

with chat_col:
    # Chat history
    chat_box = st.container()
    with chat_box:
        if not st.session_state.messages:
            st.markdown("""
            <div style="
              text-align:center; padding:1.5rem;
              border:1px dashed #2d3748; border-radius:12px;
              color:#64748b; font-size:0.8rem;
            ">
              👋 Hi! I'm AgroBot. Ask me anything about your farm.<br>
              <span style="color:#4ade80">No API key needed</span>
              — I have built-in smart responses!
            </div>
            """, unsafe_allow_html=True)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"],
                                 avatar="🌾" if msg["role"]=="assistant" else "👨‍🌾"):
                st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask about your crops, soil, water, sustainability…"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Call backend /chat
        farm_ctx = st.session_state.result or {}
        try:
            reply = chat(prompt, farm_ctx).get("reply", "Sorry, I couldn't process that.")
        except ApiClientError:
            reply = "⚠️ Chatbot backend offline or not yet integrated."

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

with tip_col:
    st.markdown("""
    <div style="
      background:var(--surface); border:1px solid var(--border);
      border-radius:12px; padding:1.2rem;
    ">
      <div style="font-size:0.65rem;color:#64748b;letter-spacing:0.1em;
                  text-transform:uppercase;margin-bottom:10px">
        💡 Suggested Questions
      </div>
    """, unsafe_allow_html=True)

    suggestions = [
        "💧 What irrigation saves most water?",
        "🌿 How can I reduce carbon footprint?",
        "🔄 What should I plant next season?",
        "🧪 How to improve soil nutrients?",
        "🐛 How to manage pests sustainably?",
        "📊 Explain my Green Impact Score",
    ]
    for s in suggestions:
        if st.button(s, use_container_width=True, key=f"sug_{s[:10]}"):
            st.session_state.messages.append({"role": "user", "content": s})
            farm_ctx = st.session_state.result or {}
            try:
                reply = chat(s, farm_ctx).get("reply", "Sorry, I couldn't process that.")
            except ApiClientError:
                reply = "⚠️ Backend offline or not yet integrated."
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Clear chat
    if st.session_state.messages:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="
  border-top:1px solid #2d3748; margin-top:2rem; padding:1rem 0;
  display:flex; justify-content:space-between; align-items:center;
  flex-wrap:wrap; gap:0.5rem;
">
  <div style="font-size:0.7rem;color:#2d3748">
    AgroSmart AI  ·  Spandan '26  ·  AI Foresight Competition
  </div>
  <div style="font-size:0.7rem;color:#2d3748;font-family:'DM Mono',monospace">
    XGBoost · FastAPI · Streamlit · Claude API
  </div>
</div>
""", unsafe_allow_html=True)
