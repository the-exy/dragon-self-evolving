# -*- coding: utf-8 -*-
import sys, time
sys.path.insert(0, r'C:\Tools\QClaw\resources\openclaw\config\skills\browser-cdp\scripts')

from cdp_client import CDPClient
from page_snapshot import PageSnapshot
from browser_actions import BrowserActions

cdp_url = "http://127.0.0.1:28800"
client = CDPClient(cdp_url)
client.connect()

tabs = client.list_tabs()
for t in tabs:
    if 'yqp-crrc' in t['url']:
        client.attach(t['id'])
        break

snapshot = PageSnapshot(client)
actions = BrowserActions(client, snapshot)
time.sleep(2)

# Step 1: 用JS探索Vue router和全局变量
print("=== Step 1: 探索页面JS环境 ===")
result = actions.evaluate("""
(function(){
    // 尝试获取Vue实例
    var vueApp = document.querySelector('#app').__vue_app__;
    var info = {hasVue: !!vueApp};
    
    // 尝试获取路由
    if(vueApp && vueApp.config && vueApp.config.globalProperties) {
        var $router = vueApp.config.globalProperties.$router;
        if($router) {
            info.routerType = $router.constructor.name;
            info.currentRoute = $router.currentRoute ? $router.currentRoute.value : null;
            info.routes = $router.getRoutes ? $router.getRoutes().map(r => r.path) : [];
        }
    }
    
    // 尝试获取页面state
    if(vueApp && vueApp._instance) {
        var comp = vueApp._instance;
        while(comp && !comp.data) comp = comp.parent;
        if(comp && comp.data) {
            try {
                info.stateKeys = Object.keys(comp.data());
            } catch(e) {}
        }
    }
    
    // 打印所有子路由链接
    var links = [];
    document.querySelectorAll('a, [role="button"], button').forEach(el => {
        var href = el.href || el.getAttribute('data-href') || '';
        var text = el.innerText.trim().substring(0, 30);
        if(href || text) links.push({text, href, className: el.className.substring(0,50)});
    });
    info.links = links.slice(0, 30);
    
    return info;
})()
""")
print(result)
print()

# Step 2: 监听网络请求，找API端点
print("=== Step 2: 启动网络监听 ===")
# 启用网络域
client.send('Network.enable', {})
time.sleep(1)

# 清除已有请求
try:
    client.send('Network.clearBrowserCache', {})
except: pass

# 触发一个搜索请求（用搜索框）
tree = snapshot.accessibility_tree(max_chars=2000)
for line in tree.split('\n'):
    if '搜索' in line and '[e' in line:
        ref = line.split('[')[1].split(']')[0]
        print(f"找到搜索框 ref={ref}")
        actions.click_by_ref(ref)
        time.sleep(1)
        break

# 查找搜索/筛选相关的网络请求
requests_info = []

def handle_request(req):
    url = req.get('params', {}).get('request', {}).get('url', '')
    if any(kw in url for kw in ['api', 'yqp', 'crrc', 'list', 'deal', 'bid', 'trade', 'announce']):
        requests_info.append(url)

# 尝试导航到竞价交易页面触发请求
result2 = actions.evaluate("""
(function(){
    // 查找所有iframe和shadow dom
    var iframes = Array.from(document.querySelectorAll('iframe'));
    var frames = [];
    iframes.forEach((f, i) => {
        try {
            var src = f.src;
            frames.push({index: i, src: src, id: f.id, className: f.className});
        } catch(e) {}
    });
    
    // 查找所有script标签的src
    var scripts = Array.from(document.querySelectorAll('script[src]')).map(s => s.src).filter(s => s);
    
    // 查找meta中的api地址
    var metas = Array.from(document.querySelectorAll('meta')).map(m => m.outerHTML).filter(s => s.includes('api') || s.includes('url'));
    
    return {frames, scripts: scripts.slice(0, 20), metas: metas.slice(0, 10),
            baseUrl: window.location.origin,
            href: window.location.href};
})()
""")
print("页面环境信息：")
print(f"  baseUrl: {result2.get('baseUrl')}")
print(f"  href: {result2.get('href')}")
print(f"  iframes: {len(result2.get('frames', []))}")
print(f"  scripts (sample): {result2.get('scripts', [])[:5]}")

# Step 3: 尝试直接导航到各种可能的路由
possible_routes = [
    'https://yqp-crrc.com/yqp-index/#/bidding',
    'https://yqp-crrc.com/yqp-index/#/trading',
    'https://yqp-crrc.com/yqp-index/#/deals',
    'https://yqp-crrc.com/yqp-index/#/completed',
    'https://yqp-crrc.com/yqp-index/#/result',
    'https://yqp-crrc.com/yqp-index/#/deal-list',
    'https://yqp-crrc.com/yqp-index/#/transaction',
    'https://yqp-crrc.com/yqp-index/#/notice-list',
    'https://yqp-crrc.com/yqp-index/#/announcement-list',
    'https://yqp-crrc.com/yqp-index/#/search',
    'https://yqp-crrc.com/yqp-index/#/query',
]

print("\n=== Step 3: 尝试直接导航到可能的路由 ===")
for route in possible_routes:
    actions.navigate(route)
    time.sleep(2)
    url = actions.get_url()
    title = actions.get_title()
    tree_r = snapshot.accessibility_tree(max_chars=500)
    # 检查是否真的到了不同页面
    is_home = '您好，请登录' in tree_r and '增效' in tree_r
    status = "⚠️ 首页重定向" if is_home else "✅ 新页面"
    print(f"{status} {route} -> {url}")
    if not is_home:
        print(f"  标题: {title}")
        print(f"  内容片段: {tree_r[:200]}")
        # 截图
        actions.screenshot(rf'C:\Users\84471\.qclaw\workspace\dragon-self-evolving\notes\yqp_{route.split("#/")[1]}.png')
        print(f"  截图: yqp_{route.split('#/')[1]}.png")

print("\n✅ 探索完成！")
client.close()
