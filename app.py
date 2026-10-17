import os
from otcharts import Client
import pandas as pd
from telegram import Bot

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# ⚙️ إعدادات منصة Pocket Option وزوج OTC
VENUE = "otc" 
SYMBOL = "EURUSD_otc" 

def calculate_indicators(df):
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

def generate_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    buy_condition = (
        last['RSI'] < 30 and
        last['EMA_20'] > last['EMA_50'] and
        last['MACD'] > last['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']
    )
    sell_condition = (
        last['RSI'] > 70 and
        last['EMA_20'] < last['EMA_50'] and
        last['MACD'] < last['MACD_Signal'] and prev['MACD'] >= prev['MACD_Signal']
    )
    if buy_condition:
        return "شراء (CALL) 🟢"
    elif sell_condition:
        return "بيع (PUT) 🔴"
    return None

def main():
    print(f"جاري تحليل سوق OTC لـ {SYMBOL} على {VENUE}...")
    
    try:
        otc = Client() # يقرأ المفتاح من متغير البيئة OTCHARTS_API_KEY
        bars = otc.candles(VENUE, SYMBOL, tf=60, limit=300)
        
        df = pd.DataFrame([{
            'time': b.time, 'open': b.open, 'high': b.high,
            'low': b.low, 'close': b.close
        } for b in bars])
        df = df.set_index('time')
        
    except Exception as e:
        print(f"خطأ في جلب البيانات (قد يكون بسبب نفاد الطلبات): {e}")
        return

    if df.empty:
        print("لا توجد بيانات متاحة.")
        return

    df = calculate_indicators(df)
    signal = generate_signal(df)
    
    bot = Bot(token=TELEGRAM_TOKEN)
    
    if signal:
        price = df['close'].iloc[-1]
        message = f"🚨 إشارة OTC جديدة!\n\nالمنصة: Pocket Option\nالزوج: {SYMBOL}\nالإشارة: {signal}\nالسعر: {price:.5f}\nالإطار الزمني: 1 دقيقة"
        bot.send_message(chat_id=CHAT_ID, text=message)
        print(f"تم إرسال الإشارة: {signal}")
    else:
        print("لا توجد إشارات حالياً. شروط الاستراتيجية لم تتحقق.")

if __name__ == '__main__':
    main()
