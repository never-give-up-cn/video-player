#!/usr/bin/env python3
"""
缩略图生成进度监控器 v3
实时显示每个视频的生成状态 + 控制按钮
用法: python thumbnail_monitor.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import time

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
        self.root.title('缩略图生成进度 v3')
        self.root.geometry('780x700+300+100')
        self.root.configure(bg=self.bg)
        self.root.resizable(False, False)
        self._build_ui()
        self.running = True
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

    def _build_ui(self):
        # ====== Header ======
        header = tk.Frame(self.root, bg=self.bg)
        header.pack(fill='x', padx=16, pady=(12, 0))

        tk.Label(header, text='🖼️  缩略图生成进度',
                 font=('Microsoft YaHei', 16, 'bold'),
                 bg=self.bg, fg=self.fg).pack(side='left')

        btn_frame = tk.Frame(header, bg=self.bg)
        btn_frame.pack(side='right')

        self.btn_stop = tk.Button(btn_frame, text='⏹ 停止', command=self._stop,
                                  bg=self.card_bg, fg=self.red,
                                  font=('Microsoft YaHei', 9), relief='flat',
                                  padx=10, cursor='hand2', activebackground='#21262d')
        self.btn_stop.pack(side='left', padx=2)

        self.btn_start = tk.Button(btn_frame, text='▶ 开始', command=self._start,
                                   bg=self.card_bg, fg=self.green,
                                   font=('Microsoft YaHei', 9), relief='flat',
                                   padx=10, cursor='hand2', activebackground='#21262d')
        self.btn_start.pack(side='left', padx=2)

        self.btn_delete = tk.Button(btn_frame, text='🗑 删除缩略图', command=self._delete,
                                    bg=self.card_bg, fg=self.orange,
                                    font=('Microsoft YaHei', 9), relief='flat',
                                    padx=10, cursor='hand2', activebackground='#21262d')
        self.btn_delete.pack(side='left', padx=2)

        # ====== Status ======
        self.status_label = tk.Label(self.root, text='连接中...',
                                     font=('Microsoft YaHei', 11),
                                     bg=self.bg, fg=self.accent)
        self.status_label.pack(anchor='w', padx=16, pady=(4, 0))

        # ====== Progress bar ======
        bar_frame = tk.Frame(self.root, bg=self.bg)
        bar_frame.pack(fill='x', padx=16, pady=(8, 2))
        self.progress = ttk.Progressbar(bar_frame, length=748, mode='determinate')
        self.progress.pack(fill='x')
        self.percent_label = tk.Label(bar_frame, text='0%',
                                      font=('Consolas', 10), bg=self.bg, fg=self.fg)
        self.percent_label.pack(anchor='e')

        # ====== Stats ======
        stats = tk.Frame(self.root, bg=self.card_bg, highlightbackground=self.border, highlightthickness=1)
        stats.pack(fill='x', padx=16, pady=(4, 6))

        row0 = tk.Frame(stats, bg=self.card_bg)
        row0.pack(fill='x', padx=12, pady=(6, 2))
        self._stat_item(row0, '已完成', '0', self.green, 'left')
        self._stat_item(row0, '失败', '0', self.red, 'left')
        self._stat_item(row0, '剩余', '0', self.orange, 'left')
        self._stat_item(row0, '总计', '0', self.fg, 'right')

        row1 = tk.Frame(stats, bg=self.card_bg)
        row1.pack(fill='x', padx=12, pady=(0, 6))
        self._stat_item(row1, '耗时', '0s', self.accent, 'left')
        self._stat_item(row1, '并发', '0', self.fg, 'left')

        # ====== Three-column video panels ======
        panels = tk.Frame(self.root, bg=self.bg)
        panels.pack(fill='both', padx=16, pady=(4, 12), expand=True)

        # -- 生成中 (left) --
        left = tk.Frame(panels, bg=self.card_bg, highlightbackground=self.border, highlightthickness=1)
        left.pack(side='left', fill='both', expand=True)
        tk.Label(left, text='🎬 生成中',
                 font=('Microsoft YaHei', 10, 'bold'),
                 bg=self.card_bg, fg=self.orange).pack(anchor='w', padx=8, pady=(6, 2))
        tk.Frame(left, bg=self.border, height=1).pack(fill='x', padx=4)
        self.gen_list = tk.Listbox(left, height=12,
                                   bg=self.card_bg, fg=self.orange,
                                   font=('Consolas', 9),
                                   borderwidth=0, highlightthickness=0,
                                   relief='flat', selectbackground='#1f6feb')
        self.gen_list.pack(fill='both', padx=4, pady=(2, 6), expand=True)

        # -- 排队中 (middle) --
        mid = tk.Frame(panels, bg=self.card_bg, highlightbackground=self.border, highlightthickness=1)
        mid.pack(side='left', fill='both', expand=True, padx=(6, 0))
        tk.Label(mid, text='⏳ 排队中',
                 font=('Microsoft YaHei', 10, 'bold'),
                 bg=self.card_bg, fg='#8b949e').pack(anchor='w', padx=8, pady=(6, 2))
        tk.Frame(mid, bg=self.border, height=1).pack(fill='x', padx=4)
        self.pending_list = tk.Listbox(mid, height=12,
                                       bg=self.card_bg, fg='#8b949e',
                                       font=('Consolas', 9),
                                       borderwidth=0, highlightthickness=0,
                                       relief='flat', selectbackground='#1f6feb')
        self.pending_list.pack(fill='both', padx=4, pady=(2, 6), expand=True)

        # -- 已完成 (right) --
        right = tk.Frame(panels, bg=self.card_bg, highlightbackground=self.border, highlightthickness=1)
        right.pack(side='left', fill='both', expand=True, padx=(6, 0))
        tk.Label(right, text='✅ 已完成',
                 font=('Microsoft YaHei', 10, 'bold'),
                 bg=self.card_bg, fg=self.green).pack(anchor='w', padx=8, pady=(6, 2))
        tk.Frame(right, bg=self.border, height=1).pack(fill='x', padx=4)
        self.done_list = tk.Listbox(right, height=12,
                                    bg=self.card_bg, fg=self.green,
                                    font=('Consolas', 9),
                                    borderwidth=0, highlightthickness=0,
                                    relief='flat', selectbackground='#1f6feb')
        self.done_list.pack(fill='both', padx=4, pady=(2, 6), expand=True)

    def _stat_item(self, parent, label, value, color, side):
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
            except requests.RequestException as e:
                self.root.after(0, lambda: self.status_label.config(text=f'⏹ 停止失败: {e}', fg=self.red))
        threading.Thread(target=task, daemon=True).start()

    def _start(self):
        def task():
            try:
                requests.post(START_URL, timeout=5)
            except requests.RequestException as e:
                self.root.after(0, lambda: self.status_label.config(text=f'▶ 启动失败: {e}', fg=self.red))
        threading.Thread(target=task, daemon=True).start()

    def _delete(self):
        if not messagebox.askyesno('确认删除', '确定要删除所有缩略图缓存吗？\n此操作不可撤销！', icon='warning', default='no'):
            return
        def task():
            try:
                requests.delete(DELETE_URL, timeout=10)
                self.root.after(0, lambda: self.status_label.config(text='🗑 缩略图已全部删除', fg=self.orange))
            except requests.RequestException as e:
                self.root.after(0, lambda: self.status_label.config(text=f'删除失败: {e}', fg=self.red))
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
        pending_files = data.get('pendingFiles', [])
        recent_completed = data.get('recentCompleted', [])
        failed_files = data.get('failedFiles', [])
        elapsed_ms = data.get('elapsed', 0)
        concurrency = data.get('concurrency', 0)

        elapsed_s = elapsed_ms // 1000
        elapsed_str = (f'{elapsed_s // 60}m {elapsed_s % 60}s' if elapsed_s >= 60 else f'{elapsed_s}s')

        # ---- Buttons ----
        is_gen = (status == 'generating')
        self.btn_stop.config(state='normal' if is_gen else 'disabled')
        self.btn_start.config(state='disabled' if is_gen else 'normal')

        if status == 'idle':
            self.status_label.config(text='⏸ 空闲 — 点击 ▶ 开始生成缩略图', fg=self.accent)
        elif status == 'generating':
            pct = (completed / total * 100) if total > 0 else 0
            self.progress['value'] = pct
            self.percent_label.config(text=f'{pct:.1f}%')
            self.status_label.config(text=f'⏳ 生成中... 并发 {max(len(current_files), concurrency)}', fg=self.orange)
        elif status == 'done':
            self.progress['value'] = 100
            self.percent_label.config(text='100%')
            self.status_label.config(
                text='✅ 全部生成完成' if failed == 0 else f'✅ 生成完成（{failed} 个失败）',
                fg=self.green if failed == 0 else self.orange)
        elif status == 'stopped':
            self.status_label.config(text=f'⏸ 已暂停（已完成 {completed}，失败 {failed}）', fg=self.red)

        self.stat_已完成.config(text=str(completed))
        self.stat_失败.config(text=str(failed))
        self.stat_剩余.config(text=str(remaining))
        self.stat_总计.config(text=str(total))
        self.stat_耗时.config(text=elapsed_str)
        self.stat_并发.config(text=str(concurrency))

        # ---- Fill three panels ----
        bar_w = 8

        # 生成中
        self.gen_list.delete(0, 'end')
        if current_files:
            for f in current_files:
                display = f if len(f) <= 42 else f'...{f[-39:]}'
                bar = '█' * (bar_w // 2) + '░' * (bar_w - bar_w // 2)
                self.gen_list.insert('end', f'  {bar}  {display}')
        else:
            self.gen_list.insert('end', '  (无)')

        # 排队中
        self.pending_list.delete(0, 'end')
        if pending_files:
            for f in pending_files:
                display = f if len(f) <= 48 else f'...{f[-45:]}'
                self.pending_list.insert('end', f'  {display}')
        else:
            self.pending_list.insert('end', '  (无)')

        # 已完成 + 失败
        self.done_list.delete(0, 'end')
        has_done = False
        if recent_completed:
            has_done = True
            for item in reversed(recent_completed):
                f = item.get('file', '')
                display = f if len(f) <= 44 else f'...{f[-41:]}'
                self.done_list.insert('end', f'  ✅ {display}')
        if failed_files:
            has_done = True
            for f in reversed(failed_files):
                display = f if len(f) <= 44 else f'...{f[-41:]}'
                self.done_list.insert('end', f'  ❌ {display}')
        if not has_done:
            self.done_list.insert('end', '  (无)')

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
