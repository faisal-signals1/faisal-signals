import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
import time

BRAND_NAME = "FAISAL SIGNALS"
BRAND_SUB = "AI TRADING SYSTEM"
OWNER_NAME = "فيصل"
REFRESH_SEC = 30
ALERT_CONF = 80

PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/JPY": "GBPJPY=X",
    "USD/TRY": "USDTRY=X",
    "EUR/GBP": "EURGBP=X",
    "USD/JPY": "USDJPY=X",
    "GBP/USD": "GBPUSD=X",
    "A(
UD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
}

TIMEFRAMES = {
    "1 دقيقة": "1m",
    "2 دقيقة": "2m",
    "5 دقائق": "5m",
    "15 دقيقة": "15m",
    "30 دقيقة": "30m",
}

st.set_page    page_title=f"{BRAND_NAME} | إشارات",
    page_icon="🦈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
    .login-box { max-width: 400px; margin: 60px auto; padding: 45px 35px;
        background: linear-gradient(145deg, #0f0f16 0%, #05050a 100%);
        border-radius: 28px; border: 1px solid rgba(0,212,255,0.25);
        box-shadow: 0 0 80px rgba(0,212,255,0.15);
        text-align: center; }
    .login-logo { font-size: 64px; margin-bottom: 15px;
        filter: drop-shadow(0 0 25px rgba(0,212,255,0.6)); }
    .login-title { color: #00d4ff; font-size: 24px; font-weight: 900;
        letter-spacing: 6px; margin-bottom: 8px; }
    .login-sub { color: #555; font-size: 11px; letter-spacing: 6px; margin-bottom: 30px; }
    </style>
    <div class="login-box">
        <div class="login-logo">🦈</div>
        <div class="login-title">FAISAL SIGNALS</div>
        <div class="login-sub">SECURE ACCESS</div>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.text_input("🔒 كلمة المرور", type="password",
                      on_change=password_entered, key="password",
                      placeholder="أدخل كلمة المرور...")
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ كلمة المرور غير صحيحة")
    return False

if not check_password():
    st.stop()

st_autorefresh(interval=REFRESH_SEC * 1000, key="auto_refresh")

if "history" not in st.session_state:
    st.session_state.history = []

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

def stochastic(df, n=14, d=3):
    low_n = df['Low'].rolling(n).min()
    high_n = df['High'].rolling(n).max()
    k = 100 * (df['Close'] - low_n) / (high_n - low_n)
    d_line = k.rolling(d).mean()
    return k, d_line

def calc_atr(df, n=14):
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def detect_candle_pattern(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    body = abs(last['Close'] - last['Open'])
    range_ = last['High'] - last['Low']
    upper_shadow = last['High'] - max(last['Close'], last['Open'])
    lower_shadow = min(last['Close'], last['Open']) - last['Low']
    if range_ == 0:
        return None, 0
    if (prev['Close'] < prev['Open'] and last['Close'] > last['Open'] and
        last['Close'] > prev['Open'] and last['Open'] < prev['Close']):
        return "Bullish Engulfing", 1
    elif (prev['Close'] > prev['Open'] and last['Close'] < last['Open'] and
          last['Close'] < prev['Open'] and last['Open'] > prev['Close']):
        return "Bearish Engulfing", -1
    elif lower_shadow > body * 2 and upper_shadow < body * 0.5:
        return "Hammer", 1
    elif upper_shadow > body * 2 and lower_shadow < body * 0.5:
        return "Shooting Star", -1
    elif body < range_ * 0.1:
        return "Doji", 0
    return None, 0

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
    if df.empty or len(df) < 60:
        return None
    close = df["Close"].dropna()
    if len(close) < 60:
        return None
    df = df.loc[close.index].copy()
    df["EMA9"] = ema(df["Close"], 9)
    df["EMA21"] = ema(df["Close"], 21)
    df["EMA50"] = ema(df["Close"], 50)
    df["RSI"] = rsi(df["Close"], 14)
    m, sg, h = macd(df["Close"])
    df["MACD_H"] = h
    df["MACD"] = m
    df["MACD_SIG"] = sg
    up, mid, lo = bollinger(df["Close"])
    df["BB_UP"], df["BB_LO"], df["BB_MID"] = up, lo, mid
    k, d_line = stochastic(df, 14, 3)
    df["STOCH_K"] = k
    df["STOCH_D"] = d_line
    df["ATR"] = calc_atr(df, 14)

    last = df.iloc[-1]
    price = float(last["Close"])
    score = 0
    max_score = 0
    reasons = []

    max_score += 2
    if last["EMA9"] > last["EMA21"] and last["EMA21"] > last["EMA50"]:
        score += 2; reasons.append("✅ ترتيب EMA صاعد قوي")
    elif last["EMA9"] > last["EMA21"]:
        score += 1; reasons.append("✅ EMA9 فوق EMA21")
    elif last["EMA9"] < last["EMA21"] and last["EMA21"] < last["EMA50"]:
        score -= 2; reasons.append("🔻 ترتيب EMA هابط قوي")
    else:
        score -= 1; reasons.append("🔻 EMA9 تحت EMA21")

    max_score += 2
    if last["MACD_H"] > 0 and last["MACD"] > last["MACD_SIG"]:
        score += 2; reasons.append("✅ MACD صاعد مؤكد")
    elif last["MACD_H"] > 0:
        score += 1; reasons.append("✅ MACD إيجابي")
    elif last["MACD_H"] < 0 and last["MACD"] < last["MACD_SIG"]:
        score -= 2; reasons.append("🔻 MACD هابط مؤكد")
    else:
        score -= 1; reasons.append("🔻 MACD سلبي")

    max_score += 2
    if last["RSI"] < 30:
        score += 2; reasons.append(f"✅ RSI تشبع بيع ({last['RSI']:.0f})")
    elif last["RSI"] > 70:
        score -= 2; reasons.append(f"🔻 RSI تشبع شراء ({last['RSI']:.0f})")
    elif 50 < last["RSI"] < 70:
        score += 1; reasons.append(f"✅ RSI قوي ({last['RSI']:.0f})")
    elif 30 < last["RSI"] < 50:
        score -= 1; reasons.append(f"🔻 RSI ضعيف ({last['RSI']:.0f})")

    max_score += 1.5
    bb_range = last["BB_UP"] - last["BB_LO"]
    if bb_range > 0:
        bb_pos = (price - last["BB_LO"]) / bb_range
        if bb_pos <= 0.1:
            score += 1.5; reasons.append("✅ قاع بولنجر")
        elif bb_pos >= 0.9:
            score -= 1.5; reasons.append("🔻 قمة بولنجر")

    max_score += 1.5
    if not pd.isna(last["STOCH_K"]) and not pd.isna(last["STOCH_D"]):
        if last["STOCH_K"] < 20 and last["STOCH_K"] > last["STOCH_D"]:
            score += 1.5; reasons.append("✅ Stochastic تقاطع صاعد")
        elif last["STOCH_K"] > 80 and last["STOCH_K"] < last["STOCH_D"]:
            score -= 1.5; reasons.append("🔻 Stochastic تقاطع هابط")

    max_score += 1
    pattern, pat_signal = detect_candle_pattern(df)
    if pattern:
        if pat_signal > 0:
            score += 1; reasons.append(f"✅ {pattern}")
        elif pat_signal < 0:
            score -= 1; reasons.append(f"🔻 {pattern}")

    if max_score == 0:
        return None
    confidence = int(abs(score) / max_score * 100)
    if confidence < 55:
        return None
    direction = "BUY" if score > 0 else "SELL"
    if confidence >= 85:
        quality = "ممتازة ⭐⭐⭐"
    elif confidence >= 75:
        quality = "قوية ⭐⭐"
    elif confidence >= 65:
        quality = "جيدة ⭐"
    else:
        quality = "متوسطة"

    return {
        "direction": direction,
        "confidence": confidence,
        "price": price,
        "reasons": reasons,
        "quality": quality,
        "atr": float(last["ATR"]) if not pd.isna(last["ATR"]) else 0,
        "rsi": float(last["RSI"]),
        "time": datetime.now().strftime("%H:%M:%S"),
        "df": df
    }

def support_resistance(df, window=20):
    highs = df['High'].rolling(window).max().iloc[-1]
    lows = df['Low'].rolling(window).min().iloc[-1]
    return float(highs), float(lows)

def get_timeframe_seconds(interval):
    m = {"1m": 60, "2m": 120, "5m": 300, "15m": 900, "30m": 1800}
    return m.get(interval, 60)

def seconds_until_candle_end(interval):
    sec = get_timeframe_seconds(interval)
    now = time.time()
    return int(sec - (now % sec))

    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; }
.stApp { background: radial-gradient(ellipse at 0% 0%, rgba(0,212,255,0.06) 0%, transparent 45%), radial-gradient(ellipse at 100% 100%, rgba(138,43,226,0.06) 0%, transparent 45%), linear-gradient(180deg, #0a0a12 0%, #050508 100%) !important; direction: rtl; }
.brand-header { text-align: center; padding: 25px 0 30px 0; margin-bottom: 25px; position: relative; }
.brand-header::after { content: ''; position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); width: 200px; height: 1px; background: linear-gradient(90deg, transparent, #00d4ff, transparent); box-shadow: 0 0 20px rgba(0,212,255,0.5); }
.brand-name { font-size: 44px; font-weight: 900; background: linear-gradient(135deg, #00d4ff 0%, #0099ff 50%, #0066cc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; letter-spacing: 8px; margin: 0; filter: drop-shadow(0 0 30px rgba(0,212,255,0.4)); }
.brand-sub { color: #4a5568; font-size: 11px; letter-spacing: 12px; margin-top: 8px; }
.brand-owner { color: #3a3a45; font-size: 12px; margin-top: 12px; font-style: italic; }
.signal-card { background: linear-gradient(145deg, #0f0f16 0%, #05050a 100%); border-radius: 28px; padding: 35px 25px; text-align: center; margin-bottom: 22px; position: relative; overflow: hidden; }
.signal-buy { border: 1px solid rgba(0,255,136,0.3); box-shadow: 0 0 80px rgba(0,255,136,0.15), inset 0 0 80px rgba(0,255,136,0.03); }
.signal-sell { border: 1px solid rgba(255,45,85,0.3); box-shadow: 0 0 80px rgba(255,45,85,0.15), inset 0 0 80px rgba(255,45,85,0.03); }
.signal-title { color: #4a5568; font-size: 12px; letter-spacing: 12px; margin-bottom: 15px; font-weight: 600; }
.pair-title { color: #ffffff; font-size: 26px; font-weight: 700; margin-bottom: 15px; letter-spacing: 1px; }
.triangle-buy { width: 0; height: 0; border-left: 45px solid transparent; border-right: 45px solid transparent; border-bottom: 65px solid #00ff88; margin: 25px auto 15px auto; filter: drop-shadow(0 0 35px rgba(0,255,136,0.9)); animation: pulse-buy 2s ease-in-out infinite; }
.triangle-sell { width: 0; height: 0; border-left: 45px solid transparent; border-right: 45px solid transparent; border-top: 65px solid #ff2d55; margin: 25px auto 15px auto; filter: drop-shadow(0 0 35px rgba(255,45,85,0.9)); animation: pulse-sell 2s ease-in-out infinite; }
@keyframes pulse-buy { 0%, 100% { filter: drop-shadow(0 0 35px rgba(0,255,136,0.9)); } 50% { filter: drop-shadow(0 0 55px rgba(0,255,136,1)); } }
@keyframes pulse-sell { 0%, 100% { filter: drop-shadow(0 0 35px rgba(255,45,85,0.9)); } 50% { filter: drop-shadow(0 0 55px rgba(255,45,85,1)); } }
.dir-buy { font-size: 58px; font-weight: 900; color: #00ff88; margin: 8px 0; letter-spacing: 5px; text-shadow: 0 0 45px rgba(0,255,136,0.8); }
.dir-sell { font-size: 58px; font-weight: 900; color: #ff2d55; margin: 8px 0; letter-spacing: 5px; text-shadow: 0 0 45px rgba(255,45,85,0.8); }
.chips-row { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin: 22px 0 12px 0; }
.chip { background: linear-gradient(145deg, #1a1a24, #12121a); border: 1px solid rgba(0,212,255,0.15); border-radius: 16px; padding: 12px 18px; color: #4a5568; font-size: 11px; min-width: 120px; transition: all 0.3s ease; }
.chip:hover { border-color: rgba(0,212,255,0.5); transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0,212,255,0.15); }
.chip b { color: #ffffff; display: block; font-size: 15px; margin-top: 5px; font-weight: 700; }
.conf-box { margin-top: 25px; display: inline-block; padding: 28px 45px; border-radius: 50%; background: radial-gradient(circle, rgba(0,212,255,0.15), transparent 70%), linear-gradient(145deg, #0f0f16, #05050a); border: 2px solid rgba(0,212,255,0.3); box-shadow: 0 0 70px rgba(0,212,255,0.2), inset 0 0 50px rgba(0,212,255,0.05); }
.conf-label { color: #4a5568; font-size: 11px; letter-spacing: 7px; margin-bottom: 8px; font-weight: 600; }
.conf-value { font-size: 48px; font-weight: 900; background: linear-gradient(135deg, #00d4ff, #0099ff, #0066cc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; filter: drop-shadow(0 0 25px rgba(0,212,255,0.7)); }
.mini-card { background: linear-gradient(145deg, #0f0f16, #05050a); border-radius: 16px; padding: 16px 18px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; border-right: 4px solid #1a1a24; transition: all 0.2s ease; }
.mini-card:hover { transform: translateX(-4px); }
.mini-buy { border-right-color: #00ff88; box-shadow: inset -50px 0 50px -50px rgba(0,255,136,0.4); }
.mini-sell { border-right-color: #ff2d55; box-shadow: inset -50px 0 50px -50px rgba(255,45,85,0.4); }
.mini-none { border-right-color: #1a1a24; opacity: 0.5; }
.mini-pair { font-size: 16px; font-weight: 700; color: #ffffff; }
.mini-dir-buy { color: #00ff88; font-weight: 700; font-size: 13px; margin-top: 3px; }
.mini-dir-sell { color: #ff2d55; font-weight: 700; font-size: 13px; margin-top: 3px; }
.mini-dir-none { color: #4a5568; font-weight: 600; font-size: 13px; margin-top: 3px; }
.mini-conf { background: linear-gradient(135deg, #00d4ff, #0099ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 900; font-size: 17px; }
.hist-row { display: flex; justify-content: space-between; background: linear-gradient(145deg, #0f0f16, #05050a); padding: 12px 16px; border-radius: 12px; margin-bottom: 8px; border-right: 3px solid #1a1a24; font-size: 12px; }
.hist-buy { border-right-color: #00ff88; }
.hist-sell { border-right-color: #ff2d55; }
.timer-box { text-align: center; padding: 20px; margin: 12px 0; background: linear-gradient(145deg, #0f0f16 0%, #05050a 100%); border-radius: 20px; border: 1px solid rgba(0,212,255,0.2); box-shadow: 0 0 50px rgba(0,212,255,0.08); }
.timer-label { color: #4a5568; font-size: 11px; letter-spacing: 6px; margin-bottom: 10px; font-weight: 600; }
.timer-value { font-size: 44px; font-weight: 900; background: linear-gradient(135deg, #00d4ff, #0099ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-variant-numeric: tabular-nums; filter: drop-shadow(0 0 20px rgba(0,212,255,0.6)); }
.timer-bar { height: 8px; background: #1a1a24; border-radius: 4px; margin-top: 12px; overflow: hidden; }
.timer-bar-fill { height: 100%; background: linear-gradient(90deg, #00d4ff, #0099ff, #ff2d55); border-radius: 4px; transition: width 1s linear; }
.disclaimer { text-align: center; color: #3a3a45; font-size: 11px; margin-top: 30px; padding: 20px; border-top: 1px solid rgba(255,255,255,0.05); line-height: 1.8; }
div[data-testid="stSelectbox"] label { color: #4a5568 !important; font-weight: 600; font-size: 13px; }
div[data-testid="stSelectbox"] > div > div { background: linear-gradient(145deg, #0f0f16, #05050a) !important; border: 1px solid rgba(0,212,255,0.2) !important; border-radius: 14px !important; color: #ffffff !important; font-weight: 600; }
.stButton button { background: linear-gradient(135deg, #00d4ff, #0099ff, #0066cc) !important; color: #ffffff !important; font-weight: 900 !important; border: none !important; border-radius: 14px !important; padding: 10px 26px !important; font-family: 'Cairo', sans-serif !important; font-size: 15px !important; box-shadow: 0 4px 25px rgba(0,212,255,0.4); transition: all 0.3s ease; }
.stButton button:hover { transform: translateY(-2px); box-shadow: 0 6px 35px rgba(0,212,255,0.6); }
h3 { color: #00d4ff !important; font-weight: 700 !important; letter-spacing: 1px; border-bottom: 1px solid rgba(0,212,255,0.15); padding-bottom: 10px; margin-top: 30px !important; }
@media (max-width: 768px) {
    .brand-name { font-size: 28px !important; letter-spacing: 5px !important; }
    .dir-buy, .dir-sell { font-size: 42px !important; }
    .conf-value { font-size: 38px !important; }
    .conf-box { padding: 22px 32px !important; }
    .pair-title { font-size: 20px !important; }
    .timer-value { font-size: 36px !important; }
    .triangle-buy, .triangle-sell { border-left-width: 32px !important; border-right-width: 32px !important; border-bottom-width: 48px !important; border-top-width: 48px !important; }
    .chip { min-width: 100px !important; padding: 10px 12px !important; }
    .mini-pair { font-size: 14px !important; }
}
</style>
""", unsafe_allow_html=True)

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

remaining = seconds_until_candle_end(interval)
total_sec = get_timeframe_seconds(interval)
progress = int(((total_sec - remaining) / total_sec) * 100)

st.markdown(f"""
<div class="timer-box">
    <div class="timer-label">⏱️ الوقت المتبقي لانتهاء الشمعة</div>
    <div class="timer-value">{remaining // 60:02d}:{remaining % 60:02d}</div>
    <div class="timer-bar"><div class="timer-bar-fill" style="width:{progress}%"></div></div>
</div>
""", unsafe_allow_html=True)

result = analyze(symbol, interval)

if result is None:
    st.markdown(f"""
    <div class="signal-card" style="border:1px solid rgba(255,255,255,0.06);">
        <div class="signal-title">SİNYAL HAZIR DEĞİL</div>
        <div class="pair-title">{pair_name}</div>
        <div style="color:#4a5568; font-size:18px; margin-top:25px;">
            لا توجد إشارة واضحة حالياً...
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    is_buy = result["direction"] == "BUY"
    cls_card = "signal-buy" if is_buy else "signal-sell"
    cls_tri  = "triangle-buy" if is_buy else "triangle-sell"
    cls_dir  = "dir-buy" if is_buy else "dir-sell"
    dir_text = "أعلى ⬆" if is_buy else "أسفل ⬇"
    dir_en   = "CALL / BUY" if is_buy else "PUT / SELL"

    if result["confidence"] >= ALERT_CONF:
        st.markdown(f"""
        <audio autoplay>
            <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
        </audio>
        <div style="background:rgba(0,212,255,0.15); border:1px solid rgba(0,212,255,0.5);
                    padding:14px; border-radius:14px; text-align:center;
                    color:#00d4ff; font-weight:700; margin-bottom:15px;
                    font-size:15px;">
            🔔 إشارة قوية! الثقة {result['confidence']}%
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="signal-card {cls_card}">
        <div class="signal-title">SİNYAL HAZIR</div>
        <div class="pair-title">{pair_name} · {tf_name}</div>
        <div class="{cls_tri}"></div>
        <div class="{cls_dir}">{dir_text}</div>
        <div style="color:#4a5568; font-size:12px; letter-spacing:5px;">{dir_en}</div>
        <div class="chips-row">
            <div class="chip">الزوج<b>{pair_name}</b></div>
            <div class="chip">الإطار<b>{tf_name}</b></div>
            <div class="chip">السعر<b>{result['price']:.5f}</b></div>
        </div>
        <div class="conf-box">
            <div class="conf-label">OLASILIK</div>
            <div class="conf-value">%{result['confidence']}</div>
        </div>
        <div style="color:#8a8a95; font-size:12px; margin-top:20px; line-height:2.2; text-align:right; padding:0 15px;">
            {'<br>'.join(result['reasons'][:5])}
        </div>
        <div style="margin-top:18px; padding:14px; background:rgba(0,212,255,0.06); 
                    border-radius:14px; border:1px solid rgba(0,212,255,0.2);">
            <div style="color:#00d4ff; font-size:11px; letter-spacing:4px;">جودة الإشارة</div>
            <div style="color:#fff; font-size:16px; font-weight:700; margin-top:6px;">
                {result['quality']}
            </div>
            <div style="color:#4a5568; font-size:11px; margin-top:8px;">
                RSI: {result['rsi']:.0f} • ATR: {result['atr']:.5f}
            </div>
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
    df_chart = result["df"].tail(80)
    res_level, sup_level = support_resistance(result["df"], 20)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df_chart.index, open=df_chart["Open"], high=df_chart["High"],
        low=df_chart["Low"], close=df_chart["Close"],
        increasing_line_color="#00ff88", decreasing_line_color="#ff2d55",
        name=pair_name))
    fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["EMA9"],
        line=dict(color="#00d4ff", width=1.8), name="EMA9"))
    fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart["EMA21"],
        line=dict(color="#8a2be2", width=1.8), name="EMA21"))
    fig.add_hline(y=res_level, line_dash="dash", line_color="#ff2d55",
                  annotation_text=f"مقاومة {res_level:.5f}", annotation_position="right")
    fig.add_hline(y=sup_level, line_dash="dash", line_color="#00ff88",
                  annotation_text=f"دعم {sup_level:.5f}", annotation_position="right")
    fig.update_layout(template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0a0a12",
        height=380, margin=dict(l=5, r=5, t=10, b=10),
        xaxis_rangeslider_visible=False,
        font=dict(family="Cairo", color="#ccc"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📉 مؤشر RSI")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df_chart.index, y=df_chart["RSI"],
        line=dict(color="#00d4ff", width=2), name="RSI"))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="#ff2d55")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="#00ff88")
    fig_rsi.update_layout(template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0a0a12",
        height=180, margin=dict(l=5, r=5, t=5, b=5),
        yaxis=dict(range=[0, 100]),
        font=dict(family="Cairo", color="#ccc"), showlegend=False)
    st.plotly_chart(fig_rsi, use_container_width=True)

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
            <span style="color:#4a5568;">{h['tf']}</span>
            <span style="color:{'#00ff88' if h['dir']=='BUY' else '#ff2d55'}; font-weight:700;">{dtxt}</span>
            <span style="color:#00d4ff; font-weight:700;">%{h['conf']}</span>
            <span style="color:#4a5568;">{h['time']}</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown(f"""
<div class="disclaimer">
    ⚠️ تحليل آلي وليس نصيحة استثمارية. التداول فيه مخاطرة.<br>
    {BRAND_NAME} © {datetime.now().year} — by فيصل
</div>
""", unsafe_allow_html=True)  
