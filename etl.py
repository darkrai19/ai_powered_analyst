import pandas as pd
import datetime as dt
from sqlalchemy import create_engine
import psycopg
import os

# Data loading
df = pd.read_csv(r'e-commerce-shopping-dataset.csv', parse_dates=['order_date'])

# Schema Setup
fct_order_line_items = df.copy()

fct_order_line_items['location'] = fct_order_line_items['city'] + ', ' + fct_order_line_items['state'] + ' ' + fct_order_line_items['zipcode']

for column in ['payment_method', 'delivery_status', 'order_date', 'location']:
    fct_order_line_items[column + '_id'] = fct_order_line_items[column].astype('category').cat.codes + 1

dim_product = fct_order_line_items[['product_id', 'product_category', 'product_price']]
dim_payment_method = fct_order_line_items[['payment_method_id','payment_method']].drop_duplicates().dropna().sort_values(by='payment_method_id')
dim_delivery_status = fct_order_line_items[['delivery_status_id','delivery_status']].drop_duplicates().dropna().sort_values(by='delivery_status_id')
dim_customer = df[['customer_id']]
dim_location = df[['location_id', 'city', 'state', 'zipcode']].drop_duplicates().dropna().reset_index(drop=True).sort_values(by='zipcode')

dim_date = fct_order_line_items[['order_date_id', 'order_date']].drop_duplicates().dropna().reset_index(drop=True).sort_values(by='order_date')
dim_date['year'] = dim_date['order_date'].dt.year
dim_date['month'] = dim_date['order_date'].dt.month
dim_date['day'] = dim_date['order_date'].dt.day
dim_date['day_name'] = dim_date['order_date'].dt.day_name()
dim_date['day_of_week'] = dim_date['order_date'].dt.dayofweek
dim_date['day_of_year'] = dim_date['order_date'].dt.dayofyear
dim_date['weekday'] = dim_date['order_date'].dt.weekday
dim_date['quarter'] = dim_date['order_date'].dt.quarter
dim_date['year_month'] = dim_date['order_date'].dt.strftime('%Y-%m')
dim_date['year_week'] = dim_date['order_date'].dt.strftime('%Y-%W')
dim_date.sort_values(by='order_date_id', inplace=True)

fct_order_line_items.drop(columns=['payment_method', 'delivery_status', 'product_category', 'product_price', 'city', 'state', 'zipcode', 'order_date'], inplace=True)
fct_order_line_items = fct_order_line_items[['order_id', 'customer_id', 'product_id', 'location_id', 'discount_applied', 'quantity', 'order_value', 'order_date_id', 'payment_method_id', 'delivery_status_id', 'review_rating', 'return_requested' ]]

# Database connection setup
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

db_connection_str = f'postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
db_connection = create_engine(db_connection_str)

# Loading data into the database
try:
    print("Connecting to the database...")
    print("Loading dim_date...")
    dim_date.to_sql('dim_date', db_connection, if_exists='append', index=False)
    print("Loading dim_customer...")
    dim_customer.to_sql('dim_customer', db_connection, if_exists='append', index=False)
    print("Loading dim_product...")
    dim_product.to_sql('dim_product', db_connection, if_exists='append', index=False)
    print("Loading dim_location...")
    dim_location.to_sql('dim_location', db_connection, if_exists='append', index=False)
    print("Loading dim_payment_method...")
    dim_payment_method.to_sql('dim_payment_method', db_connection, if_exists='append', index=False)
    print("Loading dim_delivery_status...")
    dim_delivery_status.to_sql('dim_delivery_status', db_connection, if_exists='append', index=False)
    print("Loading fct_order_line_items...")
    fct_order_line_items.to_sql('fct_order_line_items', db_connection, if_exists='append', index=False)
    print("Data loading complete!")

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    db_connection.dispose()
