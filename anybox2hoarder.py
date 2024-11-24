#!/usr/bin/env python3

import requests
import json
import os
import time
import urllib.request
from datetime import datetime

ANYBOX_API_KEY = os.getenv('Anybox_API_Key')
HOARDER_API_KEY = os.getenv('HOARDER_API_KEY')
HOARDER_URL = os.getenv('HOARDER_URL')
PROCESSED_FILE = 'processed_hoarder_items.json'

def get_anybox_links():
    headers = {'x-api-key': ANYBOX_API_KEY}
    payload = {
        'q': '',
        'limit': 30,
        'type': 'all',
        'linkDescriptions': 'yes'
    }
    
    data = urllib.parse.urlencode(payload)
    req = urllib.request.Request('http://127.0.0.1:6391/search?' + data, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Error fetching Anybox links: {e}")
        return []

def send_to_hoarder(item):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {HOARDER_API_KEY}'
    }

    tags = [tag['name'] for tag in item.get('tags', [])]
    tags.append('from_anybox')
    
    payload = {
        "url": item['url'],
        "title": item['title'],
        "type": "link",
        "archived": False,
        "favourited": False,
        "note": item.get('description', ''),
        "tags": tags,
        "createdAt": item.get('dateLastOpened', datetime.now().isoformat())
    }

    try:
        response = requests.post(
            f"{HOARDER_URL}/api/v1/bookmarks",
            headers=headers,
            json=payload
        )
        
        if response.status_code in [200, 201]:
            print(f"Successfully sent {item['title']} to Hoarder")
            return True
        else:
            print(f"Failed to send {item['title']} to Hoarder: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Error sending to Hoarder: {e}")
        return False

def load_processed_items():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as file:
            return json.load(file)
    return []

def save_processed_items(items):
    with open(PROCESSED_FILE, 'w') as file:
        json.dump(items, file)

def monitor_and_sync():
    if not all([ANYBOX_API_KEY, HOARDER_API_KEY, HOARDER_URL]):
        print("Please set all required environment variables!")
        return

    processed_items = load_processed_items()
    
    while True:
        try:
            print("Checking for new Anybox items...")
            links = get_anybox_links()
            new_items = [item for item in links if item['id'] not in processed_items]
            
            if new_items:
                print(f"Found {len(new_items)} new items")
                for item in new_items:
                    if send_to_hoarder(item):
                        processed_items.append(item['id'])
                        save_processed_items(processed_items)
            else:
                print("No new items found")
                
            time.sleep(300)
            
        except Exception as e:
            print(f"Error in sync loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    monitor_and_sync()

