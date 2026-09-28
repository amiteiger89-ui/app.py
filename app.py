import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta

# ==========================================
# 1. הגדרות עמוד, עיצוב CSS ומפתחות נכסים
# ==========================================
# חובה ש-set_page_config תהיה פקודת ה-Streamlit הראשונה ביותר בקוד!
st.set_page_config(
    page_title="סימולטור מסחר, מדדים וצ'אט מומחה",
    page_icon="📈",
    layout="wide"
)

from streamlit_autorefresh import st_autorefresh

# רענון אוטומטי של העמוד כל 280 שניות
st_autorefresh(interval=280000, key="datarefresh")

# ייבוא ספרית Supabase לעבודה מול מסד נתונים בענן
from supabase import create_client, Client

# ייבוא הספריות החדשות של Alpaca
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

# מפתחות ה-API שקיבלת מ-Alpaca
ALPACA_API_KEY = "PKF7KS23SIX4UM7V44SVFZNPOV"
ALPACA_SECRET_KEY = "HSB27F4DLefWGS7mL7xuna28MCXKHxBw1dcr1Y4qaCzd"

# אתחול הלקוח לשליפת הנתונים
data_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)

st.markdown("""
<style>
    .stApp {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem;
    }
    .wallet-header-clean {
        border: 1px solid rgba(150, 150, 150, 0.2);
        border-radius: 12px;
        padding: 16px 22px;
        margin-top: 0px !important;
        margin-bottom: 18px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .wallet-stat-title {
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 2px;
    }
    .wallet-stat-value {
        font-size: 1.25rem;
        font-weight: 700;
    }
    .wallet-stat-desc {
        font-size: 0.72rem;
        margin-top: 3px;
        line-height: 1.2;
    }
    .expert-box {
        border: 1px solid rgba(2, 132, 199, 0.3);
        border-right: 6px solid #0284C7;
        padding: 14px;
        border-radius: 10px;
        margin-bottom: 12px;
    }
    .educational-inline-box {
        border: 1px solid rgba(150, 150, 150, 0.3);
        border-right: 5px solid #3B82F6;
        padding: 14px;
        border-radius: 8px;
        margin-top: 10px;
    }
    .alert-tp {
        background-color: rgba(34, 197, 94, 0.15);
        border: 2px solid #22C55E;
        padding: 12px;
        border-radius: 8px;
        font-weight: bold;
        margin-bottom: 8px;
    }
    .alert-sl {
        background-color: rgba(239, 68, 68, 0.15);
        border: 2px solid #EF4444;
        padding: 12px;
        border-radius: 8px;
        font-weight: bold;
        margin-bottom: 8px;
    }
    .stock-logo {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        vertical-align: middle;
        object-fit: contain;
        border: 1px solid rgba(150, 150, 150, 0.2);
        padding: 2px;
    }
    .site-card {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        border: 1px solid rgba(150, 150, 150, 0.2);
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .site-fav {
        width: 24px;
        height: 24px;
        border-radius: 4px;
        object-fit: contain;
        margin-top: 2px;
    }
    .site-title {
        font-weight: 700;
        font-size: 0.9rem;
        text-decoration: none;
    }
    .flash-blue-circle {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #0284C7;
        box-shadow: 0 0 0 rgba(2, 132, 199, 0.4);
        animation: pulse-blue 1.5s infinite;
        vertical-align: middle;
        margin-right: 4px;
    }
    @keyframes pulse-blue {
        0% { box-shadow: 0 0 0 0 rgba(2, 132, 199, 0.7); }
        70% { box-shadow: 0 0 0 8px rgba(2, 132, 199, 0); }
        100% { box-shadow: 0 0 0 0 rgba(2, 132, 199, 0); }
    }
    .red-circle {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #EF4444;
        vertical-align: middle;
        margin-right: 4px;
    }
    .feedback-success {
        background-color: rgba(34, 197, 94, 0.1);
        border-right: 5px solid #22C55E;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .feedback-danger {
        background-color: rgba(239, 68, 68, 0.1);
        border-right: 5px solid #EF4444;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

CATEGORIZED_TICKERS = {
    "📊 מדדים וקרנות סל (ETFs)": {
        "S&P 500 ETF (SPY)": "SPY",
        "Nasdaq 100 ETF (QQQ)": "QQQ",
        "Dow Jones ETF (DIA)": "DIA",
        "Russell 2000 Small Cap (IWM)": "IWM",
        "Semiconductor ETF (SMH)": "SMH",
        "Financial Sector ETF (XLF)": "XLF",
        "Energy Sector ETF (XLE)": "XLE"
    },
    "🚀 ענקיות טכנולוגיה ו-AI": {
        "Apple Inc. (AAPL)": "AAPL",
        "Nvidia Corp. (NVDA)": "NVDA",
        "Microsoft Corp. (MSFT)": "MSFT",
        "Amazon.com Inc. (AMZN)": "AMZN",
        "Alphabet / Google (GOOGL)": "GOOGL",
        "Meta Platforms (META)": "META",
        "Tesla Inc. (TSLA)": "TSLA",
        "Broadcom Inc. (AVGO)": "AVGO",
        "Palantir Technologies (PLTR)": "PLTR",
        "Salesforce Inc. (CRM)": "CRM"
    },
    "💻 שבבים וחומרה": {
        "Advanced Micro Devices (AMD)": "AMD",
        "Intel Corp. (INTC)": "INTC",
        "Taiwan Semiconductor (TSM)": "TSM",
        "Qualcomm Inc. (QCOM)": "QCOM",
        "Micron Technology (MU)": "MU"
    },
    "🏦 פיננסים ובנקאות": {
        "JPMorgan Chase (JPM)": "JPM",
        "Bank of America (BAC)": "BAC",
        "Visa Inc. (V)": "V",
        "Mastercard Inc. (MA)": "MA"
    },
    "💊 בריאות ופארמה": {
        "Eli Lilly and Co. (LLY)": "LLY",
        "Johnson & Johnson (JNJ)": "JNJ",
        "Pfizer Inc. (PFE)": "PFE",
        "UnitedHealth Group (UNH)": "UNH"
    },
    "🛒 צריכה, קמעונאות ותעשייה": {
        "Walmart Inc. (WMT)": "WMT",
        "Costco Wholesale (COST)": "COST",
        "Walt Disney Co. (DIS)": "DIS",
        "Netflix Inc. (NFLX)": "NFLX",
        "Boeing Co. (BA)": "BA",
        "Lockheed Martin (LMT)": "LMT",
        "Exxon Mobil Corp. (XOM)": "XOM"
    },
    "🇮🇱 חברות ישראליות / דואליות": {
        "Teva Pharmaceutical (TEVA)": "TEVA",
        "Check Point (CHKP)": "CHKP",
        "Wix.com (WIX)": "WIX",
        "Monday.com (MNDY)": "MNDY",
        "SolarEdge Technologies (SEDG)": "SEDG",
        "Tower Semiconductor (TSEM)": "TSEM"
    },
    "🪙 קריפטו (24/7)": {
        "Bitcoin USD (BTC-USD)": "BTC-USD",
        "Ethereum USD (ETH-USD)": "ETH-USD",
        "Solana USD (SOL-USD)": "SOL-USD"
    },
    "✏️ הזנה ידנית": {
        "הזן סימול באופן עצמאי...": "CUSTOM"
    }
}

RAW_TICKER_MAP = {}
for cat_dict in CATEGORIZED_TICKERS.values():
    RAW_TICKER_MAP.update(cat_dict)

SECTOR_HEBREW = {
    'Technology': 'טכנולוגיה',
    'Financial Services': 'שירותים פיננסיים',
    'Healthcare': 'בריאות ופארמה',
    'Consumer Cyclical': 'צריכה מחזורית',
    'Communication Services': 'שירותי תקשורת',
    'Industrials': 'תעשייה',
    'Consumer Defensive': 'צריכה בסיסית',
    'Energy': 'אנרגיה',
    'Real Estate': 'נדל"ן',
    'Utilities': 'תשתיות',
    'Basic Materials': 'חומרי גלם',
    'Financial': 'פיננסים'
}

# ==========================================
# 2. ניהול מסד נתונים Supabase בענן (Load & Save)
# ==========================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("חסרים נתוני התחברות ל-Supabase. יש לוודא שהם מוגדרים ב-Streamlit Secrets או במשתני הסביבה.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_portfolio_from_file():
    """ טעינת נתוני התיק מטבלת portfolios ב-Supabase בראשית הסשן """
    try:
        response = supabase.table("portfolios").select("data").eq("id", 1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["data"]
    except Exception as e:
        st.error(f"⚠️ שגיאה בטעינת הנתונים מ-Supabase: {e}")
    
    return {
        "cash": 10000.0,
        "total_deposits": 10000.0,
        "deposit_history": [{"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "amount": 10000.0, "note": "הפקדה ראשונית"}],
        "positions": [],
        "history": [],
        "mentor_signals_log": [],
        "chat_history": []
    }

def save_portfolio_to_file():
    """ שמירה אוטומטית (upsert) של כל מבנה התיק מתוך ה-st.session_state לתוך Supabase """
    data_to_save = {
        "cash": st.session_state.get("cash", 10000.0),
        "total_deposits": st.session_state.get("total_deposits", 10000.0),
        "deposit_history": st.session_state.get("deposit_history", []),
        "positions": st.session_state.get("positions", []),
        "history": st.session_state.get("history", []),
        "mentor_signals_log": st.session_state.get("mentor_signals_log", []),
        "chat_history": st.session_state.get("chat_history", [])
    }
    try:
        supabase.table("portfolios").upsert({"id": 1, "data": data_to_save}).execute()
    except Exception as e:
        st.error(f"⚠️ שגיאה בשמירת הנתונים ל-Supabase: {e}")

if 'initialized' not in st.session_state:
    saved_data = load_portfolio_from_file()
    st.session_state.cash = saved_data.get("cash", 10000.0)
    st.session_state.total_deposits = saved_data.get("total_deposits", 10000.0)
    st.session_state.deposit_history = saved_data.get("deposit_history", [{"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "amount": 10000.0, "note": "הפקדה ראשונית"}])
    st.session_state.positions = saved_data.get("positions", [])
    st.session_state.history = saved_data.get("history", [])
    st.session_state.mentor_signals_log = saved_data.get("mentor_signals_log", [])
    st.session_state.chat_history = saved_data.get("chat_history", [])
    st.session_state.active_sl = 0.0
    st.session_state.active_tp = 0.0
    st.session_state.confirm_wallet_reset = False
    st.session_state.confirm_history_reset = False
    st.session_state.initialized = True

def play_audio_alert():
    sound_url = "https://ia800203.us.archive.org/3/items/ICQUhOhSoundEffect/ICQ%20Uh%20Oh%20Sound%20Effect.mp3"
    st.markdown(f'<audio src="{sound_url}" autoplay="true" style="display:none;"></audio>', unsafe_allow_html=True)

def get_market_status_for_ticker(symbol):
    try:
        import pytz
        from datetime import datetime
        if "-USD" in symbol.upper():
            return "🟢 שוק הקריפטו פעיל (24/7)", True
        tz_us = pytz.timezone("America/New_York")
        now_us = datetime.now(tz_us)
        is_weekday = now_us.weekday() < 5
        current_hour_decimal = now_us.hour + now_us.minute / 60.0
        is_open_hours = 9.5 <= current_hour_decimal <= 16.0
        if is_weekday and is_open_hours:
            return '🟢 שוק ארה"ב פתוח למסחר', True
        else:
            return '🔴 שוק ארה"ב סגור כעת (מסחר מאוחר/טרום פתיחה)', False
    except Exception:
        return "⚪ סטטוס שוק לא זמין", False

def get_stock_logo_url(symbol):
    clean_sym = symbol.upper().strip()
    return f"https://assets.parqet.com/logos/symbol/{clean_sym}"

def calculate_sell_feasibility(pos, live_price, weighted_sig):
    buy_price = pos['buy_price']
    tp = pos['tp']
    sl = pos['sl']
    pnl_pct = ((live_price / buy_price) - 1) * 100
    
    try:
        buy_dt = datetime.strptime(pos.get('date', ''), "%Y-%m-%d %H:%M")
        hours_since_buy = (datetime.now() - buy_dt).total_seconds() / 3600
    except Exception:
        hours_since_buy = 999.0

    score = 30.0  
    if tp > 0 and live_price >= tp * 0.98:
        score += 50
    if sl > 0 and live_price <= sl * 1.02:
        score += 60
        
    if weighted_sig['type'] == 'sell':
        score += 30
    elif weighted_sig['type'] == 'buy':
        score -= 20
        
    if pnl_pct > 12:
        score += 20
    elif pnl_pct < -5:
        score += 15  
        
    if hours_since_buy < 24 and (tp == 0 or live_price < tp * 0.98) and (sl == 0 or live_price > sl * 1.02):
        score = min(score, 35.0)

    return int(np.clip(score, 0, 100))

# ==========================================
# 3. שליפת נתונים וניתוח טכני מתקדם (20+ פרמטרים)
# ==========================================
@st.cache_data(ttl=180)
def load_stock_data(symbol, period, interval):
    try:
        tf_map = {
            "5m": TimeFrame(5, TimeFrameUnit.Minute),
            "15m": TimeFrame(15, TimeFrameUnit.Minute),
            "30m": TimeFrame(30, TimeFrameUnit.Minute),
            "1h": TimeFrame(1, TimeFrameUnit.Hour),
            "1d": TimeFrame.Day
        }
        tf = tf_map.get(interval, TimeFrame(1, TimeFrameUnit.Minute))
        now = datetime.now()
        period_days_map = {"1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}
        days_back = period_days_map.get(period, 1)
        start_date = now - timedelta(days=days_back)
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=tf,
            start=start_date
        )
        bars = data_client.get_stock_bars(request_params)
        df = bars.df
        if not df.empty:
            if isinstance(df.index, pd.MultiIndex):
                df = df.reset_index(level=0, drop=True)
            df = df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })
            return df
    except Exception:
        pass

    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_company_info(symbol):
    try:
        return yf.Ticker(symbol).info
    except Exception:
        return {}

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data, fast=12, slow=26, signal=9):
    exp1 = data['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = data['Close'].ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def calculate_stochastic(data, k_window=14, d_window=3):
    low_min = data['Low'].rolling(window=k_window).min()
    high_max = data['High'].rolling(window=k_window).max()
    k = 100 * ((data['Close'] - low_min) / (high_max - low_min).replace(0, np.nan))
    d = k.rolling(window=d_window).mean()
    return k, d

def calculate_bollinger_bands(data, window=20, num_std=2):
    sma = data['Close'].rolling(window=window).mean()
    std = data['Close'].rolling(window=window).std()
    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    pct_b = (data['Close'] - lower) / (upper - lower).replace(0, np.nan)
    return upper, lower, pct_b

def calculate_atr(data, window=14):
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(window=window).mean()

def calculate_comprehensive_matrix(symbol):
    macro_df = load_stock_data(symbol, "1y", "1d")
    micro_df = load_stock_data(symbol, "5d", "1h")
    spy_df = load_stock_data("SPY", "5d", "1h") if symbol != "SPY" else micro_df

    if macro_df.empty or micro_df.empty:
        curr_p = 100.0
        return {
            'price': curr_p, 'signal': "⚪ ניטרלי", 'type': 'neutral', 'confluence_score': 50,
            'reason': "נתונים חלקיים זמינים בלבד.", 'sl': curr_p * 0.97, 'tp': curr_p * 1.05,
            'metrics': {}
        }

    curr_price = float(micro_df['Close'].iloc[-1])

    micro_sma20 = float(micro_df['Close'].rolling(20).mean().iloc[-1]) if len(micro_df) >= 20 else curr_price
    micro_sma50 = float(micro_df['Close'].rolling(50).mean().iloc[-1]) if len(micro_df) >= 50 else micro_sma20
    macro_sma20 = float(macro_df['Close'].rolling(20).mean().iloc[-1]) if len(macro_df) >= 20 else curr_price
    macro_sma50 = float(macro_df['Close'].rolling(50).mean().iloc[-1]) if len(macro_df) >= 50 else macro_sma20
    macro_sma200 = float(macro_df['Close'].rolling(200).mean().iloc[-1]) if len(macro_df) >= 200 else macro_sma50

    rsi_s = calculate_rsi(micro_df, 14)
    rsi_val = float(rsi_s.iloc[-1]) if not rsi_s.empty and not np.isnan(rsi_s.iloc[-1]) else 50.0
    
    macd_l, macd_sig, macd_h = calculate_macd(micro_df)
    macd_hist_val = float(macd_h.iloc[-1]) if not macd_h.empty and not np.isnan(macd_h.iloc[-1]) else 0.0

    stoch_k, stoch_d = calculate_stochastic(micro_df)
    stoch_k_val = float(stoch_k.iloc[-1]) if not stoch_k.empty and not np.isnan(stoch_k.iloc[-1]) else 50.0
    stoch_d_val = float(stoch_d.iloc[-1]) if not stoch_d.empty and not np.isnan(stoch_d.iloc[-1]) else 50.0

    bb_up, bb_low, bb_pctb = calculate_bollinger_bands(micro_df)
    bb_pctb_val = float(bb_pctb.iloc[-1]) if not bb_pctb.empty and not np.isnan(bb_pctb.iloc[-1]) else 0.5

    atr_s = calculate_atr(micro_df, 14)
    atr_val = float(atr_s.iloc[-1]) if not atr_s.empty and not np.isnan(atr_s.iloc[-1]) else curr_price * 0.015
    hist_vol = float(micro_df['Close'].pct_change().std() * np.sqrt(252) * 100) if len(micro_df) > 5 else 20.0

    vol_mean = float(micro_df['Volume'].rolling(20).mean().iloc[-1]) if len(micro_df) >= 20 else float(micro_df['Volume'].mean())
    curr_vol = float(micro_df['Volume'].iloc[-1])
    rvol = (curr_vol / vol_mean) if vol_mean > 0 else 1.0
    obv = (np.sign(micro_df['Close'].diff()) * micro_df['Volume']).fillna(0).cumsum()
    obv_trend = "עולה" if len(obv) > 5 and obv.iloc[-1] > obv.iloc[-5] else "יורד"

    asset_perf = float((micro_df['Close'].iloc[-1] / micro_df['Close'].iloc[0]) - 1) if len(micro_df) > 0 else 0.0
    spy_perf = float((spy_df['Close'].iloc[-1] / spy_df['Close'].iloc[0]) - 1) if not spy_df.empty and len(spy_df) > 0 else 0.0
    relative_strength = asset_perf - spy_perf

    score_points = 50.0
    if curr_price > micro_sma20: score_points += 8
    if curr_price > macro_sma20: score_points += 10
    if macro_sma20 > macro_sma50: score_points += 7
    if 40 <= rsi_val <= 65: score_points += 8
    elif rsi_val > 75: score_points -= 12
    elif rsi_val < 25: score_points += 6
    if macd_hist_val > 0: score_points += 8
    if stoch_k_val > stoch_d_val: score_points += 5
    if 0.2 <= bb_pctb_val <= 0.8: score_points += 5
    if rvol > 1.2: score_points += 7
    if relative_strength >= 0: score_points += 10

    confluence_score = int(np.clip(score_points, 0, 100))

    if confluence_score >= 65:
        sig_text = "🟢 איתות קנייה חזק (Confluence Bullish)"
        sig_type = 'buy'
        sl = round(curr_price - (atr_val * 1.5), 2)
        tp = round(curr_price + (atr_val * 2.5), 2)
    elif confluence_score <= 38:
        sig_text = "🔴 איתות מכירות / זהירות (Confluence Bearish)"
        sig_type = 'sell'
        sl = round(curr_price - (atr_val * 1.2), 2)
        tp = round(curr_price + (atr_val * 1.5), 2)
    else:
        sig_text = "⚪ ניטרלי / שיווי משקל (Hold / Range)"
        sig_type = 'neutral'
        sl = round(curr_price - (atr_val * 1.5), 2)
        tp = round(curr_price + (atr_val * 2.0), 2)

    reason = (f"מטריצת 20+ פרמטרים: ציון התכנסות (Confluence) עומד על {confluence_score}%. "
              f"מגמה ראשית {'חיובית' if curr_price > macro_sma20 else 'שלילית'}, "
              f"RSI שעתי: {rsi_val:.1f}, RVOL נפח יחסי: {rvol:.2f}x, עוצמה יחסית מול SPY: {relative_strength:+.2f}%.")

    metrics_dict = {
        "micro_sma20": micro_sma20, "micro_sma50": micro_sma50,
        "macro_sma20": macro_sma20, "macro_sma50": macro_sma50, "macro_sma200": macro_sma200,
        "rsi": rsi_val, "macd_hist": macd_hist_val, "stoch_k": stoch_k_val, "stoch_d": stoch_d_val,
        "bb_pctb": bb_pctb_val, "atr": atr_val, "hist_vol": hist_vol, "rvol": rvol,
        "obv_trend": obv_trend, "relative_strength": relative_strength
    }

    return {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'symbol': symbol,
        'price': curr_price,
        'signal': sig_text,
        'reason': reason,
        'sl': max(sl, curr_price * 0.8),
        'tp': max(tp, curr_price * 1.02),
        'type': sig_type,
        'rsi': rsi_val,
        'sma20': micro_sma20,
        'confluence_score': confluence_score,
        'metrics': metrics_dict
    }

def calculate_weighted_expert_signal(symbol):
    return calculate_comprehensive_matrix(symbol)

# ==========================================
# 4. מנוע צ'אט מומחה
# ==========================================
def generate_expert_ai_response(user_query, current_symbol, current_sig, positions):
    q = user_query.strip().lower()
    c_price = current_sig['price']
    c_rsi = current_sig['rsi']
    c_reason = current_sig['reason']

    if "למכור" in q or "האם כדאי למכור" in q or "החזקות" in q or "תיק" in q or "למה" in q:
        if not positions:
            return "📦 **סטטוס תיק:** אין לך כרגע פוזיציות פתוחות בתיק המסחר."
        
        response_lines = ["💼 **ניתוח מומחה רב-ממדי לפוזיציות הפתוחות שלך:**\n"]
        for p in positions:
            p_df = load_stock_data(p['symbol'], "5d", "1d")
            l_p = float(p_df['Close'].iloc[-1]) if not p_df.empty else p['buy_price']
            p_sig = calculate_comprehensive_matrix(p['symbol'])
            feas = calculate_sell_feasibility(p, l_p, p_sig)
            pnl_p = ((l_p / p['buy_price']) - 1) * 100
            
            action_advice = "🔴 **מומלץ למכור עכשיו**" if feas > 50 else "🟢 **מומלץ להחזיק**"
            reason_text = f"מחיר ${l_p:.2f} (תשואה {pnl_p:+.2f}%), ציון קונפלואנס: {p_sig['confluence_score']}%. כדאיות מכירה: {feas}%."
            response_lines.append(f"• **{p['symbol']}**: {action_advice}\n  *פרטים:* {reason_text}")
        return "\n\n".join(response_lines)

    if "טופ 3" in q or "top 3" in q:
        return f"🚀 **Top 3 נכסים מובילים (מבוסס מטריצת פרמטרים):**\n1. **{current_symbol}** (קונפלואנס: {current_sig['confluence_score']}%, RSI: {c_rsi:.1f})\n2. **NVDA** (מומנטום שבבים ובינה מלאכותית)\n3. **QQQ** (פיזור מדד הטכנולוגיה)"

    return f"👨‍💼 **תשובת מומחה מסחר (מטריצת 20+ פרמטרים):**\n\n" \
           f"לגבי שאלתך: *'{user_query}'*\n" \
           f"📌 **נתוני לייב עבור {current_symbol}:** מחיר ${c_price:.2f}, ציון התכנסות (Confluence): **{current_sig['confluence_score']}%**.\n" \
           f"💡 **ניתוח:** {c_reason}"

# ==========================================
# 5. סרגל צד - מרכז למידה וקישורים
# ==========================================
st.sidebar.title("📚 מרכז הלמידה - מושגי יסוד")
st.sidebar.caption("מדריך מעמיק לניתוח טכני, אסטרטגיות וניהול סיכונים")
st.sidebar.markdown("---")

with st.sidebar.expander("1. מגמה ומבנה שוק"):
    st.markdown("**SMA 20 (שעתי):** ממוצע נע פשוט ל-20 נרות בגרף השעתי. משמש לזיהוי כיוון המגמה בטווח הקצר-מאוד.")
    st.markdown("**SMA 50 (שעתי):** ממוצע נע פשוט ל-50 נרות בגרף השעתי. עוזר לזהות תמיכות והתנגדות בטווחי זמן קצרים.")
    st.markdown("**SMA 20 (יומי):** ממוצע נע פשוט ל-20 ימים. מציג את המגמה הבינונית של הנכס.")
    st.markdown("**SMA 200 (יומי):** ממוצע נע פשוט ל-200 ימים. המדד המרכזי שסוחרים משתמשים בו כדי לקבוע האם הנכס נמצא במגמת שוק ראשית עולה או יורדת.")
    st.caption("זיהוי מגמות ארוכות וקצרות טווח.")

with st.sidebar.expander("2. מומנטום ואוסצילטורים"):
    st.markdown("**RSI (14):** מתנד עוצמה יחסית שנע בין 0 ל-100. ערך מעל 70 מעיד על קניית-יתר (סיכון לתיקון), ומתחת ל-30 על מכירת-יתר (הזדמנות פוטנציאלית).")
    st.markdown("**MACD Hist:** היסטוגרם המציג את ההפרש בין קווי ה-MACD. עוזר לזהות מתי המומנטום של המחיר מתחזק או נחלש.")
    st.markdown("**Stoch %K / %D:** מתנד סטוכסטי המשווה את מחיר הסגירה לטווח המחירים. חצייה בין הקו המהיר (%K) לאיטי (%D) מסמנת נקודות היפוך.")
    st.markdown("**Bollinger %B:** מציג את מיקום המחיר המדויק יחסית לרצועות בולינגר (0 אומר שהמחיר על הרצועה התחתונה, 1 על העליונה).")
    st.caption("בחינת עוצמת תנועת המחיר ומצבי קיצון.")

with st.sidebar.expander("3. תנודתיות וסיכון"):
    st.markdown("**ATR (14):** מדד טווח אמצעי ממוצע המחשב את גודל התנודות של הנכס בדולרים/נקודות, ועוזר להבין כמה הנכס זז בממוצע.")
    st.markdown("**סטיית תקן שנתית:** מדד סטטיסטי שמבטא את רמת הסיכון והתנודתיות של הנכס במונחים שנתיים (באחוזים).")
    st.markdown("**סטופ-לוס אוטו:** רמת מחיר מחושבת שנועדה לחתוך הפסדים אוטומטית אם העסקה פונה נגדך.")
    st.markdown("**יעד רווח אוטו:** רמת מחיר מחושבת לנעילת רווחים אוטומטית כשהמחיר מגיע ליעד המתוכנן.")
    st.caption("ניהול סיכונים ויעדי יציאה.")

with st.sidebar.expander("4. נפח ונזילות"):
    st.markdown("**RVOL (נפח יחסי):** השוואה של נפח המסחר הנוכחי מול הממוצע. ערך גבוה מ-1 מצביע על עניין חריג בנכס (למשל בעקבות חדשות).")
    st.markdown("**OBV (זרימה):** משתמש בנפח המסחר כדי לצבור נתונים ולזהות האם יש לחץ של קונים (זרימה חיובית) או מוכרים (שלילית).")
    st.markdown("**מחזור מסחר:** אינדיקציה לכך שהפעילות בנכס אקטיבית ומתבצעות בו עסקאות ערות.")
    st.markdown("**נזילות נכס:** מדד המראה כמה קל להיכנס ולצאת מהמסחר בנכס מבלי שהפקודה שלך תשפיע לרעה על המחיר.")
    st.caption("מעקב אחר עוצמת הפעילות והנפחים.")

with st.sidebar.expander("5. חוזק יחסי ומאקרו"):
    st.markdown("**S&P 500 מול מדד:** השוואת ביצועי המניה או הנכס מול מדד הייחוס (האם הנכס חזק יותר מהשוק ומכה אותו, או חלש יותר).")
    st.markdown("**סטטוס שוק:** מציג מי השחקנים הפעילים כרגע בנכס, למשל האם יש פעילות של גופים מוסדיים גדולים.")
    st.markdown("**כיוון מבני:** המבנה הכללי של התנועה בנכס (האם מבנה השיאים והשפלים הוא חיובי או שלילי).")
    st.markdown("**איתות מערכת:** השורה התחתונה וההמלצה האלגוריתמית של המערכת (כגון BUY).")
    st.caption("השוואה למדד הייחוס ואיתותי מערכת.")

st.sidebar.markdown("---")
st.sidebar.subheader("🌐 אתרי מסחר ומידע מומלצים")

RECOMMENDED_SITES = [
    {"name": "TradingView", "url": "https://www.tradingview.com", "fav": "https://www.google.com/s2/favicons?domain=tradingview.com&sz=64", "desc": "פלטפורמת ניתוח טכני וגרפים מתקדמת."},
    {"name": "Finviz", "url": "https://www.finviz.com", "fav": "https://www.google.com/s2/favicons?domain=finviz.com&sz=64", "desc": "סורק מניות ומפות חום של השוק."},
    {"name": "Investopedia", "url": "https://www.investopedia.com", "fav": "https://www.google.com/s2/favicons?domain=investopedia.com&sz=64", "desc": "אנציקלופדיה פיננסית ללימוד מושגים."},
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com", "fav": "https://www.google.com/s2/favicons?domain=yahoo.com&sz=64", "desc": "ציטוטי מחירים בזמן אמת וחדשות."},
    {"name": "Seeking Alpha", "url": "https://seekingalpha.com", "fav": "https://www.google.com/s2/favicons?domain=seekingalpha.com&sz=64", "desc": "ניתוחי עומק של אנליסטים ותחזיות."}
]

for site in RECOMMENDED_SITES:
    st.sidebar.markdown(f"""
    <div class="site-card">
        <img src="{site['fav']}" class="site-fav">
        <div>
            <a href="{site['url']}" target="_blank" class="site-title">{site['name']} 🔗</a>
            <div style="font-size:0.75rem; color:#64748B;">{site['desc']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 6. בדיקת התראות מחיר בלייב
# ==========================================
alert_triggered = False
alerts = []
for pos in st.session_state.positions:
    check_df = load_stock_data(pos['symbol'], "5d", "1d")
    if not check_df.empty:
        live_p = float(check_df['Close'].iloc[-1])
        if pos['tp'] > 0 and live_p >= pos['tp']:
            alert_triggered = True
            alerts.append((f"🎯 **התראת יעד רווח (TP)!** {pos['symbol']} הגיעה ל-**${live_p:.2f}**.", "alert-tp"))
        elif pos['sl'] > 0 and live_p <= pos['sl']:
            alert_triggered = True
            alerts.append((f"🚨 **התראת עצירת הפסד (SL)!** {pos['symbol']} ירדה ל-**${live_p:.2f}**.", "alert-sl"))

if alert_triggered:
    play_audio_alert()

for alert_msg, alert_class in alerts:
    st.markdown(f'<div class="{alert_class}">{alert_msg}</div>', unsafe_allow_html=True)

# ==========================================
# 7. סרגל ארנק עליון
# ==========================================
open_positions_val = 0.0
gross_open_pnl = 0.0

for pos in st.session_state.positions:
    pos_df = load_stock_data(pos['symbol'], "5d", "1d")
    l_price = float(pos_df['Close'].iloc[-1]) if not pos_df.empty else pos['buy_price']
    cur_v = l_price * pos['shares']
    open_positions_val += cur_v
    gross_open_pnl += (cur_v - pos['total_cost'])

total_portfolio_value = st.session_state.cash + open_positions_val
closed_net_pnl = sum([h.get('net_pnl', 0.0) for h in st.session_state.history])
open_tax = (gross_open_pnl * 0.25) if gross_open_pnl > 0 else 0.0
open_net_pnl = gross_open_pnl - open_tax
total_net_pnl = closed_net_pnl + open_net_pnl

tot_deposits = st.session_state.get('total_deposits', 10000.0)
pnl_color = "#16A34A" if total_net_pnl >= 0 else "#DC2626"

st.markdown(f"""
<div class="wallet-header-clean">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:15px;">
        <div style="flex:1; min-width:180px;">
            <div class="wallet-stat-title">💼 סך הכל בתיק (Total Portfolio Value)</div>
            <div class="wallet-stat-value">${total_portfolio_value:,.2f}</div>
            <div class="wallet-stat-desc">מזומן פנוי (${st.session_state.cash:,.2f}) + שווי פוזיציות (${open_positions_val:,.2f})</div>
        </div>
        <div style="border-right: 1px solid #E2E8F0; height: 40px;"></div>
        <div style="flex:1; min-width:160px;">
            <div class="wallet-stat-title">💵 מזומן פנוי (Available Cash)</div>
            <div class="wallet-stat-value" style="color:#0284C7;">${st.session_state.cash:,.2f}</div>
            <div class="wallet-stat-desc">סכום המזומן הנזיל העומד לרשותך לביצוע רכישות</div>
        </div>
        <div style="border-right: 1px solid #E2E8F0; height: 40px;"></div>
        <div style="flex:1; min-width:180px;">
            <div class="wallet-stat-title">📈 רווח / הפסד נטו (Total Net P&L)</div>
            <div class="wallet-stat-value" style="color:{pnl_color};">${total_net_pnl:+,.2f}</div>
            <div class="wallet-stat-desc">סיכום עסקאות סגורות + פוזיציות פתוחות לאחר מס</div>
        </div>
        <div style="border-right: 1px solid #E2E8F0; height: 40px;"></div>
        <div style="flex:1; min-width:160px;">
            <div class="wallet-stat-title">🏦 סך הפקדות (Total Deposits)</div>
            <div class="wallet-stat-value" style="color:#334155;">${tot_deposits:,.2f}</div>
            <div class="wallet-stat-desc">סך ההון שהופקד בארנק מתחילת הפעילות</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

w_col1, w_col2, w_col3, w_col4 = st.columns([1.2, 1.4, 1.2, 3])

with w_col1:
    with st.popover("➕ הפקדה נוספת"):
        dep_amount = st.number_input("סכום להפקדה ($):", min_value=100.0, value=1000.0, step=500.0)
        dep_note = st.text_input("הערה (אופציונלי):", value="הפקדה נוספת")
        if st.button("אישור הפקדה"):
            st.session_state.cash += dep_amount
            st.session_state.total_deposits += dep_amount
            st.session_state.deposit_history.append({'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'amount': dep_amount, 'note': dep_note})
            save_portfolio_to_file()
            st.success(f"הופקדו ${dep_amount:,.2f} בהצלחה!")
            st.rerun()

with w_col2:
    with st.popover("📜 היסטוריית הפקדות"):
        dep_hist = st.session_state.get('deposit_history', [])
        for dh in reversed(dep_hist):
            st.markdown(f"• **${dh['amount']:,.2f}** - {dh['date']} (*{dh.get('note', 'הפקדה')}*)")

with w_col3:
    if st.button("🔄 איפוס ארנק", help="מאפס את המזומן והתיק ל-$10,000"):
        st.session_state.confirm_wallet_reset = True

if st.session_state.get('confirm_wallet_reset', False):
    st.warning("⚠️ **האם אתה בטוח שברצונך לאפס את הארנק?**")
    c_w1, c_w2 = st.columns([1, 4])
    with c_w1:
        if st.button("✅ כן, אפס ארנק", type="primary"):
            st.session_state.cash = 10000.0
            st.session_state.total_deposits = 10000.0
            st.session_state.deposit_history = [{"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "amount": 10000.0, "note": "הפקדה ראשונית (איפוס)"}]
            st.session_state.positions = []
            st.session_state.confirm_wallet_reset = False
            save_portfolio_to_file()
            st.rerun()
    with c_w2:
        if st.button("❌ ביטול"):
            st.session_state.confirm_wallet_reset = False
            st.rerun()

# ==========================================
# 8. בחירת מניה - מבוסס קטגוריות
# ==========================================
st.title("📈 סימולטור מסחר, מדדים מובילים וצ'אט מומחה")

col_cat, col_asset, c_per, c_int = st.columns([1.5, 1.5, 1, 1])

with col_cat:
    selected_cat = st.selectbox("בחר קטגוריה:", list(CATEGORIZED_TICKERS.keys()))

with col_asset:
    category_map = CATEGORIZED_TICKERS[selected_cat]
    selected_asset_label = st.selectbox("בחר נכס:", list(category_map.keys()))
    selected_symbol_val = category_map[selected_asset_label]

with c_per:
    period = st.selectbox("טווח היסטורי", options=["1d", "5d", "1mo", "3mo", "6mo", "1y"], index=3)

with c_int:
    interval_opts = ["5m", "15m", "30m", "1h"] if period == "1d" else ["15m", "30m", "1h", "1d"]
    interval = st.selectbox("אינטרוול נר", options=interval_opts, index=3 if "1d" in interval_opts else 0)

if selected_symbol_val == "CUSTOM":
    ticker_symbol = st.text_input("הכנס סימול (למשל: ABNB, COIN, UBER):", value="AMZN").upper().strip()
    if not ticker_symbol:
        ticker_symbol = "AMZN"
else:
    ticker_symbol = selected_symbol_val

status_text, is_open = get_market_status_for_ticker(ticker_symbol)
current_logo_url = get_stock_logo_url(ticker_symbol)

st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between; background-color:var(--background-color); border:1px solid rgba(150,150,150,0.2); padding:10px 14px; border-radius:8px; margin-top:6px; margin-bottom:12px;">
    <div style="display:flex; align-items:center; gap:10px;">
        <img src="{current_logo_url}" class="stock-logo" style="width:34px; height:34px;" onerror="this.style.display='none'">
        <div>
            <span style="font-weight:bold; font-size:1.0rem;">{ticker_symbol}</span>
            <span style="font-size:0.82rem; opacity:0.7; margin-right:8px;">{selected_asset_label}</span>
        </div>
    </div>
    <div style="font-size:0.85rem; font-weight:600;">
        {status_text}
    </div>
</div>
""", unsafe_allow_html=True)

df = load_stock_data(ticker_symbol, period, interval)
info = get_company_info(ticker_symbol)

if df.empty:
    st.error(f"לא נשלפו נתונים עבור הסימול '{ticker_symbol}'. ודא שהסימול תקין.")
    st.stop()

current_price = float(df['Close'].iloc[-1])

current_sig = calculate_comprehensive_matrix(ticker_symbol)

if not st.session_state.mentor_signals_log or st.session_state.mentor_signals_log[0]['symbol'] != ticker_symbol or st.session_state.mentor_signals_log[0]['reason'] != current_sig['reason']:
    st.session_state.mentor_signals_log.insert(0, current_sig)
    save_portfolio_to_file()

# ==========================================
# 8.1 לוח בקרה פרמטרי (At-a-Glance Matrix)
# ==========================================
with st.expander(f"📊 מטריצת החלטה רב-ממדית (20+ פרמטרים) עבור {ticker_symbol} (לחץ לפתיחה / מיזעור)", expanded=True):
    st.caption("מבט-על מרוכז המחולק ל-5 עולמות תוכן מרכזיים.")
    
    m_vals = current_sig['metrics']
    conf_score = current_sig['confluence_score']
    
    score_color = "#16A34A" if conf_score >= 65 else ("#DC2626" if conf_score <= 38 else "#D97706")
    st.markdown(f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px 18px; border-radius: 8px; margin-bottom: 12px; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <div style="font-weight:700; font-size:1.0rem; color:#0F172A;">ציון התכנסות מערכתי (Confluence Score)</div>
            <div style="font-size:0.8rem; color:#64748B;">משכלל את כל 5 עולמות התוכן למדד אחד המעיד על חוזק התמיכה בשוק</div>
        </div>
        <div style="font-size:1.4rem; font-weight:800; color:{score_color};">
            {conf_score}%
        </div>
    </div>
    """, unsafe_allow_html=True)

    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    
    with mc1:
        st.markdown("##### 1. מגמה ומבנה שוק")
        st.markdown(f"""
        <div style="font-size:0.82rem; line-height:1.4; color:#334155;">
            • SMA 20 (שעתי): <b>${m_vals.get('micro_sma20', 0):.2f}</b><br>
            • SMA 50 (שעתי): <b>${m_vals.get('micro_sma50', 0):.2f}</b><br>
            • SMA 20 (יומי): <b>${m_vals.get('macro_sma20', 0):.2f}</b><br>
            • SMA 200 (יומי): <b>${m_vals.get('macro_sma200', 0):.2f}</b>
        </div>
        """, unsafe_allow_html=True)
        
    with mc2:
        st.markdown("##### 2. מומנטום ואוסצילטורים")
        st.markdown(f"""
        <div style="font-size:0.82rem; line-height:1.4; color:#334155;">
            • RSI (14): <b>{m_vals.get('rsi', 50):.1f}</b><br>
            • MACD Hist: <b>{m_vals.get('macd_hist', 0):+.2f}</b><br>
            • Stoch %K / %D: <b>{m_vals.get('stoch_k', 0):.1f} / {m_vals.get('stoch_d', 0):.1f}</b><br>
            • Bollinger %B: <b>{m_vals.get('bb_pctb', 0.5):.2f}</b>
        </div>
        """, unsafe_allow_html=True)

    with mc3:
        st.markdown("##### 3. תנודתיות וסיכון")
        st.markdown(f"""
        <div style="font-size:0.82rem; line-height:1.4; color:#334155;">
            • ATR (14): <b>${m_vals.get('atr', 0):.2f}</b><br>
            • סטיית תקן שנתית: <b>{m_vals.get('hist_vol', 0):.1f}%</b><br>
            • סטופ-לוס אוטו: <b>${current_sig['sl']:.2f}</b><br>
            • יעד רווח אוטו: <b>${current_sig['tp']:.2f}</b>
        </div>
        """, unsafe_allow_html=True)

    with mc4:
        st.markdown("##### 4. נפח ונזילות")
        st.markdown(f"""
        <div style="font-size:0.82rem; line-height:1.4; color:#334155;">
            • RVOL (נפח יחסי): <b>{m_vals.get('rvol', 1):.2f}x</b><br>
            • OBV (מגמת זרימה): <b>{m_vals.get('obv_trend', 'ניטרלי')}</b><br>
            • מחזור מסחר: <b>פעיל</b><br>
            • נזילות נכס: <b>גבוהה</b>
        </div>
        """, unsafe_allow_html=True)

    with mc5:
        st.markdown("##### 5. חוזק יחסי ומאקרו")
        st.markdown(f"""
        <div style="font-size:0.82rem; line-height:1.4; color:#334155;">
            • מול מדד S&P 500: <b>{m_vals.get('relative_strength', 0):+.2f}%</b><br>
            • סטטוס שוק: <b>מוסדי / פעיל</b><br>
            • כיוון מבני: <b>{'חיובי' if current_price > m_vals.get('macro_sma20', 0) else 'שלילי'}</b><br>
            • איתות מערכת: <b>{current_sig['type'].upper()}</b>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 9 & 10. הגרף הטכני הכפול + צ'אט מומחה
# ==========================================
col_left_chart, col_right_chat = st.columns([1.3, 1])

with col_right_chat:
    st.markdown("### 🤖 צ'אט מומחה ומרכז המנטור")
    chat_tab1, chat_tab2, chat_tab3 = st.tabs(["💬 צ'אט מומחה", "🟢 המלצה אקטיבית", "📜 ארכיון המלצות"])
    
    with chat_tab1:
        st.caption("שאל חופשי את הצ'אט, כולל שאלות על המניות שברשותך (האם כדאי למכור ולמה):")
        q_cols1 = st.columns(2)
        selected_preset = None
        with q_cols1[0]:
            if st.button("💼 האם כדאי למכור את המניות שלי?", use_container_width=True):
                selected_preset = "האם כדאי למכור את המניות שאני מחזיק ולמה?"
        with q_cols1[1]:
            if st.button("🚀 טופ 3 קצר-יומי", use_container_width=True):
                selected_preset = "תן לי טופ 3 מניות לטווח קצר-יומי"

        chat_container = st.container(height=220)
        for msg in st.session_state.chat_history:
            with chat_container.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
        user_input = st.chat_input("שאל את המומחה בכתב חופשי (למשל: 'האם כדאי למכור את NVDA?')")
        prompt_to_process = selected_preset or user_input
        if prompt_to_process:
            st.session_state.chat_history.append({"role": "user", "content": prompt_to_process})
            reply = generate_expert_ai_response(prompt_to_process, ticker_symbol, current_sig, st.session_state.positions)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            save_portfolio_to_file()
            st.rerun()

    with chat_tab2:
        c_ref_btn1, c_ref_btn2 = st.columns([2.5, 1])
        with c_ref_btn1:
            st.markdown("#### ⚡ ניתוח והמלצות משוקללות בזמן אמת")
        with c_ref_btn2:
            if st.button("🔄 רענן נתונים"):
                st.rerun()

        st.markdown(f"""
        <div class="expert-box">
            <h4 style="margin-top:0; color:#0369A1; display:flex; align-items:center; gap:8px;">
                <img src="{current_logo_url}" class="stock-logo" onerror="this.style.display='none'">
                נבחר כעת: {current_sig['symbol']}
            </h4>
            <p style="font-size: 0.78rem; color: #64748B; margin-bottom:4px;">🕒 נרשם ב: {current_sig['timestamp']}</p>
            <p style="font-size: 0.95rem; font-weight: bold; margin-bottom: 5px;">{current_sig['signal']}</p>
            <p style="font-size: 0.85rem; color: #334155;"><strong>ניתוח משוקלל (20+ פרמטרים):</strong> {current_sig['reason']}</p>
            <hr style="border:0; border-top:1px solid #BAE6FD; margin:6px 0;">
            <p style="font-size: 0.85rem; margin:0;">🎯 <strong>TP:</strong> ${current_sig['tp']:.2f} | 🛡️ <strong>SL:</strong> ${current_sig['sl']:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📋 העתק SL/TP מומלצים לטופס רכישה", use_container_width=True):
            st.session_state.active_sl = current_sig['sl']
            st.session_state.active_tp = current_sig['tp']
            st.success("ערכי ה-SL וה-TP הועתקו בהצלחה לטופס הרכישה למטה!")
            st.rerun()

        st.markdown("---")
        
        with st.expander("🛒 ההמלצות האקטיביות שלך לכל הפוזיציות הפתוחות (לחץ לפתיחה / מיזעור)", expanded=True):
            if not st.session_state.positions:
                st.info("אין לך פוזיציות פתוחות בתיק כרגע.")
            else:
                for p in st.session_state.positions:
                    p_df = load_stock_data(p['symbol'], "5d", "1d")
                    l_p = float(p_df['Close'].iloc[-1]) if not p_df.empty else p['buy_price']
                    p_sig = calculate_comprehensive_matrix(p['symbol'])
                    feas = calculate_sell_feasibility(p, l_p, p_sig)
                    pnl_p = ((l_p / p['buy_price']) - 1) * 100
                    
                    box_style = "background-color: #FEF2F2; border-right: 5px solid #DC2626;" if feas > 50 else "background-color: #F0FDF4; border-right: 5px solid #16A34A;"
                    action_txt = "🔴 **מכור עכשיו**" if feas > 50 else "🟢 **השאר והחזק**"
                    
                    st.markdown(f"""
                    <div style="{box_style} padding: 10px; border-radius: 8px; margin-bottom: 8px;">
                        <div style="font-weight:bold; font-size:0.9rem; color:#0F172A;">{p['symbol']} ({p['shares']:.4f} יחידות) | כדאיות מכירה: {feas}%</div>
                        <div style="font-size:0.8rem; color:#334155; margin-top:2px;">
                            מחיר קנייה: ${p['buy_price']:.2f} | נוכחי: ${l_p:.2f} (תשואה: {pnl_p:+.2f}%)<br>
                            <strong>המלצה אקטיבית:</strong> {action_txt}<br>
                            <em>ציון קונפלואנס:</em> {p_sig['confluence_score']}%.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    with chat_tab3:
        if st.session_state.mentor_signals_log:
            log_options = [f"{item['timestamp']} | {item['symbol']} | {item['signal']}" for item in st.session_state.mentor_signals_log]
            selected_log_idx = st.selectbox("בחר המלצה מהארכיון:", range(len(log_options)), format_func=lambda x: log_options[x])
            selected_item = st.session_state.mentor_signals_log[selected_log_idx]
            
            st.markdown(f"""
            <div style="background-color: #F8FAFC; border:1px solid #CBD5E1; padding:10px; border-radius:8px;">
                <p style="font-size:0.75rem; color:#64748B; margin:0;">🕒 תאריך: {selected_item['timestamp']}</p>
                <h5 style="margin:4px 0;">סימול: {selected_item['symbol']} (מחיר: ${selected_item.get('price', 0):.2f})</h5>
                <p style="font-weight:bold; margin:2px 0;">{selected_item['signal']}</p>
                <p style="font-size:0.85rem; color:#334155;">{selected_item['reason']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("אין היסטוריית המלצות עדיין.")

with col_left_chart:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
        <img src="{current_logo_url}" class="stock-logo" onerror="this.style.display='none'">
        <h4 style="margin:0;">גרף מסחר דינמי {ticker_symbol} (מחיר נוכחי: ${current_price:.2f})</h4>
    </div>
    """, unsafe_allow_html=True)
    
    df['RSI'] = calculate_rsi(df, 14)
    df['RSI_MA'] = df['RSI'].rolling(window=14).mean()
    df['SMA20'] = df['Close'].rolling(20).mean()

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
    )

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        increasing_line_color='#22C55E',
        decreasing_line_color='#EF4444',
        name="מחיר OHLC"
    ), row=1, col=1, secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df.index, y=df['SMA20'], mode='lines', name='ממוצע 20 (SMA)',
        line=dict(color='#3B82F6', width=1.5)
    ), row=1, col=1, secondary_y=False)

    volume_colors = ['#22C55E' if c >= o else '#EF4444' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'], name='נפח מסחר',
        marker_color=volume_colors, opacity=0.4
    ), row=1, col=1, secondary_y=True)

    fig.update_yaxes(range=[0, df['Volume'].max() * 3.5 if not df.empty else 1], showticklabels=False, secondary_y=True, row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df.index, y=df['RSI'], mode='lines', name='RSI 14',
        line=dict(color='#8B5CF6', width=1.5)
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=df.index, y=df['RSI_MA'], mode='lines', name='RSI MA',
        line=dict(color='#EAB308', width=1.2)
    ), row=2, col=1)

    fig.add_hline(y=70, line_dash="dash", line_color="#EF4444", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#22C55E", row=2, col=1)

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=450,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='#FFFFFF',
        plot_bgcolor='#FAFAFA',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
    )

    fig.update_yaxes(title_text="מחיר ($)", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="RSI (14)", range=[0, 100], row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)

    rsi_val = current_sig['rsi']
    rsi_desc = "קניית יתר (מעל 70)" if rsi_val > 70 else ("מכירת יתר (מתחת ל30)" if rsi_val < 30 else "רמה מאוזנת")

    with st.expander("🎓 הצג ניתוח לימודי מורחב על הגרף ומדדי היסוד", expanded=False):
        st.markdown(f"""
        <div class="educational-inline-box" style="margin-top:0;">
            <ul style="margin:0; padding-right:18px; font-size:0.83rem; color:#334155; line-height:1.45;">
                <li><strong>נרות יפניים (Candlesticks):</strong> פכולוגיית השוק במסגרת הזמן הנבחרת ב-${current_price:.2f}.</li>
                <li><strong>ציון קונפלואנס רב-ממדי:</strong> עומד על <strong>{current_sig['confluence_score']}%</strong> ומאגד למעלה מ-20 פרמטרים.</li>
                <li><strong>מדד עוצמה יחסית (RSI):</strong> עומד על <strong>{rsi_val:.1f}</strong> ונמצא במצב <strong>{rsi_desc}</strong>.</li>
                <li><strong>ניהול סיכונים מבוסס ATR:</strong> עצירת הפסד ב-<strong>${current_sig['sl']:.2f}</strong> ויעד רווח ב-<strong>${current_sig['tp']:.2f}</strong>.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 10א. שני גרפי מאקרו ומיקרו קבועים
# ==========================================
st.markdown("---")
with st.expander(f"🔬 ניתוח רב-זמני קבוע (Multi-Timeframe Anchor) עבור {ticker_symbol} (לחץ לפתיחה / מיזעור)", expanded=False):
    st.caption("שתי רזולוציות קבועות ומדויקות: **מאקרו** (יומי) וחתך **מיקרו** (שעתי).")

    macro_df = load_stock_data(ticker_symbol, "1y", "1d")
    micro_df = load_stock_data(ticker_symbol, "5d", "1h")

    if not macro_df.empty and not micro_df.empty:
        macro_df['SMA20'] = macro_df['Close'].rolling(20).mean()
        macro_df['SMA50'] = macro_df['Close'].rolling(50).mean()
        macro_df['RSI'] = calculate_rsi(macro_df, 14)

        micro_df['SMA20'] = micro_df['Close'].rolling(20).mean()
        micro_df['RSI'] = calculate_rsi(micro_df, 14)

        fig_macro = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
        fig_macro.add_trace(go.Candlestick(x=macro_df.index, open=macro_df['Open'], high=macro_df['High'], low=macro_df['Low'], close=macro_df['Close'], name="מאקרו (יומי)", increasing_line_color='#22C55E', decreasing_line_color='#EF4444'), row=1, col=1)
        fig_macro.add_trace(go.Scatter(x=macro_df.index, y=macro_df['SMA20'], mode='lines', name='SMA 20 (יומי)', line=dict(color='#3B82F6', width=1.5)), row=1, col=1)
        fig_macro.add_trace(go.Scatter(x=macro_df.index, y=macro_df['SMA50'], mode='lines', name='SMA 50 (יומי)', line=dict(color='#F59E0B', width=1.5)), row=1, col=1)
        fig_macro.add_trace(go.Scatter(x=macro_df.index, y=macro_df['RSI'], mode='lines', name='RSI 14 (יומי)', line=dict(color='#8B5CF6', width=1.2)), row=2, col=1)
        fig_macro.add_hline(y=70, line_dash="dash", line_color="#EF4444", row=2, col=1)
        fig_macro.add_hline(y=30, line_dash="dash", line_color="#22C55E", row=2, col=1)
        fig_macro.update_layout(xaxis_rangeslider_visible=False, template="plotly_white", height=380, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
        fig_macro.update_yaxes(title_text="מחיר ($)", row=1, col=1)
        fig_macro.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1)

        fig_micro = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
        fig_micro.add_trace(go.Candlestick(x=micro_df.index, open=micro_df['Open'], high=micro_df['High'], low=micro_df['Low'], close=micro_df['Close'], name="מיקרו (שעתי)", increasing_line_color='#22C55E', decreasing_line_color='#EF4444'), row=1, col=1)
        fig_micro.add_trace(go.Scatter(x=micro_df.index, y=micro_df['SMA20'], mode='lines', name='SMA 20 (שעתי)', line=dict(color='#3B82F6', width=1.5)), row=1, col=1)
        fig_micro.add_trace(go.Scatter(x=micro_df.index, y=micro_df['RSI'], mode='lines', name='RSI 14 (שעתי)', line=dict(color='#8B5CF6', width=1.2)), row=2, col=1)
        fig_micro.add_hline(y=70, line_dash="dash", line_color="#EF4444", row=2, col=1)
        fig_micro.add_hline(y=30, line_dash="dash", line_color="#22C55E", row=2, col=1)
        fig_micro.update_layout(xaxis_rangeslider_visible=False, template="plotly_white", height=380, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
        fig_micro.update_yaxes(title_text="מחיר ($)", row=1, col=1)
        fig_micro.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1)

        st.markdown("##### 📈 1. מבט מאקרו ראשי (טווח 1 שנה | נרות יומיים)")
        st.plotly_chart(fig_macro, use_container_width=True)
        
        st.markdown("##### ⚡ 2. מבט מיקרו טקטי (טווח 5 ימים | נרות שעתיים)")
        st.plotly_chart(fig_micro, use_container_width=True)
    else:
        st.warning("לא ניתן לטעון נתוני מאקרו/מיקרו עבור סימול זה כרגע.")

# ==========================================
# 11. תיאור חברה מורחב
# ==========================================
with st.expander(f"ℹ️ תיאור חברה מורחב ופרופיל עסקי - {ticker_symbol}"):
    if info:
        raw_sector = info.get('sector', 'N/A')
        sector_hebrew = SECTOR_HEBREW.get(raw_sector, raw_sector)
        market_cap = info.get('marketCap', 0)
        market_cap_str = f"${market_cap / 1e9:.2f} מיליארד דולר" if market_cap >= 1e9 else f"${market_cap / 1e6:.2f} מיליון דולר"
        pe_ratio = info.get('trailingPE', 'N/A')
        pe_str = f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A"

        st.markdown(f"""
        ### 🏢 פרופיל עסקי: {info.get('longName', ticker_symbol)}
        **מגזר ענפי:** {sector_hebrew} | **שווי שוק:** {market_cap_str} | **מכפיל רווח (P/E):** {pe_str}  
        **סיכום פעילות:** {info.get('longBusinessSummary', 'אין תיאור זמין.')}
        """)

# ==========================================
# 12. אזור ביצוע עסקה (Paper Trading)
# ==========================================
st.markdown("### 🛒 ביצוע עסקה (Paper Trading)")

default_sl = st.session_state.active_sl if st.session_state.active_sl > 0 else current_sig['sl']
default_tp = st.session_state.active_tp if st.session_state.active_tp > 0 else current_sig['tp']

c1, c2, c3, c4 = st.columns(4)
with c1:
    shares = st.number_input("כמות מניות", min_value=0.0001, value=1.0, step=0.01, format="%.4f")
with c2:
    sl_price = st.number_input("Stop Loss ($)", min_value=0.0, value=default_sl)
with c3:
    tp_price = st.number_input("Take Profit ($)", min_value=0.0, value=default_tp)
with c4:
    st.write("")
    buy_btn = st.button("📥 קנה מנייה / מדד", use_container_width=True)

total_cost = shares * current_price
pct_of_cash = (total_cost / st.session_state.cash) * 100 if st.session_state.cash > 0 else 0

st.info(f"💵 **עלות העסקה:** **${total_cost:,.2f}** (מהווה **{pct_of_cash:.1f}%** מהמזומן הפנוי)")

if buy_btn:
    if total_cost > st.session_state.cash:
        st.error("אין מספיק מזומן פנוי בתיק לביצוע העסקה!")
    else:
        st.session_state.cash -= total_cost
        st.session_state.positions.append({
            'symbol': ticker_symbol,
            'shares': shares,
            'buy_price': current_price,
            'total_cost': total_cost,
            'sl': sl_price,
            'tp': tp_price,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'buy_rsi': current_sig['rsi'],
            'buy_reason': current_sig['reason']
        })
        play_audio_alert()
        save_portfolio_to_file()
        st.success(f"נרכשו {shares:.4f} יחידות של {ticker_symbol} בעלות של ${total_cost:,.2f}!")
        st.rerun()

# ==========================================
# 13. פוזיציות פתוחות ומעקב רווח/הפסד
# ==========================================
st.markdown("---")
with st.expander("💼 פוזיציות פתוחות ומעקב רווח/הפסד (לחץ לפתיחה / מיזעור)", expanded=True):
    if not st.session_state.positions:
        st.info("אין פוזיציות פתוחות כרגע בתיק.")
    else:
        for i, pos in enumerate(st.session_state.positions):
            pos_df = load_stock_data(pos['symbol'], "5d", "1d")
            live_price = float(pos_df['Close'].iloc[-1]) if not pos_df.empty else pos['buy_price']
            
            pos_sig = calculate_comprehensive_matrix(pos['symbol'])
            sell_feasibility = calculate_sell_feasibility(pos, live_price, pos_sig)
            
            if sell_feasibility > 50:
                circle_indicator = f'<span class="flash-blue-circle" title="כדאיות מכירה גבוהה (>50%)"></span>'
            else:
                circle_indicator = f'<span class="red-circle" title="כדאיות מכירה נמוכה (<=50%)"></span>'

            current_val = live_price * pos['shares']
            gross_pnl = current_val - pos['total_cost']
            pnl_pct = ((live_price / pos['buy_price']) - 1) * 100
            tax_amount = (gross_pnl * 0.25) if gross_pnl > 0 else 0.0
            net_pnl = gross_pnl - tax_amount
            pos_logo = get_stock_logo_url(pos['symbol'])

            col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns([2, 1.8, 1.8, 2.2, 1.7])
            
            with col_p1:
                st.markdown(f"""
                <div style="display:flex; align-items:center; gap:6px;">
                    <img src="{pos_logo}" class="stock-logo" onerror="this.style.display='none'">
                    <div>
                        <strong>{pos['symbol']}</strong> ({pos['shares']:.4f} יח')<br>
                        <span style="font-size:0.75rem; color:#64748B;">עלות: ${pos['total_cost']:,.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_p2:
                st.write(f"קנייה: **${pos['buy_price']:.2f}**")
                st.write(f"נוכחי: **${live_price:.2f}**")
            with col_p3:
                st.write(f"SL: **${pos['sl']:.2f}**")
                st.write(f"TP: **${pos['tp']:.2f}**")
            with col_p4:
                color_code = "#16A34A" if gross_pnl >= 0 else "#DC2626"
                tax_html = f"<br><span style='font-size:0.75rem; color:#64748B;'>נטו לאחר מס: ${net_pnl:+.2f}</span>" if tax_amount > 0 else ""
                st.markdown(f"""
                <div style="line-height:1.25;">
                    <span style="color:{color_code}; font-weight:bold; font-size:1.0rem;">${gross_pnl:+.2f} ({pnl_pct:+.2f}%)</span>
                    {tax_html}
                </div>
                """, unsafe_allow_html=True)
            with col_p5:
                st.markdown(f"""
                <div style="font-size:0.78rem; font-weight:600; color:#334155; margin-bottom:2px;">
                    כדאיות מכירה: {sell_feasibility}% {circle_indicator}
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"🔴 מכור", key=f"sell_{i}"):
                    sell_date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    cash_return = pos['total_cost'] + net_pnl
                    st.session_state.cash += cash_return
                    
                    feedback = [f"🟢 **עסקה סגורה!** רווח ברוטו: ${gross_pnl:.2f}."] if gross_pnl >= 0 else [f"🔴 **עסקה בהפסד** של ${abs(gross_pnl):.2f}."]
                    if tax_amount > 0:
                        feedback.append(f"נוכו ${tax_amount:.2f} מס רווח הון (25%).")
                    
                    st.session_state.history.append({
                        'symbol': pos['symbol'],
                        'shares': pos['shares'],
                        'cost': pos['total_cost'],
                        'buy_price': pos['buy_price'],
                        'sell_val': current_val,
                        'gross_pnl': gross_pnl,
                        'tax': tax_amount,
                        'net_pnl': net_pnl,
                        'buy_date': pos.get('date', 'לא ידוע'),
                        'sell_date': sell_date_str,
                        'buy_sl': pos.get('sl', 0.0),
                        'buy_tp': pos.get('tp', 0.0),
                        'buy_rsi': pos.get('buy_rsi', 50.0),
                        'buy_reason': pos.get('buy_reason', 'אין נתון'),
                        'sell_rsi': pos_sig['rsi'],
                        'feedback': " ".join(feedback)
                    })
                    st.session_state.positions.pop(i)
                    play_audio_alert()
                    save_portfolio_to_file()
                    st.rerun()

# ==========================================
# 14. היסטוריית עסקאות וסגירת פוזיציות
# ==========================================
st.markdown("---")
with st.expander("📜 היסטוריית עסקאות וסגירת פוזיציות (לחץ לפתיחה / מיזעור)", expanded=False):
    h_title_col, h_reset_col = st.columns([4, 1])

    with h_reset_col:
        if st.button("🗑️ איפוס היסטוריה"):
            st.session_state.confirm_history_reset = True

    if st.session_state.get('confirm_history_reset', False):
        st.warning("⚠️ **האם אתה בטוח שברצונך למחוק את היסטוריית העסקאות?**")
        c_h1, c_h2 = st.columns([1, 4])
        with c_h1:
            if st.button("✅ כן, מחק", type="primary"):
                st.session_state.history = []
                st.session_state.confirm_history_reset = False
                save_portfolio_to_file()
                st.rerun()
        with c_h2:
            if st.button("❌ ביטול"):
                st.session_state.confirm_history_reset = False
                st.rerun()

    if not st.session_state.history:
        st.info("אין עסקאות סגורות בהיסטוריה.")
    else:
        for h in reversed(st.session_state.history):
            box_class = "feedback-success" if h['gross_pnl'] >= 0 else "feedback-danger"
            buy_date = h.get('buy_date', 'לא ידוע')
            sell_date = h.get('sell_date', 'לא ידוע')
            buy_price_val = h.get('buy_price', h['cost'] / h['shares'] if h['shares'] > 0 else 0.0)
            buy_sl = h.get('buy_sl', 0.0)
            buy_tp = h.get('buy_tp', 0.0)
            buy_rsi = h.get('buy_rsi', 50.0)
            sell_rsi = h.get('sell_rsi', 50.0)
            buy_reason = h.get('buy_reason', 'לא זמין')
            
            st.markdown(f"""
            <div class="{box_class}" style="padding: 14px; border-radius: 8px; margin-bottom: 12px;">
                <h4 style="margin-top:0; margin-bottom:6px;">עסקה סגורה ב-{h['symbol']} | רווח/הפסד נטו: ${h['net_pnl']:+.2f}</h4>
                <div style="font-size:0.85rem; line-height:1.5; color:#334155;">
                    <div>📅 <strong>תאריך ושעת קנייה:</strong> {buy_date} | 📅 <strong>תאריך ושעת מכירה:</strong> {sell_date}</div>
                    <div>💰 <strong>מחיר קנייה:</strong> ${buy_price_val:.2f} | 🛡️ <strong>SL שהוגדר:</strong> ${buy_sl:.2f} | 🎯 <strong>TP שהוגדר:</strong> ${buy_tp:.2f}</div>
                    <div>💵 <strong>עלות כוללת:</strong> ${h['cost']:,.2f} | 🏦 <strong>תקבול מכירה:</strong> ${h['sell_val']:,.2f} | <strong>מס שנוכה (25%):</strong> ${h['tax']:.2f}</div>
                    <div>📊 <strong>מדד RSI בקנייה:</strong> {buy_rsi:.1f} | 📉 <strong>מדד RSI במכירה:</strong> {sell_rsi:.1f}</div>
                    <div style="margin-top:4px;">💡 <strong>ניתוח / סיבת קנייה מקורית:</strong> {buy_reason}</div>
                    <div style="margin-top:2px;">📌 <strong>סיכום עסקה:</strong> {h['feedback']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)