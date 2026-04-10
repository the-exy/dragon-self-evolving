# -*- coding: utf-8 -*-
import sys, json, importlib.util
sys.path.insert(0, r'C:\Tools\QClaw\resources\openclaw\config\skills\browser-cdp\scripts')

from cdp_client import CDPClient

cdp_url = "http://127.0.0.1:28800"
client = CDPClient(cdp_url)
client.connect()
print("Connected! Listing tabs:")
tabs = client.list_tabs()
for t in tabs:
    print(f"  [{t['id']}] {t['title']} - {t['url']}")

# Create new tab and navigate
print("\nNavigating to target URL...")
tab = client.create_tab("https://yqp-crrc.com/yqp-index/#/home")
client.attach(tab['id'])
print(f"Tab created: {tab['id']}")

import time
time.sleep(5)  # Wait for SPA to load

# Get page info
from page_snapshot import PageSnapshot
from browser_actions import BrowserActions
snapshot = PageSnapshot(client)
actions = BrowserActions(client, snapshot)

actions.wait_for_load(timeout=10000)
print(f"Current URL: {actions.get_url()}")
print(f"Title: {actions.get_title()}")

# Get accessibility tree
tree = snapshot.accessibility_tree(max_chars=60000)
print(f"\n=== Accessibility Tree (first 15000 chars) ===")
print(tree[:15000])

client.close()
