import argparse
import json
import queue
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


BG = '#edf2f8'
PANEL = '#ffffff'
INK = '#142338'
MUTED = '#526680'
ACCENT = '#2455cd'
STATUSES = {'online': ('В сети', '#137049'), 'away': ('Отошёл', '#925400'),
            'busy': ('Занят', '#b12645'), 'offline': ('Не в сети', MUTED)}
EMOJIS = ('😀', '😊', '😂', '👍', '👏', '🙏', '❤️', '🔥', '🎉', '👀', '✅', '🤔', '👋', '🙂', '🚀', '💡')


def configure_theme(root):
    root.configure(background=BG)
    root.option_add('*Font', ('Segoe UI', 10))
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('TFrame', background=BG)
    style.configure('TLabel', background=BG, foreground=INK)
    style.configure('Title.TLabel', font=('Segoe UI', 19, 'bold'))
    style.configure('Muted.TLabel', foreground=MUTED)
    style.configure('TButton', padding=(10, 6))
    style.configure('Primary.TButton', foreground=PANEL, background=ACCENT, bordercolor=ACCENT)
    style.map('Primary.TButton', background=[('disabled', '#a1b4df'), ('active', '#1a429f')])
    style.configure('TEntry', fieldbackground=PANEL, foreground=INK, padding=7)
    style.configure('Treeview', background=PANEL, fieldbackground=PANEL, foreground=INK,
                    rowheight=35, borderwidth=0)
    style.map('Treeview', background=[('selected', '#dce8ff')], foreground=[('selected', INK)])


class Api:
    def __init__(self, config):
        self.base = config['server'].rstrip('/')
        self.headers = {'X-User': str(config['user']), 'Authorization': 'Bearer ' + config['token'],
                        'Content-Type': 'application/json'}

    def request(self, path, body=None, timeout=5):
        data = json.dumps(body).encode() if body is not None else None
        with urlopen(Request(self.base + path, headers=self.headers, data=data), timeout=timeout) as response:
            return json.load(response)


class Composer:
    def __init__(self, app, parent, recipient):
        self.app = app
        self.recipient = recipient
        self.attempt = None
        self.picker = None
        self.frame = ttk.Frame(parent)
        self.entry = ttk.Entry(self.frame, font=('Segoe UI Emoji', 11))
        self.entry.pack(side='left', fill='x', expand=True, padx=(0, 8))
        self.button = ttk.Button(self.frame, text='Отправить', command=self.send, style='Primary.TButton')
        self.button.pack(side='right')
        self.emoji = ttk.Button(self.frame, text='☺', width=3, command=self.pick_emoji)
        self.emoji.pack(side='right', padx=(0, 8))
        self.entry.bind('<Return>', self.send)
    def pick_emoji(self):
        if self.picker is not None:
            self.close_picker()
            return
        picker = self.picker = tk.Toplevel(self.frame)
        picker.withdraw()
        picker.title('Эмодзи')
        picker.transient(self.frame.winfo_toplevel())
        picker.resizable(False, False)
        picker.protocol('WM_DELETE_WINDOW', self.close_picker)
        picker.bind('<Escape>', lambda event: self.close_picker())
        panel = ttk.Frame(picker, padding=8)
        panel.pack()
        for index, emoji in enumerate(EMOJIS):
            row, column = divmod(index, 4)
            button = tk.Button(panel, text=emoji, font=('Segoe UI Emoji', 15), width=3,
                               background=PANEL, relief='flat', activebackground='#dce8ff',
                               command=lambda value=emoji: self.insert_emoji(value))
            button.grid(row=row, column=column, padx=2, pady=2)
        picker.update_idletasks()
        x = max(0, self.emoji.winfo_rootx() + self.emoji.winfo_width() - picker.winfo_reqwidth())
        y = max(0, self.emoji.winfo_rooty() - picker.winfo_reqheight() - 36)
        picker.geometry(f'+{x}+{y}')
        picker.deiconify()
        picker.lift()

    def close_picker(self):
        self.picker.destroy()
        self.picker = None

    def insert_emoji(self, emoji):
        self.entry.insert('insert', emoji)
        self.close_picker()
        self.entry.focus_set()

    def send(self, event=None):
        if self.button.instate(['disabled']):
            return
        recipient = self.recipient()
        text = self.entry.get().strip()
        if not recipient or not text:
            return
        if len(text) > 4000:
            self.app.status.set('Максимум 4000 символов')
            return
        if self.attempt is None or self.attempt[:2] != (recipient, text):
            self.attempt = (recipient, text, str(uuid4()))
        if self.picker is not None:
            self.close_picker()
        self.entry.state(['disabled'])
        self.button.state(['disabled'])
        self.emoji.state(['disabled'])
        threading.Thread(target=self.post, args=self.attempt, daemon=True).start()

    def post(self, recipient, text, nonce):
        try:
            self.app.api.request('/messages', {'recipient': recipient, 'text': text, 'nonce': nonce})
        except (OSError, ValueError):
            self.app.events.put(('sent', (self, False)))
        else:
            self.app.events.put(('sent', (self, True)))

    def finish(self, success):
        if not self.frame.winfo_exists():
            return
        self.entry.state(['!disabled'])
        self.button.state(['!disabled'])
        self.emoji.state(['!disabled'])
        if success:
            self.entry.delete(0, 'end')
            self.attempt = None
        self.button.configure(text='Отправить' if success else 'Повторить')


