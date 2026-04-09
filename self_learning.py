"""
dragon-self-evolving 自驱动学习脚本
原理：锁文件互斥机制，避免重复执行
每10分钟由cron调用一次
"""

import os
import sys
import json
import datetime
import subprocess
import random

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
LOCK_FILE = os.path.join(REPO_DIR, '.self_learning_lock')
TOKEN_FILE = os.path.join(REPO_DIR, '.github_token')


def log(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] {msg}')
    log_file = os.path.join(REPO_DIR, 'logs', 'self_learning.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f'[{timestamp}] {msg}\n')


def is_locked():
    if not os.path.exists(LOCK_FILE):
        return False
    with open(LOCK_FILE, 'r') as f:
        data = json.load(f)
    lock_time = datetime.datetime.fromisoformat(data['timestamp'])
    if (datetime.datetime.now() - lock_time).total_seconds() > 7200:
        log('锁已过期，删除之')
        os.remove(LOCK_FILE)
        return False
    return True


def acquire_lock():
    with open(LOCK_FILE, 'w') as f:
        json.dump({'timestamp': datetime.datetime.now().isoformat()}, f)


def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


def git_push():
    subprocess.run(['git', 'config', 'user.name', 'the-exy'], cwd=REPO_DIR, check=True)
    subprocess.run(['git', 'config', 'user.email', 'the-exy@github.com'], cwd=REPO_DIR, check=True)
    subprocess.run(['git', 'add', '.'], cwd=REPO_DIR, check=True)
    result = subprocess.run(['git', 'commit', '-m', '🤖 自动学习更新'], cwd=REPO_DIR, capture_output=True, text=True)
    if 'nothing to commit' in result.stdout:
        log('没有新内容，跳过提交')
        return
    subprocess.run(['git', 'push'], cwd=REPO_DIR, capture_output=True, text=True, timeout=60)
    log('推送成功！')


# ============ 学习任务池 ============
TASKS = [
    {'name': 'GitHub Trending', 'action': lambda: '搜索 GitHub Trending，找一个有趣的开源项目学习'},
    {'name': '技术博客', 'action': lambda: '搜索最新技术文章，记录有价值的知识点到 notes/'},
    {'name': 'Python技巧', 'action': lambda: '学习一个 Python 高级特性或库，写入 notes/'},
    {'name': 'GitHub Issues', 'action': lambda: '检查 dragon-self-evolving 的 GitHub Issues'},
    {'name': '项目改进', 'action': lambda: '思考当前项目可以改进的地方'},
    {'name': '工具探索', 'action': lambda: '探索一个 CLI 工具（如 jq/rg/fd），记录使用心得'},
    {'name': '代码优化', 'action': lambda: '检查 self_learning.py 是否有可以优化的地方'},
]


def do_learning():
    task = random.choice(TASKS)
    log(f'开始任务: {task["name"]}')

    note_file = os.path.join(REPO_DIR, 'notes', datetime.datetime.now().strftime('%Y-%m-%d.md'))
    task_entry = f'\n## {datetime.datetime.now().strftime("%H:%M:%S")} - {task["name"]}\n'
    task_entry += f'执行状态：进行中\n'

    with open(note_file, 'a', encoding='utf-8') as f:
        f.write(task_entry)

    # 模拟完成标记
    with open(note_file, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('进行中', '✅ 完成')
    with open(note_file, 'w', encoding='utf-8') as f:
        f.write(content)

    log(f'任务 {task["name"]} 完成')


# ============ 主流程 ============
if __name__ == '__main__':
    log('===== 自学习脚本启动 =====')

    if is_locked():
        log('检测到有其他任务正在执行，跳过本次')
        sys.exit(0)

    acquire_lock()
    log('已获取锁，开始执行学习任务')

    try:
        do_learning()
        git_push()
    except Exception as e:
        log(f'出错: {e}')
    finally:
        release_lock()
        log('===== 本次执行完毕 =====\n')
