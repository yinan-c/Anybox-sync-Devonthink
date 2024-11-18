#!/usr/bin/env python3

from flask import Flask, Response
from feedgen.feed import FeedGenerator
import urllib.request
import json
import os
import time
from datetime import datetime
import pytz

app = Flask(__name__)

api_key = os.getenv('Anybox_API_Key')

def get_links():
    headers = {'x-api-key': api_key}
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
    except:
        return []

@app.route('/rss')
def rss():
    fg = FeedGenerator()
    fg.title('Anybox Links')
    fg.description('RSS feed of Anybox links')
    fg.link(href='http://localhost:5033/rss')
    fg.language('en')

    links = get_links()
    
    for link in links:
        fe = fg.add_entry()
        fe.title(link['title'])
        fe.link(href=link['url'])
        
        description = link.get('description', '')
        if description:
            fe.description(description)
            
        tags = link.get('tags', [])
        if tags:
            tag_names = [tag['name'] for tag in tags]
            fe.category(term=','.join(tag_names))
            
        if 'dateLastOpened' in link:
            date = datetime.strptime(link['dateLastOpened'], "%Y-%m-%dT%H:%M:%S%z")
            fe.published(date)
            
        fe.id(link['id'])

    rssfeed = fg.rss_str(pretty=True)
    return Response(rssfeed, mimetype='application/rss+xml')

if __name__ == '__main__':
    # 运行服务器在5033端口，监听所有网络接口
    app.run(host='0.0.0.0', port=5033)