class Desktop:
    def __init__(self, root, config):
        self.root = root
        self.user = str(config['user'])
        self.api = Api(config)
        self.events = queue.Queue()
        self.names = {}
        self.presence = {}
        self.contact = None
        self.presence_requests = queue.Queue()
        self.messages = []
        self.dialogs = {}
        self.drafts = {}
        self.status = tk.StringVar(master=root, value='Подключение…')
        self.search = tk.StringVar(master=root)
        self.title = tk.StringVar(master=root, value='Выберите сотрудника')
        self.details = tk.StringVar(master=root, value='Личные сообщения')

        configure_theme(root)
        root.title('Офисный чат')
        root.geometry('920x600')
        root.minsize(660, 380)
        root.protocol('WM_DELETE_WINDOW', root.iconify)
        sidebar = ttk.Frame(root, padding=(18, 16, 12, 16), width=290)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        ttk.Label(sidebar, text='Офисный чат', style='Title.TLabel').pack(anchor='w')
        ttk.Label(sidebar, textvariable=self.status, style='Muted.TLabel').pack(anchor='w', pady=(2, 18))
        ttk.Label(sidebar, text='Сотрудники').pack(anchor='w')
        ttk.Label(sidebar, text='Поиск по имени', style='Muted.TLabel').pack(anchor='w', pady=(7, 0))
        ttk.Entry(sidebar, textvariable=self.search).pack(fill='x', pady=(4, 8))
        directory = ttk.Frame(sidebar)
        directory.pack(fill='both', expand=True)
        scroll = ttk.Scrollbar(directory)
        scroll.pack(side='right', fill='y')
        self.people = ttk.Treeview(directory, columns=('name', 'status'), show='headings',
                                   selectmode='browse', yscrollcommand=scroll.set)
        self.people.heading('name', text='Имя', anchor='w')
        self.people.heading('status', text='Статус', anchor='w')
        self.people.column('name', width=138, minwidth=70)
        self.people.column('status', width=94, stretch=False)
        self.people.pack(side='left', fill='both', expand=True)
        scroll.configure(command=self.people.yview)
        for key, (_, color) in STATUSES.items():
            self.people.tag_configure(key, foreground=color)
        self.people.bind('<<TreeviewSelect>>', self.select_contact)
        self.search.trace_add('write', lambda *args: self.refresh_people())
        controls = ttk.Frame(sidebar)
        controls.pack(fill='x', pady=(12, 0))
        labels = {label: key for key, (label, _) in STATUSES.items() if key != 'offline'}
        availability = ttk.Combobox(controls, state='readonly', values=list(labels), width=12)
        availability.current(0)
        availability.pack(side='left')
        availability.bind('<<ComboboxSelected>>', lambda event: self.presence_requests.put(labels[availability.get()]))
        ttk.Button(controls, text='Выйти', command=root.destroy).pack(side='right')
        dialog = ttk.Frame(root, padding=(8, 16, 18, 16))
        dialog.pack(side='left', fill='both', expand=True)
        ttk.Label(dialog, textvariable=self.title, style='Title.TLabel').pack(anchor='w')
        ttk.Label(dialog, textvariable=self.details, style='Muted.TLabel').pack(anchor='w', pady=(2, 14))
        self.composer = Composer(self, dialog, self.selected)
        self.composer.frame.pack(side='bottom', fill='x', pady=(8, 0))
        self.history = self.make_history(dialog)

        threading.Thread(target=self.listen, daemon=True).start()
        threading.Thread(target=self.heartbeat, daemon=True).start()
        root.after(35, self.drain)

    def make_history(self, parent):
        history = ttk.Frame(parent)
        history.pack(fill='both', expand=True)
        scroll = ttk.Scrollbar(history)
        scroll.pack(side='right', fill='y')
        text = tk.Text(history, wrap='word', state='disabled', yscrollcommand=scroll.set,
                       background=PANEL, foreground=INK, relief='flat', highlightthickness=0,
                       padx=14, pady=12, font=('Segoe UI Emoji', 11), width=1, height=1)
        text.pack(side='left', fill='both', expand=True)
        scroll.configure(command=text.yview)
        text.tag_configure('incoming', lmargin1=12, lmargin2=12, rmargin=68, spacing1=4,
                           spacing3=4, background='#edf2f8')
        text.tag_configure('outgoing', justify='right', lmargin1=68, lmargin2=68, rmargin=12,
                           spacing1=4, spacing3=4, background='#e0ebff')
        text.tag_configure('meta', foreground=MUTED, font=('Segoe UI', 9, 'bold'))
        return text

    def heartbeat(self):
        status = 'online'
        while True:
            try:
                self.events.put(('presence', self.api.request('/presence', {'status': status})))
            except HTTPError as error:
                if error.code == 401:
                    return
            except (OSError, ValueError):
                pass
            try:
                status = self.presence_requests.get(timeout=3)
            except queue.Empty:
                pass

    def listen(self):
        cursor = None
        connected = False
        while True:
            try:
                if cursor is None:
                    snapshot = self.api.request('/bootstrap')
                    cursor = snapshot['messages'][-1]['id'] if snapshot['messages'] else 0
                    self.events.put(('snapshot', snapshot))
                if not connected:
                    self.events.put(('status', 'Подключено'))
                    connected = True
                rows = self.api.request(f'/events?after={cursor}', timeout=20)
                if rows:
                    cursor = rows[-1]['id']
                    self.events.put(('messages', rows))
            except (OSError, ValueError) as error:
                if isinstance(error, HTTPError) and error.code == 401:
                    self.events.put(('status', 'Проверьте ID и токен в настройках клиента'))
                    return
                self.events.put(('status', 'Нет связи. Повторное подключение…'))
                connected = False
                time.sleep(1)

    def drain(self):
        for _ in range(100):
            try:
                kind, data = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == 'snapshot':
                self.names = data['users']
                self.root.title(f"Офисный чат · {self.names[self.user]}")
                self.messages.extend(data['messages'])
                self.refresh_people()
                self.render()
            elif kind == 'messages':
                self.messages.extend(data)
                self.render()
                incoming = dict.fromkeys(row['sender'] for row in data if row['recipient'] == self.user)
                for sender in incoming:
                    self.show_dialog(sender)
                for contact, (_, history, _) in self.dialogs.items():
                    self.render_history(history, contact)
            elif kind == 'presence' and self.presence != data:
                self.presence = data
                self.refresh_people()
                for contact, (_, _, status) in self.dialogs.items():
                    status.set(self.status_label(contact))
            elif kind == 'sent':
                composer, success = data
                composer.finish(success)
            elif kind == 'status':
                self.status.set(data)
        self.root.after(35, self.drain)

    def selected(self):
        return self.contact

    def select_contact(self, event):
        selection = self.people.selection()
        if selection and selection[0] != self.contact:
            if self.composer.button.instate(['disabled']):
                if self.people.exists(self.contact):
                    self.people.selection_set(self.contact)
                return
            entry = self.composer.entry
            if self.contact:
                self.drafts[self.contact] = (entry.get(), self.composer.attempt)
            self.contact = selection[0]
            draft, self.composer.attempt = self.drafts.pop(self.contact, ('', None))
            entry.delete(0, 'end')
            entry.insert(0, draft)
            self.composer.button.configure(text='Повторить' if self.composer.attempt else 'Отправить')
            self.render()

    def status_label(self, contact):
        status = self.presence.get(contact, 'offline')
        return STATUSES[status][0]

    def refresh_people(self):
        query = self.search.get().strip().casefold()
        contacts = sorted((key for key, name in self.names.items() if key != self.user and query in name.casefold()),
                          key=lambda key: self.names[key].casefold())
        for key in self.people.get_children():
            if key not in contacts:
                self.people.delete(key)
        for index, key in enumerate(contacts):
            status = self.presence.get(key, 'offline')
            values = (self.names[key], f'● {self.status_label(key)}')
            if self.people.exists(key):
                self.people.item(key, values=values, tags=(status,))
                self.people.move(key, '', index)
            else:
                self.people.insert('', index, iid=key, values=values, tags=(status,))
        if self.contact in contacts and self.people.selection() != (self.contact,):
            self.people.selection_set(self.contact)
        if self.contact:
            self.details.set(self.status_label(self.contact))

    def render(self):
        self.title.set(self.names.get(self.contact, 'Выберите сотрудника'))
        self.details.set(self.status_label(self.contact) if self.contact else 'Личные сообщения')
        self.render_history(self.history, self.contact)

    def render_history(self, history, contact):
        previous_contact = getattr(history, 'contact', None)
        top, bottom = history.yview()
        history.contact = contact
        history.configure(state='normal')
        history.delete('1.0', 'end')
        for row in self.messages:
            own = row['sender'] == self.user
            other = row['recipient'] if own else row['sender']
            if other == contact:
                name = 'Вы' if own else self.names.get(other, other)
                stamp = datetime.fromisoformat(row['sent_at'].replace('Z', '+00:00')).astimezone()
                tag = 'outgoing' if own else 'incoming'
                history.insert('end', f'{name}  ·  {stamp:%d.%m %H:%M}\n', (tag, 'meta'))
                history.insert('end', row['text'] + '\n', (tag,))
                history.insert('end', '\n')
        if history.index('end-1c') == '1.0':
            history.insert('end', 'Начните переписку.' if contact else 'Выберите сотрудника слева.', ('meta',))
        history.configure(state='disabled')
        if previous_contact == contact and bottom < .99:
            history.yview_moveto(top)
        else:
            history.see('end')

    def close_dialog(self, sender):
        window, _, _ = self.dialogs.pop(sender)
        window.destroy()

    def show_dialog(self, sender):
        if sender in self.dialogs:
            window, _, _ = self.dialogs[sender]
        else:
            window = tk.Toplevel(self.root)
            window.withdraw()
            window.title(f"Офисный чат · {self.names.get(sender, sender)}")
            window.minsize(320, 240)
            window.geometry('560x460')
            window.protocol('WM_DELETE_WINDOW', lambda: self.close_dialog(sender))
            panel = ttk.Frame(window, padding=18)
            panel.pack(fill='both', expand=True)
            ttk.Label(panel, text=self.names.get(sender, sender), style='Title.TLabel').pack(anchor='w')
            status = tk.StringVar(master=window, value=self.status_label(sender))
            ttk.Label(panel, textvariable=status, style='Muted.TLabel').pack(anchor='w', pady=(2, 12))
            Composer(self, panel, lambda: sender).frame.pack(side='bottom', fill='x', pady=(8, 0))
            history = self.make_history(panel)
            self.dialogs[sender] = window, history, status
        if not window.winfo_viewable():
            window.update_idletasks()
            width, height = max(560, window.winfo_width()), max(460, window.winfo_height())
            width = min(width, window.winfo_screenwidth() - 40)
            height = min(height, window.winfo_screenheight() - 100)
            x = (window.winfo_screenwidth() - width) // 2
            y = (window.winfo_screenheight() - height) // 2
            window.geometry(f'{width}x{height}+{x}+{y}')
        window.deiconify()
        window.attributes('-topmost', True)
        window.lift()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    root = tk.Tk()
    Desktop(root, config)
    root.mainloop()


if __name__ == '__main__':
    main()
