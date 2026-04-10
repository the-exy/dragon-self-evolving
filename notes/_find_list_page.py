# -*- coding: utf-8 -*-
import sys, time
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

# 去竞价交易页面
print("导航到竞价交易...")
actions.navigate("https://yqp-crrc.com/yqp-index/#/home")
actions.wait_for_load(timeout=15000)
time.sleep(3)

# 点击竞价交易按钮
tree = snapshot.accessibility_tree(max_chars=3000)
for line in tree.split('\n'):
    if '竞价交易' in line and '[e' in line:
        ref = line.split('[')[1].split(']')[0]
        print(f"点击竞价交易 ref={ref}")
        actions.click_by_ref(ref)
        time.sleep(4)
        break

# 截图确认当前页面
actions.screenshot(r'C:\Users\84471\.qclaw\workspace\dragon-self-evolving\notes\yqp_bidding2.png')
print(f"当前URL: {actions.get_url()}")

# 完整获取页面结构
tree2 = snapshot.accessibility_tree(max_chars=50000)
print(f"\n=== 竞价交易页面结构 (前15000字) ===")
print(tree2[:15000])

# 截图看看这个页面
actions.screenshot(r'C:\Users\84471\.qclaw\workspace\dragon-self-evolving\notes\yqp_bidding_full.png')
print("\n截图: yqp_bidding_full.png")

client.close()
