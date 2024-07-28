from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
import csv
from collections import defaultdict
from datetime import datetime
import pandas as pd
from data.data_path import data_path

app = Flask(__name__)
Bootstrap(app)

def read_csv(filepath):
    offers = defaultdict(lambda: {'dates': [], 'prices': []})
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            key = (row['address'], row['description'], row['url'])
            if not offers[key]['prices'] or row['price'] not in offers[key]['prices']:
                offers[key]['dates'].append(row['date'])
                offers[key]['prices'].append(row['price'])
    # Sort dates and prices together
    for key in offers:
        sorted_dates_prices = sorted(zip(offers[key]['dates'], offers[key]['prices']), 
                                     key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'))
        unique_dates_prices = []
        last_price = None
        for date, price in sorted_dates_prices:
            if price != last_price:
                unique_dates_prices.append((date, price))
                last_price = price
            else:
                unique_dates_prices[-1] = (unique_dates_prices[-1][0], price)
        offers[key]['dates'], offers[key]['prices'] = zip(*unique_dates_prices) if unique_dates_prices else ([], [])
    return offers

def convert_price_to_float(price_str):
    if price_str.strip() == '':
        return 0.0  
    return float(price_str.replace(' ', '').replace(',', '.').replace('zł', ''))


@app.route('/')
def index():
    offers = read_csv(data_path)
    # Sort offers by the newest date of each key
    sorted_offers = dict(sorted(offers.items(), key=lambda x: datetime.strptime(x[1]['dates'][-1], '%Y-%m-%d'), reverse=True))
    # Convert to DataFrame for analysis
    df = pd.DataFrame([(key[0], key[1], key[2], dates, prices) 
                       for key, value in sorted_offers.items() 
                       for dates, prices in zip(value['dates'], value['prices'])],
                      columns=['Address', 'Description', 'URL', 'Date', 'Price'])
    # Data analysis
    df['Price'] = df['Price'].apply(convert_price_to_float)
    avg_price = df['Price'].mean()
    return render_template('index.html', offers=sorted_offers, enumerate=enumerate, avg_price=avg_price)

if __name__ == '__main__':
    app.run(debug=True)
