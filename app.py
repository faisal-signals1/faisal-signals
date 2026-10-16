import os
import random
import pandas as pd
import numpy as np
from telegram import Bot

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def get_mock_data():
    # توليد بيانات تجريبية لمحاكاة سوق OTC
    dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='1min')
    prices = [1.0850]
    for _ in range(99):
        prices.append(prices[-1] + random.uniform(-0.001, 0.001))
    
    df = pd.DataFrame({
        'close': prices
    }, index=dates)
    return df

def calculate_indicators(df):
    # حساب المؤشرات
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
    # شراء: RSI < 30، EMA20 > EMA50، تقاطع MACD صعودي
    buy_condition = (
        last['RSI'] < 30 and
        last['EMA_20'] > last['EMA_50'] and
        last['MACD'] > last['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']
    )
    
    # بيع: RSI > 70، EMA20 < EMA50، تقاطع MACD هبوطي
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
    print("جاري تحليل السوق...")
    df = get_mock_data()
    df = calculate_indicators(df)
    signal = generate_signal(df)
    
    bot = Bot(token=TELEGRAM_TOKEN)
    
    if signal:
        price = df['close'].iloc[-1]
        message = f"🚨 إشارة جديدة!\n\nالزوج: EURUSD_otc\nالإشارة: {signal}\nالسعر: {price:.5f}\nالإطار الزمني: 1 دقيقة"
        bot.send_message(chat_id=CHAT_ID, text=message)
        print(f"تم إرسال الإشارة: {signal}")
    else:
        print("لا توجد إشارات حالياً.")
        # يمكنك إرسال رسالة تأكيد فقط عند التشغيل اليدوي
        # bot.send_message(chat_id=CHAT_ID, text="✅ البوت يعمل، لكن لا توجد إشارة حالياً.")
    
    print("انتهى التحليل.")

if __name__ == '__main__':
    main()
