import pika
import time
import json
import os
import psycopg2
from psycopg2 import Error

RABBITMQ_URL = os.environ.get('RABBITMQ_URL', 'amqp://guest:guest@localhost/')
QUEUE_NAME = 'order_queue'
POSTGRES_URI = os.environ.get('POSTGRES_URI', 'dbname=payments user=postgres password=password host=localhost')

print("Payment Worker starting...")

# PostgreSQL Setup
def connect_postgres():
    while True:
        try:
            conn = psycopg2.connect(POSTGRES_URI)
            print("Connected to PostgreSQL")
            return conn
        except Error as e:
            print(f"PostgreSQL connection error: {e}, retrying in 5s...")
            time.sleep(5)

db_conn = connect_postgres()
db_cursor = db_conn.cursor()

# Bikin tabel kalau belum ada
db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_payments (
        id SERIAL PRIMARY KEY,
        order_id VARCHAR(255) NOT NULL,
        customer_name VARCHAR(255),
        amount DECIMAL,
        status VARCHAR(50),
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
db_conn.commit()

# Callback function pas dapet pesan dari RabbitMQ
def callback(ch, method, properties, body):
    order_data = json.loads(body)
    order_id = order_data['orderId']
    amount = order_data['amount']
    customer = order_data['customerName']
    
    print(f" [x] Received Order ID: {order_id} for amount {amount}")
    
    # 1. Simulasi Proses Pembayaran (biasanya panggil API Bank)
    print(" [x] Processing payment...")
    time.sleep(3) # Pura-puranya loading lama
    
    payment_status = 'SUCCESS' if amount < 1000 else 'FAILED' # Contoh logika simpel

    # 2. Simpan status ke PostgreSQL
    try:
        db_cursor.execute(
            "INSERT INTO processed_payments (order_id, customer_name, amount, status) VALUES (%s, %s, %s, %s)",
            (order_id, customer, amount, payment_status)
        )
        db_conn.commit()
        print(f" [x] Payment {payment_status} for Order {order_id} saved to Postgres")
    except Error as e:
        print(f" [!] Error saving to Postgres: {e}")
        db_conn.rollback()

    # 3. Acknowledge pesan (biar RabbitMQ tahu pesan udah kelar diproses)
    ch.basic_ack(delivery_tag=method.delivery_tag)

# RabbitMQ Setup & Consumption
def connect_rabbitmq():
    while True:
        try:
            # Perlu parse URL karena pika pake format beda
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            channel = connection.createChannel()
            channel.queueDeclare(queue=QUEUE_NAME, durable=True)
            
            # Biar worker nggak ngerjain lebih dari 1 pesan berbarengan
            channel.basic_qos(prefetch_count=1) 
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

            print(' [*] Waiting for messages. To exit press CTRL+C')
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ connection error, retrying in 5s...")
            time.sleep(5)

if __name__ == '__main__':
    connect_rabbitmq()
