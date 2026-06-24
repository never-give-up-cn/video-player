#!/usr/bin/env python3
"""
缩略图生成进度监控器 v2
实时显示 ffmpeg 缩略图生成进度，支持停止/开始/删除缩略图
用法: python thumbnail_monitor.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import time
import os

API_BASE = 'http://localhost:3000'
PROGRESS_URL = f'{API_BASE}/api/thumbnail-progress'
STOP_URL = f'{API_BASE}/api/thumbnail/stop'
START_URL = f'{API_BASE}/api/thumbnail/start'
DELETE_URL = f'{API_BASE}/api/thumbnails'
POLL_INTERVAL = 1


class ThumbnailMonitor:
    bg = '#0d1117'
    fg = '#e6edf3'
    accent = '#58a6ff'
    green = '#3fb950'
    orange = '#d29922'
    red = '#f85149'
    card_bg = '#161b22'
    border = '#30363d'

    def __init__(self, root):
        self.root = root
        self.root.title('缩略图生成进度 v2')
        self.root.geometry('720x620+300+200')
        self.root.configure(bg=self.bg)
        self.root.resizable(False, False)
        self._build_ui()
        self.running = True
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

    def _build_ui(self):
        # ==== Header ====
        header = tk.Frame(self.root, bg=self.bg)
        header.pack(fill='x', padx=16, pady=(12, 0))
        tk.Label(header, text='🖼️  缩略图生成进度',
                 font=('Microsoft YaHei', 16, 'bold'),
                 bg=self.bg, fg=self.fg).pack(side='left')

        # Buttons
        btn_frame = tk.Frame(header, bg=self.bg)
        btn_frame.pack(side='right')

        self.btn_stop = tk.Button(btn_frame, text='⏹ 停止', command=self._stop,
                                  bg=self.card_bg, fg=self.red,
                                  font=('Microsoft YaHei', 9),
                                  relief='flat', padx=10, cursor='hand2',
                                  activebackground='#21262d')
        self.btn_stop.pack(side='left', padx=2)

        self.btn_start = tk.Button(btn_frame, text='▶ 开始', command=self._start,
                                   bg=self.card_bg, fg=self.green,
                                   font=('Microsoft YaHei', 9),
                                   relief='flat', padx=10, cursor='hand2',
                                   activebackground='#21262d')
        self.btn_start.pack(side='left', padx=2)

        self.btn_delete = tk.Button(btn_frame, text='🗑 删除缩略图', command=self._delete,
                                    bg=self.card_bg, fg=self.orange,
                                    font=('Microsoft YaHei', 9),
                                    relief='flat', padx=10, cursor='hand2',
                                    activebackground='#21262d')
        self.btn_delete.pack(side='left', padx=2)

        self.status_label = tk.Label(self.root, text='连接中...',
                                     font=('Microsoft YaHei', 11),
                                     bg=self.bg, fg=self.accent)
        self.status_label.pack(anchor='w', padx=16, pady=(4, 0))

        # ==== Progress bar ====
        bar_frame = tk.Frame(self.root, bg=self.bg)
        bar_frame.pack(fill='x', padx=16, pady=(8, 2))

        self.progress = ttk.Progressbar(bar_frame, length=688, mode='determinate')
        self.progress.pack(fill='x')
        self.percent_label = tk.Label(bar_frame, text='0%',
                                      font=('Consolas', 10),
                                      bg=self.bg, fg=self.fg)
        self.percent_label.pack(anchor='e')

        # ==== Stats card ====
        stats = tk.Frame(self.root, bg=self.card_bg, highlightbackground=self.border, highlightthickness=1)
        stats.pack(fill='x', padx=16, pady=(4, 4))

        row0 = tk.Frame(stats, bg=self.card_bg)
        row0.pack(fill='x', padx=12, pady=(8, 2))
        self._stat_item(row0, '已完成', '0', self.green, side='left')
        self._stat_item(row0, '失败', '0', self.red, side='left')
        self._stat_item(row0, '剩余', '0', self.orange, side='left')
        self._stat_item(row0, '总计', '0', self.fg, side='right')

        row1 = tk.Frame(stats, bg=self.card_bg)
        row1.pack(fill='x', padx=12, pady=(0, 8))
        self._stat_item(row1, '耗时', '0s', self.accent, side='left')
        self._stat_item(row1, '并发', '0', self.fg, side='left')

        # ==== Bottom panes ====
        bottom = tk.Frame(self.root, bg=self.bg)
        bottom.pack(fill='both', padx=16, pady=(4, 12), expand=True)

        # Left: Current files
        left = tk.Frame(bottom, bg=self.bg)
        left.pack(side='left', fill='both', expand=True)

        tk.Label(left, text='正在处理:',
                 font=('Microsoft YaHei', 10, 'bold'),
                 bg=self.bg, fg=self.fg).pack(anchor='w')

        self.current_list = tk.Listbox(left, height=6,
                                       bg=self.card_bg, fg=self.fg,
                                       selectbackground=self.accent,
                                       font=('Consolas', 9),
                                       borderwidth=0, highlightthickness=1,
                                       highlightbackground=self.border, relief='flat')
        self.current_list.pack(fill='both', pady=(2, 6), expand=True)

        # Middle: Recent completed
        mid = tk.Frame(bottom, bg=self.bg)
        mid.pack(side='left', fill='both', expand=True, padx=(6, 0))

        tk.Label(mid, text='最近完成:',
                 font=('Microsoft YaHei', 10, 'bold'),
                 bg=self.bg, fg=self.fg).pack(anchor='w')

        self.completed_list = tk.Listbox(mid, height=6,
                                         bg=self.card_bg, fg=self.green,
                                         selectbackground=self.accent,
                                         font=('Consolas', 9),
                                         borderwidth=0, highlightthickness=1,
                                         highlightbackground=self.border, relief='flat')
        self.completed_list.pack(fill='both', pady=(2, 6), expand=True)

        # Right: Failed
        right = tk.Frame(bottom, bg=self.bg)
        right.pack(side='left', fill='both', expand=True, padx=(6, 0))

        tk.Label(right, text='失败列表:',
                 font=('Microsoft YaHei', 10, 'bold'),
                 bg=self.bg, fg=self.fg).pack(anchor='w')

        self.failed_list = tk.Listbox(right, height=6,
                                      bg=self.card_bg, fg=self.red,
                                      selectbackground=self.accent,
                                      font=('Consolas', 9),
                                      borderwidth=0, highlightthickness=1,
                                      highlightbackground=self.border, relief='flat')
        self.failed_list.pack(fill='both', pady=(2, 6), expand=True)

        # Initial button state
        self.btn_stop.config(state='disabled')
        self.btn_start.config(state='disabled')

    def _stat_item(self, parent, label, value, color, side='left'):
        frame = tk.Frame(parent, bg=self.card_bg)
        frame.pack(side=side, padx=(0, 24))
        tk.Label(frame, text=label, font=('Microsoft YaHei', 9),
                 bg=self.card_bg, fg='#8b949e').pack(anchor='w')
        lbl = tk.Label(frame, text=value, font=('Consolas', 13, 'bold'),
                       bg=self.card_bg, fg=color)
        lbl.pack(anchor='w')
        setattr(self, f'stat_{label}', lbl)

    # ---- Button handlers ----

    def _stop(self):
        def task():
            try:
                requests.post(STOP_URL, timeout=5)
                self.root.after(0, lambda: self.status_label.config(
                    text='⏹ 已停止', fg=self.red))
            except requests.RequestException as e:
                self.root.after(0, lambda: self.status_label.config(
                    text=f'停止失败: {e}', fg=self.red))
        threading.Thread(target=task, daemon=True).start()

    def _start(self):
        def task():
            try:
                requests.post(START_URL, timeout=5)
                self.root.after(0, lambda: self.status_label.config(
                    text='▶ 启动中...', fg=self.green))
            except requests.RequestException as e:
                self.root.after(0, lambda: self.status_label.config(
                    text=f'启动失败: {e}', fg=self.red))
        threading.Thread(target=task, daemon=True).start()

    def _delete(self):
        if not messagebox.askyesno('确认删除', '确定要删除所有缩略图缓存吗？\n此操作不可撤销！',
                                   icon='warning', default='no'):
            return
        def task():
            try:
                requests.delete(DELETE_URL, timeout=10)
                self.root.after(0, lambda: self.status_label.config(
                    text='🗑 缩略图已全部删除', fg=self.orange))
            except requests.RequestException as e:
                self.root.after(0, lambda: self.status_label.config(
                    text=f'删除失败: {e}', fg=self.red))
        threading.Thread(target=task, daemon=True).start()

    # ---- Polling ----

    def _poll_loop(self):
        while self.running:
            try:
                r = requests.get(PROGRESS_URL, timeout=3)
                data = r.json().get('data', {})
                self.root.after(0, self._update_ui, data)
            except requests.RequestException:
                self.root.after(0, self._set_offline)
            except Exception:
                pass
            time.sleep(POLL_INTERVAL)

    def _update_ui(self, data):
        status = data.get('status', 'idle')
        total = data.get('total', 0)
        completed = data.get('completed', 0)
        failed = data.get('failed', 0)
        remaining = data.get('remaining', 0)
        current_files = data.get('currentFiles', [])
        recent_completed = data.get('recentCompleted', [])
        failed_files = data.get('failedFiles', [])
        elapsed_ms = data.get('elapsed', 0)
        concurrency = data.get('concurrency', 0)

        elapsed_s = elapsed_ms // 1000
        elapsed_str = (f'{elapsed_s // 60}m {elapsed_s % 60}s' if elapsed_s >= 60
                       else f'{elapsed_s}s')

        # Status & buttons
        is_generating = (status == 'generating')
        self.btn_stop.config(state='normal' if is_generating else 'disabled')
        self.btn_start.config(state='disabled' if is_generating else 'normal')

        if status == 'idle':
            self.status_label.config(text='空闲 - 点击 ▶ 开始 生成缩略图', fg=self.accent)
            self.btn_start.config(state='normal')
        elif status == 'generating':
            pct = (completed / total * 100) if total > 0 else 0
            self.progress['value'] = pct
            self.percent_label.config(text=f'{pct:.1f}%')
            self.status_label.config(text=f'⏳ 生成中... 并发 {len(current_files) if current_files else concurrency}',
                                     fg=self.orange)
        elif status == 'done':
            self.progress['value'] = 100
            self.percent_label.config(text='100%')
            self.status_label.config(text='✅ 全部生成完成' if failed == 0 else f'✅ 生成完成（{failed} 个失败）',
                                     fg=self.green if failed == 0 else self.orange)
        elif status == 'stopped':
            self.status_label.config(text=f'⏸ 已暂停（已完成 {completed}，失败 {failed}）',
                                     fg=self.red)
            self.btn_start.config(state='normal')

        self.stat_已完成.config(text=str(completed))
        self.stat_失败.config(text=str(failed))
        self.stat_剩余.config(text=str(remaining))
        self.stat_总计.config(text=str(total))
        self.stat_耗时.config(text=elapsed_str)
        self.stat_并发.config(text=str(concurrency))

        # Current files
        self.current_list.delete(0, 'end')
        if current_files:
            for f in current_files[:8]:
                display = f if len(f) <= 55 else f'...{f[-52:]}'
                self.current_list.insert('end', f'  📹  {display}')
        else:
            self.current_list.insert('end', '  (无)')

        # Recent completed
        self.completed_list.delete(0, 'end')
        if recent_completed:
            for item in recent_completed[-10:]:
                f = item.get('file', '')
                t = item.get('time', '')
                display = f if len(f) <= 40 else f'...{f[-37:]}'
                self.completed_list.insert('end', f'  ✅ {display}')
        else:
            self.completed_list.insert('end', '  (无)')

        # Failed
        self.failed_list.delete(0, 'end')
        if failed_files:
            for f in failed_files[-10:]:
                display = f if len(f) <= 45 else f'...{f[-42:]}'
                self.failed_list.insert('end', f'  ❌ {display}')
        else:
            self.failed_list.insert('end', '  (无)')

    def _set_offline(self):
        self.status_label.config(text='❌ 无法连接服务器 (localhost:3000)', fg=self.red)
        self.btn_stop.config(state='disabled')
        self.btn_start.config(state='disabled')

    def _on_close(self):
        self.running = False
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        ThumbnailMonitor(root)
        root.mainloop()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
