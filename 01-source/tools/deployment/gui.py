"""A separate desktop window survives both backend and UE shutdown during an update."""
import argparse
import json
import os
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser

from manager import Manager, read_json, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--home', type=Path)
    args = parser.parse_args()
    preferences = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'OntoTwin/deployment-manager.json'
    saved = read_json(preferences) if preferences.exists() else {}
    default_home = args.home or saved.get('home') or str(preferences.parent / 'Environment')

    root = tk.Tk()
    root.title('OntoTwin · 部署管理')
    root.geometry('960x740'); root.minsize(860, 660)
    root.configure(bg='#f7f7f7')
    style = ttk.Style(root); style.theme_use('clam')
    style.configure('.', font=('Microsoft YaHei UI', 10), background='#f7f7f7', foreground='#202020')
    style.configure('TButton', padding=(14, 8), background='#ffffff', bordercolor='#dddddd')
    style.configure('Primary.TButton', background='#202020', foreground='#ffffff')
    style.map('Primary.TButton', background=[('active', '#404040'), ('disabled', '#a0a0a0')])
    style.configure('TEntry', fieldbackground='#ffffff', padding=6)
    outer = ttk.Frame(root, padding=24); outer.pack(fill='both', expand=True)
    ttk.Label(outer, text='OntoTwin 部署管理', font=('Microsoft YaHei UI', 22, 'bold')).pack(anchor='w')
    ttk.Label(outer, text='统一更新网页后台与 UE 插件。更新前自动备份，保留现有数据与关卡绑定。', padding=(0, 6, 0, 14)).pack(anchor='w')
    controls, busy = [], [False]
    events = queue.Queue()
    selected_release = [None]
    home = tk.StringVar(value=str(default_home))
    summary = tk.StringVar(value='先接管已有安装，或选择已配置的环境目录')
    status = tk.StringVar(value='就绪')
    confirmed = tk.BooleanVar(value=False)

    def button(parent, label, callback, primary=False):
        item = ttk.Button(parent, text=label, command=callback, style='Primary.TButton' if primary else 'TButton')
        controls.append(item)
        return item

    def manager():
        return Manager(home.get(), lambda text: events.put(('log', text)))

    def refresh():
        try:
            m = manager(); state = m.state()
            current = read_json(m.release(state) / 'manifest.json')['package_version']
            recent = Path(state['last_backup']).name if state.get('last_backup') else '尚无备份'
            pending = m.pending()
            text = f"当前版本：{current}    后台：http://127.0.0.1:{state['port']}\n最近备份：{recent}    {state.get('status', '')}"
            if pending:
                text += '\n上次更新中断，请点击“恢复上次更新”。'
            if selected_release[0]:
                text += '\n待导入版本：' + selected_release[0]
            summary.set(text)
            projects.delete(0, 'end')
            for project in state['projects']: projects.insert('end', project)
        except Exception:
            summary.set('尚未接管安装：点击“接管已有安装”，选择原接入包的解压目录。')
            projects.delete(0, 'end')

    def work(action, function):
        if busy[0]: return
        busy[0] = True
        for control in controls: control.configure(state='disabled')
        status.set(action)
        write_json(preferences, {'home': home.get(), 'launcher': str(Path(__file__).with_name('Launch-Manager.ps1'))})
        def execute():
            try:
                result = function()
                events.put(('done', result))
            except Exception as exc:
                events.put(('error', str(exc)))
        threading.Thread(target=execute, daemon=True).start()

    def choose_home():
        value = filedialog.askdirectory(title='选择固定安装环境目录')
        if value:
            home.set(value); selected_release[0] = None; confirmed.set(False); refresh()

    def adopt():
        existing = filedialog.askdirectory(title='选择正在使用的接入包解压目录（含 .runtime）')
        if existing:
            m = manager()
            work('接管已有安装……', lambda: m.adopt(existing))

    def add_project():
        project = filedialog.askopenfilename(title='添加使用此后台的 UE 工程', filetypes=[('UE 工程', '*.uproject')])
        if project:
            confirmed.set(False)
            m = manager()
            work('检查工程……', lambda: m.add_project(project))

    def import_package():
        package = filedialog.askopenfilename(title='选择更新包（完整接入 ZIP 也可以）', filetypes=[('OntoTwin 接入包', '*.zip')])
        if package:
            m = manager()
            def inspect():
                with m.locked():
                    release = m.stage(package)
                    selected_release[0] = release
                    m.preflight(release)
                return release
            work('核验更新包与工程……', inspect)

    def apply():
        if not selected_release[0]:
            messagebox.showinfo('请先导入', '先选择一个更新包。', parent=root); return
        if not confirmed.get():
            messagebox.showinfo('确认工程范围', '请添加所有使用此后台的工程，然后勾选工程范围确认。', parent=root); return
        if not messagebox.askokcancel('开始统一更新', '请关闭列表中的 UE 工程。\n更新期间网页暂停访问；自动备份完成后才会替换程序与插件。\n继续更新？', parent=root): return
        m = manager(); release = selected_release[0]
        work('正在备份和更新……', lambda: m.update(release, all_projects_confirmed=True))

    def start():
        m = manager()
        def launch():
            state = m.start()
            webbrowser.open(f"http://127.0.0.1:{state['port']}/account")
        work('正在启动平台……', launch)

    def open_backup():
        path = Path(home.get()) / 'backups'; path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)

    def recover():
        if messagebox.askokcancel('恢复上次更新', '恢复中断前的程序与插件。\n如果更新未对外开放，将从自动备份恢复到新数据卷；原数据卷仍保留。\n请先关闭相关 UE 工程。', parent=root):
            m = manager(); work('正在恢复……', m.recover)

    row = ttk.Frame(outer); row.pack(fill='x')
    ttk.Label(row, text='固定环境目录', width=14).pack(side='left')
    entry = ttk.Entry(row, textvariable=home, state='readonly'); entry.pack(side='left', fill='x', expand=True)
    button(row, '选择', choose_home).pack(side='left', padx=(8, 0))
    button(row, '接管已有安装', adopt).pack(side='left', padx=(8, 0))
    ttk.Label(outer, textvariable=summary, wraplength=880, padding=(0, 14)).pack(anchor='w')
    row = ttk.Frame(outer); row.pack(fill='x', pady=(0, 6))
    ttk.Label(row, text='一起更新的 UE 工程', font=('Microsoft YaHei UI', 11, 'bold')).pack(side='left')
    button(row, '添加工程', add_project).pack(side='right')
    projects = tk.Listbox(outer, height=3, font=('Microsoft YaHei UI', 10), relief='flat', borderwidth=1, highlightbackground='#dddddd', highlightthickness=1)
    projects.pack(fill='x')
    confirm = ttk.Checkbutton(outer, text='已添加所有使用此后台的 UE 工程（本次统一更新全部已添加工程）', variable=confirmed)
    confirm.pack(anchor='w', pady=8); controls.append(confirm)
    row = ttk.Frame(outer); row.pack(fill='x', pady=(4, 12))
    button(row, '启动平台', start).pack(side='left')
    button(row, '导入更新包', import_package).pack(side='left', padx=8)
    button(row, '备份并更新', apply, True).pack(side='left')
    button(row, '查看备份', open_backup).pack(side='right')
    button(row, '恢复上次更新', recover).pack(side='right', padx=8)
    report = tk.Text(outer, height=9, wrap='word', background='#ffffff', foreground='#202020', relief='flat', padx=12, pady=12, font=('Microsoft YaHei UI', 10))
    report.pack(fill='both', expand=True); report.configure(state='disabled')
    ttk.Label(outer, textvariable=status, padding=(0, 10, 0, 0), wraplength=880).pack(anchor='w')
    ttk.Label(outer, text='适用：已有 4.8 接入环境的同结构更新。当前不自动处理数据库跨版本迁移或共享插件目录。', foreground='#666666').pack(anchor='w')

    def poll():
        try:
            while True:
                kind, value = events.get_nowait()
                if kind == 'log' or kind == 'error':
                    report.configure(state='normal'); report.insert('end', str(value) + '\n'); report.see('end'); report.configure(state='disabled')
                if kind in ('done', 'error'):
                    busy[0] = False
                    for control in controls: control.configure(state='normal')
                    status.set('完成本步，请查看结果' if kind == 'done' else '本步未完成，请查看原因')
                    refresh()
        except queue.Empty:
            pass
        root.after(120, poll)
    root.protocol('WM_DELETE_WINDOW', lambda: messagebox.showinfo('正在处理', '请等待当前操作完成。', parent=root) if busy[0] else root.destroy())
    refresh(); poll(); root.mainloop()


if __name__ == '__main__': main()
