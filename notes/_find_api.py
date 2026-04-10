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

print("=== Step 1: JS探索Router和API配置 ===")
js_result = actions.evaluate("""
(function(){
    var app = document.querySelector('#app');
    var info = {href: window.location.href, hash: window.location.hash};
    
    // 找Vue实例
    try { info.vue = !!app.__vue__; } catch(e) { info.vue = false; }
    
    // 找$router实例
    try {
        var vue = app.__vue__;
        while(vue && !vue.$router) vue = vue.$parent;
        if(vue && vue.$router) {
            info.router = {
                current: vue.$router.currentRoute ? vue.$router.currentRoute.value.path : vue.$router.current ? vue.$router.current.path : '?',
                routes: vue.$router.getRoutes ? vue.$router.getRoutes().map(r => r.path) : []
            };
        }
    } catch(e) { info.routerError = e.message; }
    
    // 找API baseURL
    try {
        // 查找window上的API配置
        var cfgKeys = ['BASE_URL', 'VUE_APP_API', 'API_BASE', 'VUE_APP_BASE_API'];
        cfgKeys.forEach(function(k) {
            if(window[k]) info[k] = window[k];
        });
        // 查找script中的配置
        var scripts = Array.from(document.querySelectorAll('script'));
        scripts.forEach(function(s) {
            if(s.innerText && s.innerText.includes('baseURL')) {
                var match = s.innerText.match(/baseURL["']?\s*[:=]\s*["']([^"']+)["']/);
                if(match) info.baseURL_script = match[1];
            }
        });
    } catch(e) {}
    
    // 找meta中的API配置
    var metas = Array.from(document.querySelectorAll('meta'));
    metas.forEach(function(m) {
        var html = m.outerHTML;
        if(html.includes('api') || html.includes('base')) {
            info.meta = html;
        }
    });
    
    // 直接尝试导航
    window.location.hash = '#/bidding';
    return info;
})()
""")
print(json.dumps(js_result, ensure_ascii=False, indent=2))
time.sleep(3)
print(f"URL after JS hash change: {actions.get_url()}")

# 尝试拦截CDP Network请求
print("\n=== Step 2: 启用CDP Network监听 ===")
try:
    # CDP原生方式：用send+waitFor方法
    client.send('Network.enable', {})
    print("Network域已启用")
except Exception as e:
    print(f"Network启用失败: {e}")

# 触发搜索操作，看网络请求
print("\n=== Step 3: 在搜索框输入关键词触发请求 ===")
tree = snapshot.accessibility_tree(max_chars=2000)
for line in tree.split('\n'):
    if '请输入' in line and '[e' in line:
        ref = line.split('[')[1].split(']')[0]
        print(f"找到搜索框 ref={ref}，输入关键词...")
        actions.click_by_ref(ref)
        time.sleep(1)
        # 输入后按回车搜索
        actions.press_key('Control+a')
        time.sleep(0.5)
        actions.press_key('Backspace')
        time.sleep(0.5)
        actions.type_text('废钢', submit=True)
        time.sleep(5)
        print(f"URL after search: {actions.get_url()}")
        
        tree3 = snapshot.accessibility_tree(max_chars=5000)
        print(f"\n=== 搜索结果 ===\n{tree3[:3000]}")
        break

# 截图
actions.screenshot(r'C:\Users\84471\.qclaw\workspace\dragon-self-evolving\notes\yqp_search_result.png')

print("\n✅ API探索完成！")
client.close()
