"""
dragon-self-evolving 每小时总结脚本
每60分钟执行一次，汇总本小时的学习成果
"""

import os
import datetime

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
SUMMARY_FILE = os.path.join(REPO_DIR, 'notes', 'hourly_summary.md')
TODAY_NOTE = os.path.join(REPO_DIR, 'notes', datetime.datetime.now().strftime('%Y-%m-%d.md'))


def log(msg):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{ts}] {msg}')
    log_file = os.path.join(REPO_DIR, 'logs', 'hourly_summary.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f'[{ts}] {msg}\n')


def generate_summary():
    if not os.path.exists(TODAY_NOTE):
        log('今日笔记为空，跳过总结')
        return

    with open(TODAY_NOTE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取本小时的记录
    now = datetime.datetime.now()
    hour_label = now.strftime('%Y-%m-%d %H:00')
    lines = content.split('\n')
    hour_lines = []
    in_hour = False
    for line in lines:
        if hour_label in line:
            in_hour = True
        if in_hour:
            hour_lines.append(line)
        if in_hour and line.startswith('## ') and hour_label not in line:
            break

    if not hour_lines:
        log('本小时无新记录，跳过总结')
        return

    tasks = [l for l in hour_lines if l.strip().startswith('-')]
    summary_text = '\n'.join(hour_lines)

    # 写入总结
    summary_header = f'\n---\n## 📊 {hour_label} ~ {now.strftime("%H:59")} 学习总结\n'
    summary_header += f'**生成时间：** {now.strftime("%Y-%m-%d %H:%M:%S")}\n'
    summary_header += f'**完成任务数：** {len(tasks)} 项\n\n'

    with open(SUMMARY_FILE, 'a', encoding='utf-8') as f:
        f.write(summary_header)
        f.write(summary_text + '\n\n')

    log(f'总结生成成功！本小时完成 {len(tasks)} 项任务')


if __name__ == '__main__':
    log('===== 每小时总结开始 =====')
    generate_summary()
    log('===== 总结完毕 =====\n')
