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

actions = BrowserActions(client, None)
snapshot = PageSnapshot(client)

# 启用网络请求拦截
client.send('Network.enable', {})

captured_requests = []
captured_responses = []

def handle_request(req):
    url = req.get('params', {}).get('request', {}).get('url', '')
    if url and any(kw in url.lower() for kw in ['api', 'yqp', 'list', 'deal', 'trade', 'notice', 'announce', 'result', 'query', 'search']):
        captured_requests.append(url)
        print(f"[请求] {url[:120]}")

def handle_response(resp):
    url = resp.get('params', {}).get('response', {}).get('url', '')
    if url and any(kw in url.lower() for kw in ['api', 'yqp', 'list', 'deal', 'trade', 'notice', 'announce']):
        status = resp.get('params', {}).get('response', {}).get('status', '')
        print(f"[响应] {status} {url[:100]}")

# 注册事件
client._ws.emit('Network.requestWillBeSent', handle_request)
try:
    client._ws.emit('Network.responseReceived', handle_response)
except: pass

# 用JS探索Router并触发导航
print("\n=== 用JS探索Router ===")
js_result = actions.evaluate("""
(function(){
    // 找Vue/Element组件实例
    var app = document.querySelector('#app');
    var info = {
        href: window.location.href,
        hash: window.location.hash,
        pathname: window.location.pathname
    };
    
    // 尝试通过Bus/EventEmitter导航
    // ElementUI使用Vue.prototype.$bus
    var children = app.children;
    info.childCount = children.length;
    info.childTags = Array.from(children).map(c => c.tagName + '.' + c.className.substring(0,30));
    
    // 查找所有可能包含router的对象
    var keys = ['$router', '$route', 'router', 'VueRouter'];
    var found = {};
    keys.forEach(function(k) {
        try {
            var v = eval(k);
            if(v) found[k] = typeof v === 'object' ? JSON.stringify(v).substring(0,100) : String(v).substring(0,100);
        } catch(e) {}
    });
    info.foundKeys = found;
    
    // 尝试直接修改hash触发路由
    window.location.hash = '#/bidding';
    setTimeout(function(){}, 500);
    
    // 获取router实例 - 尝试多种方式
    var routerMatch = null;
    try {
        var vm = app.__vue__;
        if(vm && vm.$router) routerMatch = {found: 'app.__vue__.$router', current: vm.$router.currentRoute ? vm.$router.currentRoute.path : '?'};
    } catch(e) {}
    
    return info;
})()
""")
print(f"JS探索结果: {json.dumps(js_result, ensure_ascii=False, indent=2)}")

time.sleep(2)
print(f"\n当前URL: {actions.get_url()}")

# 启用Network监听后触发几个请求，看API端点
print("\n=== 触发网络请求 ===")
tree = snapshot.accessibility_tree(max_chars=2000)
for line in tree.split('\n'):
    if '更多(76979)' in line and '[e' in line:
        ref = line.split('[')[1].split(']')[0]
        print(f"点击'竞价结束-更多' ref={ref}")
        actions.click_by_ref(ref)
        time.sleep(5)
        break

print(f"\n当前URL: {actions.get_url()}")

# 再次获取网络请求
print("\n=== 监听网络请求结果 ===")
if captured_requests:
    print(f"捕获到 {len(captured_requests)} 个相关请求:")
    for r in captured_requests[:20]:
        print(f"  {r[:150]}")
else:
    print("没有捕获到API请求，尝试用JS获取")

# 尝试JS获取axios/fetch配置
api_result = actions.evaluate("""
(function(){
    // 找API基础配置
    var result = {urls: []};
    
    // 找axios实例
    if(window.axios) result.axiosisInstalled = true;
    
    // 找所有配置好的API baseURL
    var scripts = Array.from(document.querySelectorAll('script'));
    var mainScript = null;
    scripts.forEach(function(s) {
        if(s.src && s.src.includes('chunk-') && !s.src.includes('commons')) {
            mainScript = s.src;
        }
    });
    result.mainScript = mainScript;
    
    // 尝试获取$http配置（部分项目使用vue-resource）
    try {
        var vm = document.querySelector('#app').__vue__;
        if(vm && vm.$http) {
            result.$http = vm.$http.defaults ? vm.$http.defaults.baseURL : 'found';
        }
    } catch(e) {}
    
    // 找包含API URL的meta标签
    var metas = Array.from(document.querySelectorAll('meta'));
    metas.forEach(function(m) {
        var content = m.content || '';
        if(content.includes('api') || content.includes('url')) {
            result.urls.push(m.outerHTML);
        }
    });
    
    // 找包含baseURL配置
    try {
        var cfg = JSON.stringify(window).match(/"baseURL"[^,}]+/);
        if(cfg) result.baseURL = cfg[0];
    } catch(e) {}
    
    return result;
})()
""")
print(f"API探索: {json.dumps(api_result, ensure_ascii=False, indent=2)}")

# 尝试直接调用搜索功能，输入"竞价结束"作为关键词
print("\n=== 尝试使用搜索功能 ===")
tree2 = snapshot.accessibility_tree(max_chars=3000)
for line in tree2.split('\n'):
    if '请输入' in line and '[e' in line:
        ref = line.split('[')[1].split(']')[0]
        print(f"找到搜索框 ref={ref}")
        actions.click_by_ref(ref)
        time.sleep(1)
        actions.type_text('废钢', submit=True)
        time.sleep(5)
        print(f"URL after search: {actions.get_url()}")
        # 获取搜索结果
        tree3 = snapshot.accessibility_tree(max_chars=10000)
        print(f"\n=== 搜索结果片段 ===\n{tree3[:3000]}")
        break

client.close()
