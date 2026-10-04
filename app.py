import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# ================== ⚙️ الإعدادات ==================
BRAND_NAME   = "FAISAL SIGNALS"
BRAND_SUB    = "AI TRADING SIGNALS"
OWNER_NAME   = "فيصل"
REFRESH_SEC  = 30

PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/JPY": "GBPJPY=X",
    "USD/TRY": "USDTRY=X",
    "EUR/GBP": "EURGBP=X",
    "USD/JPY": "USDJPY=X",
    "GBP/USD": "GBPUSD=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
}

TIMEFRAMES = {
    "1 دقيقة":  "1m",
    "2 دقيقة":  "2m",
    "5 دقائق":  "5m",
    "15 دقيقة": "15m",
    "30 دقيقة": "30m",
}
# ==================================================

st.set_page_config(
    page_title=f"{BRAND_NAME} | إشارات",
    page_icon="🦈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ================== 🔐 كلمة المرور ==================
def check_password():
    def password_entered():
        if st.session_state.get("password") == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.markdown("""
    <style>
    .login-box {
        max-width: 400px; margin: 60px auto; padding: 40px 30px;
        background: linear-gradient(160deg, #17171d 0%, #0d0d12 100%);
        border-radius: 24px; border: 1px solid rgba(212,175,55,0.3);
        box-shadow: 0 0 60px rgba(212,175,55,0.15); text-align: center;
    }
    .login-logo { font-size: 60px; margin-bottom: 10px; }
    .login-title { color: #d4af37; font-size: 22px; font-weight: 900;
        letter-spacing: 4px; margin-bottom: 5px; }
    .login-sub { color: #777; font-size: 12px; letter-spacing: 4px;
        margin-bottom: 25px; }
    </style>
    <div class="login-box">
        <div class="login-logo">🦈</div>
        <div class="login-title">FAISAL SIGNALS</div>
        <div class="login-sub">منطقة خاصة</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.text_input("🔒 كلمة المرور", type="password",
                      on_change=password_entered, key="password",
                      placeholder="أدخل كلمة المرور...")
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ كلمة المرور غير صحيحة")
        st.caption("هذا الموقع خاص — الدخول بإذن فقط.")
    return False

if not check_password():
    st.stop()
# ====================================================

st_autorefresh(interval=REFRESH_SEC * 1000, key="auto_refresh")

if "history" not in st.session_state:
    st.session_state.history = []

# ================== CSS ==================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; }
.stApp {
    background: radial-gradient(circle at 50% 0%, #1a0a0a 0%, #08080c 60%) !important;
    direction: rtl;
}
.brand-header { text-align: center; padding: 10px 0 20px 0;
    border-bottom: 1px solid rgba(212,175,55,0.2); margin-bottom: 25px; }
.brand-name { font-size: 38px; font-weight: 900; color: #d4af37;
    letter-spacing: 5px; margin: 0; text-shadow: 0 0 25px rgba(212,175,55,0.4); }
.brand-sub { color: #777; font-size: 12px; letter-spacing: 8px; margin-top: 4px; }
.brand-owner { color: #666; font-size: 13px; margin-top: 8px; }
.signal-card { background: linear-gradient(160deg, #17171d 0%, #0d0d12 100%);
    border-radius: 24px; padding: 28px 20px; text-align: center; margin-bottom: 20px; }
.signal-buy { border: 1px solid rgba(0,255,136,0.35);
    box-shadow: 0 0 60px rgba(0,255,136,0.15); }
.signal-sell { border: 1px solid rgba(255,50,80,0.35);
    box-shadow: 0 0 60px rgba(255,50,80,0.15); }
.signal-title { color: #999; font-size: 13px; letter-spacing: 8px; margin-bottom: 10px; }
.pair-title { color: #fff; font-size: 22px; font-weight: 700; margin-bottom: 8px; }
.triangle-buy { width: 0; height: 0;
    border-left: 32px solid transparent; border-right: 32px solid transparent;
    border-bottom: 46px solid #00ff88; margin: 16px auto 8px auto;
    filter: drop-shadow(0 0 22px rgba(0,255,136,0.7)); }
.triangle-sell { width: 0; height: 0;
    border-left: 32px solid transparent; border-right: 32px solid transparent;
    border-top: 46px solid #ff3250; margin: 16px auto 8px auto;
    filter: drop-shadow(0 0 22px rgba(255,50,80,0.7)); }
.dir-buy { font-size: 48px; font-weight: 900; color: #00ff88;
    margin: 4px 0; text-shadow: 0 0 35px rgba(0,255,136,0.6); letter-spacing: 3px; }
.dir-sell { font-size: 48px; font-weight: 900; color: #ff3250;
    margin: 4px 0; text-shadow: 0 0 35px rgba(255,50,80,0.6); letter-spacing: 3px; }
.chips-row { display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; margin: 15px 0 8px 0; }
.chip { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px; padding: 10px 14px; color: #ccc; font-size: 12px; min-width: 110px; }
.chip b { color: #fff; display: block; font-size: 14px; margin-top: 3px; }
.conf-box { margin-top: 18px; display: inline-block; padding: 18px 28px; border-radius: 50%;
    background: radial-gradient(circle, rgba(212,175,55,0.1), transparent 70%); }
.conf-label { color: #888; font-size: 12px; letter-spacing: 5px; margin-bottom: 5px; }
.conf-value { font-size: 40px; font-weight: 900; color: #d4af37;
    text-shadow: 0 0 25px rgba(212,175,55,0.6); }
.mini-card { background: #121216; border-radius: 14px; padding: 14px 16px;
    margin-bottom: 10px; display: flex; justify-content: space-between;
    align-items: center; border-right: 4px solid #333; }
.mini-buy { border-right-color: #00ff88; }
.mini-sell { border-right-color: #ff3250; }
.mini-none { border-right-color: #555; }
.mini-pair { font-size: 15px; font-weight: 700; color: #fff; }
.mini-dir-buy { color: #00ff88; font-weight: 700; font-size: 13px; }
.mini-dir-sell { color: #ff3250; font-weight: 700; font-size: 13px; }
.mini-dir-none { color: #888; font-weight: 700; font-size: 13px; }
.mini-conf { color: #d4af37; font-weight: 700; font-size: 14px; }
.hist-row { display: flex; justify-content: space-between; background: #121216;
    padding: 10px 14px; border-radius: 10px; margin-bottom: 6px;
    border-right: 3px solid #333; font-size: 12px; }
.hist-buy { border-right-color: #00ff88; }
.hist-sell { border-right-color: #ff3250; }
.disclaimer { text-align: center; color: #555; font-size: 11px;
    margin-top: 25px; padding: 15px; border-top: 1px solid rgba(255,255,255,0.05); }
div[data-testid="stSelectbox"] label { color: #aaa !important; font-weight: 600; }
div[data-testid="stSelectbox"] > div > div {
    background: #131318 !important; border: 1px solid rgba(212,175,55,0.2) !important;
    border-radius: 12px !important; color: #fff !important; }
.stButton button { background: linear-gradient(135deg, #d4af37, #a8862a) !important;
    color: #000 !important; font-weight: 700 !important; border: none !important;
    border-radius: 12px !important; padding: 8px 22px !important;
    font-family: 'Cairo', sans-serif !important; font-size: 14px !important; }
@media (max-width: 768px) {
    .brand-name { font-size: 26px !important; letter-spacing: 3px !important; }
    .dir-buy, .dir-sell { font-size: 36px !important; }
    .conf-value { font-size: 34px !important; }
    .pair-title { font-size: 18px !important; }
}
</style>
""", unsafe_allow_html=True)

# ================== الدوال ==================
def ema(s, n): return s.ewm(span=n, adjust=False).mean()

def rsi(s, n=14):
    d = s.diff()
    g = d.where(d > 0, 0.0)
    l = -d.where(d < 0, 0.0)
    ag = g.rolling(n).mean()
    al = l.rolling(n).mean()
    return 100 - 100 / (1 + ag / al)

def macd(s, f=12, sl=26, sig=9):
    m = ema(s, f) - ema(s, sl)
    sg = ema(m, sig)
    return m, sg, m - sg

def bollinger(s, n=20, k=2):
    mid = s.rolling(n).mean()
    sd = s.rolling(n).std()
    return mid + k*sd, mid, mid - k*sd

@st.cache_data(ttl=25)
def fetch(symbol, interval):
    try:
        df = yf.download(symbol, interval=interval, period="5d",
                         progress=False, auto_adjust=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()

def analyze(symbol, interval):
    df = fetch(symbol, interval)
    if df.empty or len(df) < 50:
        return None
    close = df["Close"].dropna()
    if len(close) < 50:
        return None
    df = df.loc[close.index].copy()
    df["EMA9"]  = ema(df["Close"], 9)
    df["EMA21"] = ema(df["Close"], 21)
    df["RSI"]   = rsi(df["Close"], 14)
    m, sg, h = macd(df["Close"])
    df["MACD_H"] = h
    up, mid, lo = bollinger(df["Close"])
    df["BB_UP"], df["BB_LO"] = up, lo

    last = df.iloc[-1]
    price = float(last["Close"])
    bull = bear = 0
    reasons = []

    if last["EMA9"] > last["EMA21"]:
        bull += 1; reasons.append("EMA9 فوق EMA21")
    else:
        bear += 1; reasons.append("EMA9 تحت EMA21")

    if last["MACD_H"] > 0:
        bull += 1; reasons.append("MACD إيجابي")
    else:
        bear += 1; reasons.append("MACD سلبي")

    if last["RSI"] < 30:
        bull += 1; reasons.append(f"RSI تشبع بيع ({last['RSI']:.0f})")
    elif last["RSI"] > 70:
        bear += 1; reasons.append(f"RSI تشبع شراء ({last['RSI']:.0f})")

    if price <= last["BB_LO"]:
        bull += 1; reasons.append("السعر عند بولنجر السفلي")
    elif price >= last["BB_UP"]:
        bear += 1; reasons.append("السعر عند بولنجر العلوي")

    total = bull + bear
    if total == 0: return None
    if bull > bear:
        direction, conf = "BUY", int(bull/total*100)
    elif bear > bull:
        direction, conf = "SELL", int(bear/total*100)
    else:
        return None

    return {"direction": direction, "confidence": conf, "price": price,
            "reasons": reasons, "time": datetime.now().strftime("%H:%M:%S"), "df": df}

# ================== الواجهة ==================
st.markdown(f"""
<div class="brand-header">
    <div class="brand-name">{BRAND_NAME}</div>
    <div class="brand-sub">{BRAND_SUB}</div>
    <div class="brand-owner">by {OWNER_NAME}</div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns([2, 2, 1])
with c1:
    pair_name = st.selectbox("🌍 الزوج", list(PAIRS.keys()))
with c2:
    tf_name = st.selectbox("⏱️ الإطار", list(TIMEFRAMES.keys()), index=2)
with c3:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄"):
        st.cache_data.clear()
        st.rerun()

symbol = PAIRS[pair_name]
interval = TIMEFRAMES[tf_name]
result = analyze(symbol, interval)

if result is None:
    st.markdown(f"""
    <div class="signal-card" style="border:1px solid rgba(255,255,255,0.08);">
        <div class="signal-title">SİNYAL HAZIR DEĞİL</div>
        <div class="pair-title">{pair_name}</div>
        <div style="color:#888; font-size:18px; margin-top:25px;">
            لا توجد إشارة واضحة حالياً...
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    is_buy = result["direction"] == "BUY"
    cls_card = "signal-buy" if is_buy else "signal-sell"
    cls_tri = "triangle-buy" if is_buy else "triangle-sell"
    cls_dir = "dir-buy" if is_buy else "dir-sell"
    dir_text = "أعلى ⬆" if is_buy else "أسفل ⬇"
    dir_en = "CALL / BUY" if is_buy else "PUT / SELL"

    st.markdown(f"""
    <div class="signal-card {cls_card}">
        <div class="signal-title">SİNYAL HAZIR</div>
        <div class="pair-title">{pair_name} · {tf_name}</div>
        <div class="{cls_tri}"></div>
        <div class="{cls_dir}">{dir_text}</div>
        <div style="color:#aaa; font-size:12px; letter-spacing:4px;">{dir_en}</div>
        <div class="chips-row">
            <div class="chip">الزوج<b>{pair_name}</b></div>
            <div class="chip">الإطار<b>{tf_name}</b></div>
            <div class="chip">السعر<b>{result['price']:.5f}</b></div>
        </div>
        <div class="conf-box">
            <div class="conf-label">OLASILIK</div>
            <div class="conf-value">%{result['confidence']}</div>
        </div>
        <div style="color:#777; font-size:11px; margin-top:15px;">
            {' • '.join(result['reasons'])}
        </div>
    </div>
    """, unsafe_allow_html=True)

    sig_key = f"{pair_name}_{interval}_{result['direction']}_{result['time']}"
    if sig_key not in [h["key"] for h in st.session_state.history]:
        st.session_state.history.insert(0, {
            "key": sig_key, "pair": pair_name, "tf": tf_name,
            "dir": result["direction"], "conf": result["confidence"],
            "time": result["time"]})
        st.session_state.history = st.session_state.history[:20]

if result and "df" in result:
    st.markdown("### 📈 الرسم البياني")
    df_chart = result["df"].tail(80)
    fig = go.Figure(data=[go.Candlestick(
        x=df_chart.index, open=df_chart["Open"], high=df_chart["High"],
        low=df_chart["Low"], close=df_chart["Close"],
        increasing_line_color="#00ff88", decreasing_line_color="#ff3250",
        name=pair_name)])
    fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["EMA9"],
        line=dict(color="#3b82f6", width=1.5), name="EMA9"))
    fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["EMA21"],
        line=dict(color="#d4af37", width=1.5), name="EMA21"))
    fig.update_layout(template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0d0d12",
        height=350, margin=dict(l=5, r=5, t=10, b=10),
        xaxis_rangeslider_visible=False,
        font=dict(family="Cairo", color="#ccc"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### 📊 جميع الأزواج")
cols = st.columns(2)
for i, (pname, psym) in enumerate(PAIRS.items()):
    r = analyze(psym, interval)
    with cols[i % 2]:
        if r is None:
            st.markdown(f"""
            <div class="mini-card mini-none">
                <div><div class="mini-pair">{pname}</div>
                <div class="mini-dir-none">لا إشارة</div></div>
                <div class="mini-conf">—</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            buy = r["direction"] == "BUY"
            cls = "mini-buy" if buy else "mini-sell"
            dcls = "mini-dir-buy" if buy else "mini-dir-sell"
            dtxt = "▲ CALL" if buy else "▼ PUT"
            st.markdown(f"""
            <div class="mini-card {cls}">
                <div><div class="mini-pair">{pname}</div>
                <div class="{dcls}">{dtxt}</div></div>
                <div class="mini-conf">%{r['confidence']}</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("### 📝 آخر الإشارات")
if not st.session_state.history:
    st.info("لا يوجد سجل بعد.")
else:
    for h in st.session_state.history:
        cls = "hist-buy" if h["dir"] == "BUY" else "hist-sell"
        dtxt = "▲ CALL" if h["dir"] == "BUY" else "▼ PUT"
        st.markdown(f"""
        <div class="hist-row {cls}">
            <span style="color:#fff; font-weight:700;">{h['pair']}</span>
            <span style="color:#aaa;">{h['tf']}</span>
            <span style="color:{'#00ff88' if h['dir']=='BUY' else '#ff3250'}; font-weight:700;">{dtxt}</span>
            <span style="color:#d4af37; font-weight:700;">%{h['conf']}</span>
            <span style="color:#666;">{h['time']}</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown(f"""
<div class="disclaimer">
    ⚠️ تحليل آلي وليس نصيحة استثمارية. التداول فيه مخاطرة.<br>
    {BRAND_NAME} © {datetime.now().year} — by فيصل
</div>
""", unsafe_allow_html=True)
