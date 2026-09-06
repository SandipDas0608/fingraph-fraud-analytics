"""
Kafka Event Producer for Financial Transaction Data Streaming.
Engineered by shubhamgawari9226 - Simulates real-time transaction events.
"""
import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
from kafka import KafkaProducer

load_dotenv()

# 1. Initialize Kafka Producer Configuration
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'financial-transactions')
KAFKA_SERVER = os.getenv('KAFKA_SERVER', 'localhost:9092')
STREAM_DELAY = float(os.getenv('STREAM_INTERVAL_SECONDS', '0.5'))

try:
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_SERVER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print(f"Successfully connected to Kafka server at {KAFKA_SERVER} (Topic: {KAFKA_TOPIC})")
except Exception as e:
    print(f"Error: Could not connect to Kafka server. Details: {e}")
    producer = None

# 2. Load the Dataset with New Column Structure
csv_file_path = os.getenv('TRANSACTIONS_CSV_PATH', 'transactions_dataset.csv')

try:
    print(f"Loading updated dataset from '{csv_file_path}'...")
    df = pd.read_csv(csv_file_path)
    
    # Shuffle the dataset to mix normal and suspicious rows naturally
    df_final = df.sample(frac=1).reset_index(drop=True) 
    print(f"Successfully loaded {len(df_final)} rows from the dataset.")
except FileNotFoundError:
    print(f"Error: The file '{csv_file_path}' was not found in your project folder.")
    df_final = None

# 3. Stream Rows to Kafka with Updated Headers
print("""
Kafka Event Producer for Financial Transaction Data Streaming.
Engineered by shubhamgawari9226 - Simulates real-time transaction events.
""")
    
    for index, row in df_final.iterrows():
        # Convert row to dictionary map
        transaction_data = row.to_dict()
        
        # Track streaming row inside terminal using new headers
        t_id = transaction_data.get('txn_id')
        t_amt = transaction_data.get('txn_amount')
        t_lbl = transaction_data.get('fraud_label')
        
        print(f"Streaming Row {index+1} -> ID: {t_id} | Amount: {t_amt} | Label: {t_lbl}")
        
        if producer:
            # Send transaction data packet to Kafka broker
            producer.send(KAFKA_TOPIC, value=transaction_data)
        
        # Artificial streaming interval (0.5 second lag)
        time.sleep(0.5)

    if producer:
        producer.flush()
    print("\nStreaming pipeline finished execution.")
