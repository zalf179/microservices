import pika
import time
import json
import os
import psycopg2
from psycopg2 import Error
import pymongo
from bson.objectid import ObjectId

# --- KONFIGURASI ---
RABBITMQ_URL = os.environ.get('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq:5672/')
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://mongodb:27017/')
POSTGRES_URI = os.environ.get('POSTGRES_URI', 'dbname=payments user=postgres password=password host=postgres')
QUEUE_NAME = 'order_queue'

print("� Payment Worker: Memulai inisialisasi...")

# --- KONEKSI MONGODB ---
try:
    mongo_client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_db = mongo_client["orders"]
    mongo_col = mongo_db["orders"]
    # Tes koneksi
    mongo_client.server_info()
    print("✅ MongoDB: Terhubung!")
except Exception as e:
    print(f"❌ MongoDB Error: {e}")

# --- KONEKSI POSTGRES ---
def connect_postgres():
    while True:
        try:
            conn = psycopg2.connect(POSTGRES_URI)
            print("✅ PostgreSQL: Terhubung!")
            return conn
        except Error as e:
            print(f"❌ PostgreSQL Error: {e}. Coba lagi dalam 5 detik...")
            time.sleep(5)

db_conn = connect_postgres()
db_cursor = db_conn.cursor()

# Buat tabel jika belum ada
db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_payments (
        id SERIAL PRIMARY KEY,
        order_id VARCHAR(255),
        customer_name VARCHAR(255),
        amount DECIMAL,
        status VARCHAR(50),
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
db_conn.commit()

# --- FUNGSI PROSES PESAN ---
def callback(ch, method, properties, body):
    print(f"\n� [DAPET PESAN] Raw data: {body.decode()}")
    
    try:
        data = json.loads(body)
        order_id = data.get('orderId')
        amount = data.get('amount')
        customer = data.get('customerName')

        print(f"⚙️ Memproses Order ID: {order_id} (Customer: {customer}, Total: {amount})")
        
        # Simulasi proses (biar keliatan di UI ada jeda)
        time.sleep(2)
        
        # Logika Bisnis
        payment_status = 'SUCCESS' if amount < 1000 else 'FAILED'

        # 1. Simpan ke Postgres
        db_cursor.execute(
            "INSERT INTO processed_payments (order_id, customer_name, amount, status) VALUES (%s, %s, %s, %s)",
            (order_id, customer, amount, payment_status)
        )
        db_conn.commit()
        print(f"� Disimpan ke Postgres: {payment_status}")

        # 2. Update ke MongoDB agar UI berubah
        result = mongo_col.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": payment_status}}
        )
        
        if result.modified_count > 0:
            print(f"✨ MongoDB Berhasil Update Status ke: {payment_status}")
        else:
            print("⚠️ MongoDB Gagal Update (ID tidak ditemukan atau status sudah sama)")

    except Exception as e:
        print(f"❌ ERROR SAAT PROSES: {e}")
    
    # Kasih tau RabbitMQ kalau pesan udah diproses (biar dihapus dari antrean)
    ch.basic_ack(delivery_tag=method.delivery_tag)

# --- JALANKAN WORKER ---
def start_worker():
    while True:
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

            print('� [*] Worker READY. Menunggu pesanan baru...')
            channel.start_consuming()
        except Exception as e:
            print(f"❌ RabbitMQ Error: {e}. Restarting worker in 5s...")
            time.sleep(5)

if __name__ == '__main__':
    start_worker()