import os
import requests
import pandas as pd
from telegram import Bot

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
TWELVE_DATA_API_KEY = os.environ.get("TWELVE_DATA_API_KEY")
SYMBOL = "EUR/USD" # يمكنك تغييره لاحقاً لأي زوج آخر

def get_real_data(symbol):
    # جلب البيانات الحقيقية من Twelve Data
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=100&apikey={TWELVE_DATA_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    # التحقق من وجود أخطاء في الاتصال
    if 'values' not in data:
        print("خطأ في جلب البيانات:", data.get('message', 'سبب غير معروف'))
        return None
        
    df = pd.DataFrame(data['values'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.set_index('datetime')
    df = df.astype(float)
    df = df.sort_index()
    return df

def calculate_indicators(df):
    # حساب المؤشرات الفنية
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

def generate_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    # استراتيجية Triple Confirmation
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
    print(f"جاري تحليل السوق لـ {SYMBOL}...")
    df = get_real_data(SYMBOL)
    
    if df is None or df.empty:
        print("فشل في جلب البيانات. تأكد من صحة مفتاح API.")
        return

    df = calculate_indicators(df)
    signal = generate_signal(df)
    
    bot = Bot(token=TELEGRAM_TOKEN)
    
    if signal:
        price = df['close'].iloc[-1]
        message = f"🚨 إشارة جديدة!\n\nالزوج: {SYMBOL}\nالإشارة: {signal}\nالسعر: {price:.5f}\nالإطار الزمني: 1 دقيقة"
        bot.send_message(chat_id=CHAT_ID, text=message)
        print(f"تم إرسال الإشارة: {signal}")
    else:
        print("لا توجد إشارات حالياً. شروط الاستراتيجية لم تتحقق.")

if __name__ == '__main__':
    main()
