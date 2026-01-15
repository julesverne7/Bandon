#!/usr/bin/env python
"""Wait for database to be ready before starting the application."""
import os
import sys
import time
import psycopg

def wait_for_db(max_retries=30, delay=2):
    """Wait for database to be available."""
    db_config = {
        'dbname': os.getenv('DB_NAME', 'gymwebdb'),
        'user': os.getenv('DB_USER', 'gymweb'),
        'password': os.getenv('DB_PASSWORD', '0ccdcd0dfee241416a4e924b367bb07f'),
        'host': os.getenv('DB_HOST', 'db'),
        'port': os.getenv('DB_PORT', '5432'),
    }
    
    print(f"Waiting for database at {db_config['host']}:{db_config['port']}...")
    
    for attempt in range(max_retries):
        try:
            conn = psycopg.connect(**db_config)
            conn.close()
            print("✓ Database is ready!")
            return True
        except psycopg.OperationalError as e:
            print(f"Attempt {attempt + 1}/{max_retries}: Database not ready yet... ({e})")
            time.sleep(delay)
    
    print("✗ Could not connect to database after maximum retries", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    wait_for_db()
