# Anybox Sync to DEVONthink 

This Python script is a one-way sync from documents and links (with its archive and downloaded) in Anybox to DEVONthink.
It automatically tags all synced file with `Anybox` and importing into DEVONthink.

## Prerequisites

- `tag` command-line tool (Install via Homebrew with `brew install tag`)

## Configuration

Set the following environment variables:

- Anybox_API_Key: Your Anybox API key.
- Bookmark_database_uuid: UUID for the DEVONthink group where bookmarks should be saved.

## Usage
This script aims to run in the background and sync every 5 minutes. 

You can export those env vars and add the run commands in `~/.zshrc` like this:

In ~/.zshrc:
```
export Anybox_API_Key="xxx"
export Bookmark_database_uuid='yyy'

if ! pgrep -f 'anybox_to_devonthink.py' > /dev/null; then
    nohup paht/to/script/anybox_to_devonthink.py paht/to/log/processed_items.json > /path/to/log/anybox_to_devonthink_nohup.log 2>&1 &
fi
```

## Note

This script does not aim to exporting all documents and links from Anybox to DEVONthink, but for syncing recently added items only.



