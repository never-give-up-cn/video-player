#!/usr/bin/env python3
"""
缩略图生成进度监控器
实时显示 ffmpeg 缩略图生成进度
用法: python thumbnail_monitor.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import time
import os

API_URL = 'http://localhost:3000/api/thumbnail-progress'
POLL_INTERVAL = 1  # seconds


class ThumbnailMonitor:
    bg = '#0d1117'
    fg = '#e6edf3'
    accent = '#58a6ff'
    green = '#3fb950'
    orange = '#d29922'
    red = '#f85149'
    card_bg = '#161b22'

    def __init__(self, root):
        self.root = root
        self.root.title('缩略图生成进度')
        self.root.geometry('680x400+300+200')
        self.root.configure(bg=self.bg)
        self.root.resizable(False, False)

        try:
            self._build_ui()
        except Exception as e:
            messagebox.showerror('启动错误', f'UI初始化失败:\n{e}')
            raise
        self.running = True
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()

        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

    def _build_ui(self):
        # ---- Header ----
        header = tk.Frame(self.root, bg=self.bg)
        header.pack(fill='x', padx=20, pady=(16, 4))

        tk.Label(header, text='🖼️  缩略图生成进度',
                 font=('Microsoft YaHei', 16, 'bold'),
                 bg=self.bg, fg=self.fg).pack(anchor='w')

        self.status_label = tk.Label(header, text='等待中...',
                                     font=('Microsoft YaHei', 11),
                                     bg=self.bg, fg=self.accent)
        self.status_label.pack(anchor='w', pady=(2, 0))

        # ---- Progress bar ----
        bar_frame = tk.Frame(self.root, bg=self.bg)
        bar_frame.pack(fill='x', padx=20, pady=(10, 4))

        self.progress = ttk.Progressbar(bar_frame, length=640, mode='determinate')
        self.progress.pack(fill='x')

        self.percent_label = tk.Label(bar_frame, text='0%',
                                      font=('Consolas', 10),
                                      bg=self.bg, fg=self.fg)
        self.percent_label.pack(anchor='e', pady=(2, 0))

        # ---- Stats card ----
        stats = tk.Frame(self.root, bg=self.card_bg, highlightbackground='#30363d',
                         highlightthickness=1)
        stats.pack(fill='x', padx=20, pady=(8, 4))

        row0 = tk.Frame(stats, bg=self.card_bg)
        row0.pack(fill='x', padx=14, pady=(10, 4))
        self._stat_item(row0, '已完成', '0', self.green, side='left')
        self._stat_item(row0, '失败', '0', self.red, side='left')
        self._stat_item(row0, '剩余', '0', self.orange, side='left')
        self._stat_item(row0, '总计', '0', self.fg, side='right')

        row1 = tk.Frame(stats, bg=self.card_bg)
        row1.pack(fill='x', padx=14, pady=(0, 10))
        self._stat_item(row1, '耗时', '0s', self.accent, side='left')
        self._stat_item(row1, '并发', '0', self.fg, side='left')

        # ---- Current files ----
        files_header = tk.Frame(self.root, bg=self.bg)
        files_header.pack(fill='x', padx=20, pady=(8, 2))
        tk.Label(files_header, text='正在处理:',
                 font=('Microsoft YaHei', 10, 'bold'),
                 bg=self.bg, fg=self.fg).pack(anchor='w')

        self.files_listbox = tk.Listbox(
            self.root, height=6,
            bg=self.card_bg, fg=self.fg,
            selectbackground=self.accent,
            font=('Consolas', 9),
            borderwidth=0, highlightthickness=1,
            highlightbackground='#30363d',
            relief='flat'
        )
        self.files_listbox.pack(fill='both', padx=20, pady=(2, 16), expand=False)

    def _stat_item(self, parent, label, value, color, side='left'):
        frame = tk.Frame(parent, bg=self.card_bg)
        frame.pack(side=side, padx=(0, 28))
        tk.Label(frame, text=label,
                 font=('Microsoft YaHei', 9),
                 bg=self.card_bg, fg='#8b949e').pack(anchor='w')
        lbl = tk.Label(frame, text=value,
                       font=('Consolas', 13, 'bold'),
                       bg=self.card_bg, fg=color)
        lbl.pack(anchor='w')
        setattr(self, f'stat_{label}', lbl)

    def _poll_loop(self):
        while self.running:
            try:
                r = requests.get(API_URL, timeout=3)
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
        elapsed_ms = data.get('elapsed', 0)

        elapsed_s = elapsed_ms // 1000
        elapsed_str = (f'{elapsed_s // 60}m {elapsed_s % 60}s' if elapsed_s >= 60
                       else f'{elapsed_s}s')

        if status == 'idle':
            self.status_label.config(text='等待生成任务...', fg=self.accent)
        elif status == 'generating':
            pct = (completed / total * 100) if total > 0 else 0
            self.progress['value'] = pct
            self.percent_label.config(text=f'{pct:.1f}%')
            self.status_label.config(text=f'⏳ 生成中... 并发 {len(current_files) if current_files else "?"}',
                                     fg=self.orange)
        elif status == 'done':
            self.progress['value'] = 100
            self.percent_label.config(text='100%')
            if failed > 0:
                self.status_label.config(text=f'✅ 生成完成（{failed} 个失败）', fg=self.green)
            else:
                self.status_label.config(text='✅ 全部生成完成', fg=self.green)

        self.stat_已完成.config(text=str(completed))
        self.stat_失败.config(text=str(failed))
        self.stat_剩余.config(text=str(remaining))
        self.stat_总计.config(text=str(total))
        self.stat_耗时.config(text=elapsed_str)

        # Update files list
        self.files_listbox.delete(0, 'end')
        if current_files:
            for f in current_files[:8]:
                display = f if len(f) <= 60 else f'...{f[-57:]}'
                self.files_listbox.insert('end', f'  📹  {display}')
        else:
            self.files_listbox.insert('end', '  (无)')

    def _set_offline(self):
        self.status_label.config(text='❌ 无法连接服务器 (localhost:3000)', fg=self.red)

    def _on_close(self):
        self.running = False
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ThumbnailMonitor(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.running = False


if __name__ == '__main__':
    main()
