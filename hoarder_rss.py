#!/usr/bin/env python3

from flask import Flask, Response
from feedgen.feed import FeedGenerator
import requests
import os
from datetime import datetime
import pytz

app = Flask(__name__)

HOARDER_API_KEY = os.getenv('HOARDER_API_KEY')
HOARDER_SERVER_ADDR = os.getenv('HOARDER_SERVER_ADDR', 'http://localhost:8080')

def get_bookmarks():
    url = f"{HOARDER_SERVER_ADDR}/api/v1/bookmarks"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {HOARDER_API_KEY}'
    }
    params = {
        'limit': 100
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('bookmarks', [])
    except Exception as e:
        print(f"Error fetching bookmarks: {e}")
        return []

@app.route('/rss')
def rss():
    fg = FeedGenerator()
    fg.title('Hoarder Bookmarks')
    fg.description('RSS feed of Hoarder bookmarks')
    fg.link(href='http://localhost:5034/rss')
    fg.language('en')

    bookmarks = get_bookmarks()
    
    for bookmark in bookmarks:
        fe = fg.add_entry()
        
        title = (bookmark.get('content', {}).get('title') or 
                bookmark.get('title') or 
                'Untitled')
        fe.title(title)
        
        url = bookmark.get('content', {}).get('url', '')
        fe.link(href=url)
        
        description = bookmark.get('content', {}).get('description', '')
        if description:
            fe.description(description)
            
        tags = bookmark.get('tags', [])
        if tags:
            tag_names = [tag.get('name', '') for tag in tags] if isinstance(tags[0], dict) else tags
            tag_names = [t for t in tag_names if t]
            if tag_names:
                fe.category(term=','.join(tag_names))

        if 'createdAt' in bookmark:
            date = datetime.strptime(bookmark['createdAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
            date = date.replace(tzinfo=pytz.UTC)
            fe.published(date)
            
        fe.id(bookmark['id'])

    rssfeed = fg.rss_str(pretty=True)
    return Response(rssfeed, mimetype='application/rss+xml')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5034)
