# -*- coding: utf-8 -*-
import sys, time, json
sys.path.insert(0, r'C:\Tools\QClaw\resources\openclaw\config\skills\browser-cdp\scripts')

from cdp_client import CDPClient
from page_snapshot import PageSnapshot
from browser_actions import BrowserActions

cdp_url = "http://127.0.0.1:28800"
client = CDPClient(cdp_url)
client.connect()

for t in client.list_tabs():
    if 'yqp-crrc' in t['url']:
        client.attach(t['id'])
        break

snapshot = PageSnapshot(client)
actions = BrowserActions(client, snapshot)
time.sleep(2)

# Step 1: 直接导航到竞价交易页面
print("导航到竞价交易...")
actions.navigate("https://yqp-crrc.com/yqp-index/#/bidding")
actions.wait_for_load(timeout=15000)
time.sleep(5)
actions.screenshot(r'C:\Users\84471\.qclaw\workspace\dragon-self-evolving\notes\yqp_bidding3.png')
tree = snapshot.accessibility_tree(max_chars=30000)
print(f"URL: {actions.get_url()}")
print(f"Tree长度: {len(tree)}")
print(f"\n=== 竞价交易页内容（前8000字）===")
print(tree[:8000])

# Step 2: 找竞价结束列表
print("\n\n=== 找竞价结束列表入口 ===")
lines = tree.split('\n')
for i, line in enumerate(lines):
    if '竞价结束' in line or '竞价中' in line or '成交' in line or '结束' in line:
        start = max(0, i-2)
        end = min(len(lines), i+5)
        print('\n'.join(f"  {j}: {lines[j]}" for j in range(start, end)))
        print("---")

# Step 3: 点击"更多(76979)"找完整列表
for line in lines:
    if '更多' in line and '[e' in line:
        ref = line.split('[')[1].split(']')[0]
        print(f"\n点击 ref={ref} ({line.strip()})")
        actions.click_by_ref(ref)
        time.sleep(5)
        actions.screenshot(r'C:\Users\84471\.qclaw\workspace\dragon-self-evolving\notes\yqp_deal_list.png')
        print(f"URL: {actions.get_url()}")
        tree2 = snapshot.accessibility_tree(max_chars=50000)
        print(f"\n=== 竞价结束列表页（前10000字）===")
        print(tree2[:10000])
        break

client.close()
