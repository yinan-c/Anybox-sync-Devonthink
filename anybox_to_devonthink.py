#!/usr/bin/env python3

# Modified from Alfred workflow of Anybox:
# https://github.com/anyboxhq/anybox-alfred-workflow

import urllib.request
import sys
import json
import os
import time
from datetime import datetime

# usage: python3 anybox_to_devonthink.py processed_items.json
processed_file_path = sys.argv[1]

# DEVONthink group UUID for bookmarks, can be obtained by copy item link in DEVONthink
Bookmark_group_uuid = os.getenv('Bookmark_database_uuid')
# Anybox API Key in settings
api_key = os.getenv('Anybox_API_Key')
HOME_DIR = os.path.expanduser("~")

show_full_urls = os.getenv('show_full_urls') == '1'
show_dates = os.getenv('show_dates') == '1'
show_tags = os.getenv('show_tags') == '1'
link_descriptions = os.getenv('link_descriptions') == '1'

q = ''


def is_today(date):
    today = datetime.today().replace(tzinfo=date.tzinfo)
    if (today - date).days == 0:
        return True
    else:
        return False

def is_yesteryday(date):
    today = datetime.today().replace(tzinfo=date.tzinfo)
    if (today - date).days == 1:
        return True
    else:
        return False

def less_than_a_week(date):
    today = datetime.today().replace(tzinfo=date.tzinfo)
    if (today - date).days <= 7:
        return True
    else:
        return False

def format_url(url):
    if url.startswith('https://'):
        return url.removeprefix('https://')
    elif url.startswith('http://'):
        return url.removeprefix('http://')
    else:
        return url

# E.g., 2021-12-09T02:40:12Z
def format_date(original):
    date = datetime.strptime(original, "%Y-%m-%dT%H:%M:%S%z")
    tz = datetime.now().astimezone().tzinfo
    if is_today(date):
        return 'Today at ' + date.astimezone(tz).strftime("%H:%M")
    elif is_yesteryday(date):
        return 'Yesterady at ' + date.astimezone(tz).strftime("%H:%M")
    elif less_than_a_week(date):
        return date.astimezone(tz).strftime("%b %d, %Y at %H:%M")
    return date.astimezone(tz).strftime("%b %d, %Y")

def format_subtitle(link):
    subtitle = ''
    date = ''
    if show_dates:
        date = ' • ' + format_date(link['dateLastOpened'])
    if show_full_urls:
        subtitle = format_url(link['url']) + date
    else:
        subtitle = link['host'] + date
    if 'comment' in link and link['comment'] != "":
      subtitle = subtitle + ' • ' + link['comment']
    return subtitle


def download_file(url, folder):
    if not os.path.isdir(folder):
        os.makedirs(folder)
        try:
            urllib.request.urlretrieve(url, folder + '/icon')
        except:
            try:
                urllib.request.urlretrieve(
                    "http://127.0.0.1:6391/images/default-browser-icon.png",
                    folder + '/icon')
            except:
                ()


def throw_error():
  error_feedback = {
    'items': [
      {
        'title': 'It looks like Anybox it’s not running or haven’t installed.',
        'subtitle': 'Press ⏎ to open Anybox or press ⌘ + ⏎ to install Anybox in Mac App Store.',
        'arg': ['anybox://show'],
        'mods': {
          'cmd': {
              'valid': True,
              'arg': 'itms-apps://apps.apple.com/app/id1593408455',
              'subtitle': 'Install Anybox on Mac App Store.'
          },
        }
      }
    ]
  }
  sys.stdout.write(json.dumps(error_feedback))

