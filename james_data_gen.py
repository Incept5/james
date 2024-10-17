import os
import pandas as pd
import numpy as np
import sqlite3
from faker import Faker
from datetime import datetime, timedelta

def create_db(name):
    conn = sqlite3.connect(f'{name}.db')
    conn.close()

def write_df_to_sqlite(db_name, table_name, df):
    try:
        conn = sqlite3.connect(db_name)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.commit()
        print(f"DataFrame successfully written to table '{table_name}' in the database '{db_name}'.")
    except sqlite3.Error as e:
        print(f"An error occurred while writing to SQLite: {e}")
    finally:
        if conn:
            conn.close()

fake = Faker()

def generate_currencies():
    currencies = [
        ("USD", "US Dollar"), ("EUR", "Euro"), ("JPY", "Japanese Yen"),
        ("GBP", "British Pound"), ("AUD", "Australian Dollar"),
        ("CAD", "Canadian Dollar"), ("CHF", "Swiss Franc"),
        ("CNY", "Chinese Yuan"), ("SEK", "Swedish Krona"),
        ("NZD", "New Zealand Dollar"), ("MXN", "Mexican Peso"),
        ("SGD", "Singapore Dollar"), ("HKD", "Hong Kong Dollar"),
        ("NOK", "Norwegian Krone"), ("KRW", "South Korean Won"),
        ("TRY", "Turkish Lira"), ("RUB", "Russian Ruble"),
        ("INR", "Indian Rupee"), ("BRL", "Brazilian Real"),
        ("ZAR", "South African Rand")
    ]
    df = pd.DataFrame(currencies, columns=['CCY', 'Currency_Name'])
    df.insert(0, 'ID', range(1, len(df) + 1))
    return df

def generate_counterparties():
    counterparties = []
    for i in range(1, 31):
        counterparties.append({
            'ID': i,
            'Name': f'CPTY{i:02d}',
            'Address': fake.address()
        })
    return pd.DataFrame(counterparties)

def generate_random_weekday_datetime(start_date, end_date):
    # Generate a random date between start_date and end_date
    random_date = start_date + timedelta(days=np.random.randint(0, (end_date - start_date).days))

    # If the random date is a weekend, move it to the next Monday
    while random_date.weekday() >= 5:  # 5 and 6 represent Saturday and Sunday
        random_date += timedelta(days=1)

    # Generate a random time between 9:00 AM and 5:00 PM
    random_time = timedelta(hours=np.random.randint(9, 18), minutes=np.random.randint(0, 60), seconds=np.random.randint(0, 60))

    return datetime.combine(random_date.date(), (datetime.min + random_time).time())

def generate_trades(currencies_df, counterparties_df):
    trades = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    for i in range(1, 1001):
        cpty1, cpty2 = np.random.choice(counterparties_df['ID'], 2, replace=False)
        ccy1, ccy2 = np.random.choice(currencies_df['CCY'], 2, replace=False)
        amount1 = np.random.uniform(10000, 50000000)
        amount2 = np.random.uniform(10000, 50000000)

        # Randomly decide which amount to round to 3 significant figures
        if np.random.choice([True, False]):
            amount1 = round(amount1, -int(np.floor(np.log10(abs(amount1)))) + 2)
            amount2 = round(amount2, 2)  # Round to 2 decimal places
        else:
            amount1 = round(amount1, 2)  # Round to 2 decimal places
            amount2 = round(amount2, -int(np.floor(np.log10(abs(amount2)))) + 2)

        trade_datetime = generate_random_weekday_datetime(start_date, end_date)
        trades.append({
            'ID': i,
            'CPTY1': f'CPTY{cpty1:02d}',
            'CPTY2': f'CPTY{cpty2:02d}',
            'CCY1': ccy1,
            'CCY2': ccy2,
            'BuyAmount': amount1,
            'SellAmount': amount2,
            'TradeDateTime': trade_datetime.strftime('%Y-%m-%dT%H:%M:%S')
        })
    return pd.DataFrame(trades)

if __name__ == '__main__':
    create_db('forex_trades')

    currencies_df = generate_currencies()
    write_df_to_sqlite('forex_trades.db', 'currencies', currencies_df)

    counterparties_df = generate_counterparties()
    write_df_to_sqlite('forex_trades.db', 'counterparties', counterparties_df)

    trades_df = generate_trades(currencies_df, counterparties_df)
    write_df_to_sqlite('forex_trades.db', 'trades', trades_df)