def get_links():
  headers = {'x-api-key': api_key}
  payload = {
      'q': q,
      'limit': 30,
      'type': 'all' # 'link' (default) | 'note' | 'image' | 'file' | 'all'
  }
  if link_descriptions:
    payload['linkDescriptions'] = 'yes'
  data = urllib.parse.urlencode(payload)
  req = urllib.request.Request('http://127.0.0.1:6391/search?' + data, headers=headers)
  try:
    with urllib.request.urlopen(req) as response:
      list = json.loads(response.read())
      result = []
      for link in list:
        icon_url = 'http://127.0.0.1:6391/images/' + link['id'] + '/icon'
        icon_relative_url = './Link Icons/' + link['id']
        #download_file(icon_url, icon_relative_url)
        url = link['url']
        title = link['title']
        tags = link.get('tags', [])
        description = link.get('description', '')

        markdown_url = '[' + title + ']' + '(' + url + ')'
        anybox_url = 'anybox://document/' + link['id']
        item = {
              'title': title,
              'subtitle': format_subtitle(link),
              'arg': [url, link['id']],
              'tags': tags,
              'description': description,
              'icon': {
                  'path': icon_relative_url + "/icon"
              },
              'text': {
                  'copy': url,
                  'largetype': title
              },
              'mods': {
                  'alt': {
                      'valid': True,
                      'arg': markdown_url,
                      'subtitle': markdown_url
                  },
                  'cmd': {
                      'valid': True,
                      'arg': anybox_url,
                      'subtitle': anybox_url
                  },
                  'shift': {
                      'valid': True,
                      'arg': url,
                      'subtitle': url
                  },
                  
              },
              'quicklookurl': url
          }
        result.append(item)
    #print(json.dumps({'items': result}))
    return result
  except urllib.error.HTTPError as e:
    throw_error()
  except urllib.error.URLError as e:
    throw_error()
import subprocess
import urllib.parse

def add_to_devonthink(item):
    title = item['title']
    url = item['arg'][0]
    uuid = item['arg'][1]
    document_folder = HOME_DIR + f"/Library/Containers/cc.anybox.Anybox/Data/Library/Caches/Documents/{uuid}"
    #print(document_folder)
    # check if there is any file other than the icon in the folder ~/Library/Containers/cc.anybox.Anybox/Data/Library/Caches/Documents/uuid
    if os.path.exists(document_folder):
        files = os.listdir(document_folder)
        if len(files) > 0:
            for file in files:
                if file != 'favicon.png' and file != 'favicon.ico':
                    # copy the file to folder '~/Library/Application Support/DEVONthink 3/Inbox'
                    # tag the file with Anybox then import the file to DEVONthink
                    subprocess.run(["tag", "-a", "Anybox", f"{document_folder}/{file}"], check=True)
                    subprocess.run(['cp', '-r', f"{document_folder}/{file}", HOME_DIR + "/Library/Application Support/DEVONthink 3/Inbox"], check=True)
                    
    tags = item['tags']
    description = item['description']

    encoded_title = urllib.parse.quote(title)
    encoded_url = urllib.parse.quote(url)
    tag_names = [tag['name'] for tag in tags] 
    # add one more tag Anybox
    tag_names.append('Anybox')
    encoded_tags = urllib.parse.quote(','.join(tag_names))
    devonthink_url = f"x-devonthink://createBookmark?title={encoded_title}&location={encoded_url}&tags={encoded_tags}&destination={Bookmark_group_uuid}"

    if description:
        encoded_description = urllib.parse.quote(description)
        devonthink_url += f"&comment={encoded_description}"

    subprocess.run(["open", "-g", devonthink_url], check=True)


def load_processed_items():
    if os.path.exists(processed_file_path):
        with open(processed_file_path, 'r') as file:
            return json.load(file)
    return []

def save_processed_items(items):
    with open(processed_file_path, 'w') as file:
        json.dump(items, file)

def monitor_anybox():
    processed_items = load_processed_items()

    while True:
        links = get_links()
        new_items = [item for item in links if item['arg'][1] not in processed_items]
        if len(new_items) > 0:
            for item in new_items:
                add_to_devonthink(item)
                processed_items.append(item['arg'][1])

        save_processed_items(processed_items)

        time.sleep(300)  # 5 minutes

# Start monitoring Anybox
#print(json.dumps({'items': get_links()}))
monitor_anybox()
