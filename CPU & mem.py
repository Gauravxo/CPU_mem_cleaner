#!/usr/bin/env python3
"""
SysMon11  —  Win11 Desktop Widget  
Double‑click SysMon11.pyw
"""
import tkinter as tk
from tkinter import ttk
import psutil, threading, time, os, gc, sys, shutil, tempfile, datetime, subprocess
import winreg                                   

IS_WIN = sys.platform == "win32"

if IS_WIN:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)

 
    if "python.exe" in sys.executable.lower():
        pythonw = sys.executable.replace("python.exe", "pythonw.exe")
        if os.path.exists(pythonw):
            subprocess.Popen([pythonw, __file__] + sys.argv[1:],
                             creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit(0)

   
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

    
    MUTEX_NAME = "Global\\SysMon11_SingleInstance"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if ctypes.windll.kernel32.GetLastError() == 183:   
        hwnd = ctypes.windll.user32.FindWindowW(None, "SysMon11_Widget")
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9)   
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        sys.exit(0)

# ── Theme (dark only now) ─────────────────────────────────────────────────────
COL = {
    "BG": "#000000", "PANEL": "#000000", "CARD": "#000000",
    "CARD2": "#252529", "ACNT": "#0078d4", "GRN": "#22d45f",
    "AMB": "#f5a623", "RED": "#f03e3e", "TEXT": "#ececec",
    "TXT2": "#888896", "TXT3": "#303038", "BORD": "#27272f",
    "WARN": "#f5a623", "DANGER_BG": "#3d1e1e",
}

S_CLR = {
    "LISTEN":      "#4db2ff",
    "ESTABLISHED": "#22d45f",
    "TIME_WAIT":   "#f5a623",
    "CLOSE_WAIT":  "#f5a623",
    "SYN_SENT":    "#b07bfa",
    "SYN_RECV":    "#b07bfa",
    "FIN_WAIT1":   "#f5a623",
    "FIN_WAIT2":   "#f5a623",
    "CLOSED":      "#3a3a44",
    "NONE":        "#3a3a44",
}

F  = "Segoe UI Variable" if IS_WIN else "Ubuntu"
FM = "Cascadia Code"     if IS_WIN else "Ubuntu Mono"

DANGER_PORTS = {20, 21, 22, 23, 25, 53, 69, 80, 88, 110, 111, 135, 137, 138, 139, 143, 161, 162, 389, 443, 445, 465, 512, 513, 514, 587, 636, 993, 995, 1194, 1433, 1434, 1521, 1723, 2049, 2375, 2376, 3306, 3389, 5060, 5432, 5900, 5985, 5986, 6379, 6443, 8000, 8080, 8888, 27017}
SUSPICIOUS_PROCS = {"mimikatz", "netcat", "nc.exe", "ncat.exe", "powercat", "msfconsole", "meterpreter", "cobaltstrike", "beacon.exe", "empire", "psexec", "paexec", "wmic.exe", "rundll32.exe", "regsvr32.exe", "mshta.exe", "certutil.exe", "bitsadmin.exe", "powershell.exe", "pwsh.exe", "cmd.exe", "cscript.exe", "wscript.exe", "at.exe", "schtasks.exe", "procdump.exe", "processhacker.exe", "mimikatz.exe", "winpeas.exe", "linpeas.sh", "adfind.exe", "bloodhound.exe", "sharphound.exe", "responder.exe", "crackmapexec", "evil-winrm", "net.exe", "nltest.exe", "whoami.exe", "7z.exe", "rar.exe", "temp.exe", "unknown", "svch0st.exe", "explorer32.exe", "chromeupdate.exe", "javaw.exe"}

EDGE_WIDTH = 6
CORNER_RADIUS = 16  


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CPU & mem")   
        self.overrideredirect(True)
        self.attributes("-topmost", False)
        self.attributes("-alpha", 1.0)               
        self.configure(bg=COL["BORD"])
        self.geometry("350x450+120+60")

        self.running = True
        self.conns   = []
        self.flt     = "ALL"
        self._fbtns  = {}
        self._sc     = None
        self._sr     = False
        self._lc     = 0.0
        self._lm     = 0.0

        self._cam_active = False
        self._mic_active = False
        self._loc_active = False

        self._drag_start_x = self._drag_start_y = 0
        self._drag_active = False
        self._resize_edge = None
        self._resize_start_geom = None
        self._resize_start_root = None

        self._ttk_styles()
        self._ui()
        self._apply_rounded_corners(CORNER_RADIUS)

        threading.Thread(target=self._t_cpu_mem, daemon=True).start()
        threading.Thread(target=self._t_net,     daemon=True).start()
        threading.Thread(target=self._t_devices, daemon=True).start()

    
    def _apply_rounded_corners(self, radius):
        """Set a rounded rectangle region for the window."""
        if not IS_WIN:
            return
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
           
            self.update_idletasks()
            w = self.winfo_width()
            h = self.winfo_height()
         
            rgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, w + 1, h + 1, radius, radius)
            ctypes.windll.user32.SetWindowRgn(hwnd, rgn, True)
           
        except Exception:
            pass

    # ── UI ────────────────────────────────────────────────────────────────────
    def _ui(self):
        main = tk.Frame(self, bg=COL["BG"])
        main.pack(fill="both", expand=True, padx=1, pady=1)
        self._main = main

        self._build_title(main)
        self._div(main)
        self._build_stats(main)
        self._div(main)
        self._build_net(main)
        self._div(main)
        self._build_bottom(main)

        self.bind("<Motion>",           self._on_motion)
        self.bind("<ButtonPress-1>",    self._on_button_down)
        self.bind("<B1-Motion>",        self._on_button_motion)
        self.bind("<ButtonRelease-1>",  self._on_button_release)

    def _div(self, p):
        tk.Frame(p, bg=COL["BORD"], height=1).pack(fill="x")

    # ── Title bar ─────────────────────────────────────────────────────────────
    def _build_title(self, p):
        bar = tk.Frame(p, bg=COL["PANEL"], height=38)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        cv = tk.Canvas(bar, width=18, height=18, bg=COL["PANEL"], highlightthickness=0)
        cv.place(x=10, y=10)
        cv.create_rectangle(0,0,8,8,fill=COL["ACNT"],outline="")
        cv.create_rectangle(10,0,18,8,fill=COL["GRN"],outline="")
        cv.create_rectangle(0,10,8,18,fill=COL["AMB"],outline="")
        cv.create_rectangle(10,10,18,18,fill=COL["RED"],outline="")

        tk.Label(bar, text="CPU & mem", bg=COL["PANEL"], fg=COL["TEXT"],
                 font=(F,10,"bold")).place(x=36,y=10)

       
        self._sec_lbl = tk.Label(bar, text="💀", bg=COL["PANEL"],
                                 fg=COL["GRN"], font=(F,8))
        self._sec_lbl.place(x=140, y=8)

        
        cl = tk.Label(bar, text="✕", bg=COL["PANEL"], fg=COL["TXT2"],
                      font=(F,11), cursor="hand2", padx=5, pady=4)
        cl.pack(side="right")        
        cl.bind("<Button-1>", lambda e: self._quit())
        cl.bind("<Enter>",    lambda e: cl.config(bg=COL["RED"], fg=COL["TEXT"]))
        cl.bind("<Leave>",    lambda e: cl.config(bg=COL["PANEL"], fg=COL["TXT2"]))

       
        dev_frame = tk.Frame(bar, bg=COL["PANEL"])
        dev_frame.pack(side="right", padx=(6,4), pady=4)

        self._cam_icon = tk.Label(dev_frame, text="📷", bg=COL["PANEL"],
                                  fg=COL["TEXT"], font=(F,12))
        self._cam_icon.pack(side="left", padx=1)
        self._cam_dot = tk.Label(dev_frame, text="●", bg=COL["PANEL"],
                                 fg=COL["GRN"], font=(F,10))
        self._cam_dot.pack(side="left")

        self._mic_icon = tk.Label(dev_frame, text="🎤", bg=COL["PANEL"],
                                  fg=COL["TEXT"], font=(F,12))
        self._mic_icon.pack(side="left", padx=1)
        self._mic_dot = tk.Label(dev_frame, text="●", bg=COL["PANEL"],
                                 fg=COL["GRN"], font=(F,10))
        self._mic_dot.pack(side="left")

        self._loc_icon = tk.Label(dev_frame, text="📡", bg=COL["PANEL"],
                                  fg=COL["TEXT"], font=(F,12))
        self._loc_icon.pack(side="left", padx=1)
        self._loc_dot = tk.Label(dev_frame, text="●", bg=COL["PANEL"],
                                 fg=COL["GRN"], font=(F,10))
        self._loc_dot.pack(side="left")


    # ── Stats cards ───────────────────────────────────────────────────────────
    def _build_stats(self, p):
        row = tk.Frame(p, bg=COL["BG"])
        row.pack(fill="x", padx=8, pady=8)
        row.columnconfigure(0, weight=1, uniform="half")
        row.columnconfigure(1, weight=1, uniform="half")

        cf = tk.Frame(row, bg=COL["CARD"])
        cf.grid(row=0, column=0, sticky="nsew", padx=(0,4))
        tk.Label(cf, text="CPU USAGE", bg=COL["CARD"], fg=COL["TXT2"],
                 font=(F,7)).pack(anchor="w", padx=10, pady=(8,2))
        self._cc = tk.Canvas(cf, width=90, height=90, bg=COL["CARD"], highlightthickness=0)
        self._cc.pack()
        self._ring(self._cc, 0)
        inf = tk.Frame(cf, bg=COL["CARD"])
        inf.pack(fill="x", padx=8, pady=(2,4))
        self._cc_lbl = tk.Label(inf, text="—", bg=COL["CARD"], fg=COL["TXT2"], font=(F,7))
        self._cc_lbl.pack(side="left")
        self._cf_lbl = tk.Label(inf, text="—", bg=COL["CARD"], fg=COL["TXT2"], font=(F,7))
        self._cf_lbl.pack(side="right")
        self._mk_btn(cf, "🧹  Clean Temp", COL["ACNT"], self.run_clean)\
            .pack(fill="x", padx=6, pady=(2,8), ipady=7)
        self._cpu_static()

        mf = tk.Frame(row, bg=COL["CARD"])
        mf.grid(row=0, column=1, sticky="nsew", padx=(4,0))
        tk.Label(mf, text="MEMORY", bg=COL["CARD"], fg=COL["TXT2"],
                 font=(F,7)).pack(anchor="w", padx=10, pady=(8,2))
        self._mp = tk.Label(mf, text="0%", bg=COL["CARD"], fg=COL["TEXT"],
                            font=(F,26,"bold"))
        self._mp.pack(anchor="w", padx=10)
        bh = tk.Frame(mf, bg=COL["CARD"])
        bh.pack(fill="x", padx=10, pady=(4,4))
        self._mb = tk.Canvas(bh, height=5, bg=COL["TXT3"], highlightthickness=0)
        self._mb.pack(fill="x")
        sf2 = tk.Frame(mf, bg=COL["CARD"])
        sf2.pack(fill="x", padx=7, pady=(0,4))
        for lbl, attr in [("Used","_mu"), ("Free","_mf"), ("Total","_mt")]:
            col = tk.Frame(sf2, bg=COL["CARD2"])
            col.pack(side="left", fill="x", expand=True, padx=1, ipady=3)
            tk.Label(col, text=lbl, bg=COL["CARD2"], fg=COL["TXT3"], font=(F,6)).pack()
            v = tk.Label(col, text="—", bg=COL["CARD2"], fg=COL["TEXT"], font=(F,8,"bold"))
            v.pack()
            setattr(self, attr, v)
        self._mk_btn(mf, "⚡  Boost Memory", COL["GRN"], self.run_boost)\
            .pack(fill="x", padx=6, pady=(2,8), ipady=7)

        op_frame = tk.Frame(p, bg=COL["BG"])
        op_frame.pack(fill="x", padx=8, pady=(0,4))
        self._op_status = tk.Label(op_frame, text="", bg=COL["BG"],
                                   fg=COL["TEXT"], font=(F,8), anchor="center")
        self._op_status.pack(fill="x")

    def _cpu_static(self):
        c = psutil.cpu_count(logical=False) or "?"
        t = psutil.cpu_count(logical=True)  or "?"
        self._cc_lbl.config(text=f"{c}C/{t}T")
        try:
            f = psutil.cpu_freq()
            if f:
                self._cf_lbl.config(text=f"{f.current/1000:.1f}GHz")
        except: pass

    def _ring(self, cvs, pct):
        cvs.delete("all")
        cx,cy,r,lw = 45,45,34,7
        cvs.create_arc(cx-r,cy-r,cx+r,cy+r, start=0, extent=359.9, style="arc",
                       outline=COL["TXT3"], width=lw)
        if pct > 0:
            col = COL["ACNT"] if pct<55 else COL["AMB"] if pct<80 else COL["RED"]
            cvs.create_arc(cx-r,cy-r,cx+r,cy+r, start=90, extent=-(pct/100*359.9),
                           style="arc", outline=col, width=lw)
        cvs.create_text(cx, cy-5, text=f"{pct:.0f}%", fill=COL["TEXT"],
                        font=(F,16,"bold"), anchor="center")
        cvs.create_text(cx, cy+12, text="CPU", fill=COL["TXT2"],
                        font=(F,7), anchor="center")

    def _bar(self, pct):
        self._mb.update_idletasks()
        w = self._mb.winfo_width()
        if w < 4: return
        self._mb.delete("all")
        self._mb.create_rectangle(0,0,w,5, fill=COL["TXT3"], outline="")
        fw = max(0, int(w*pct/100))
        if fw:
            c = COL["GRN"] if pct<55 else COL["AMB"] if pct<80 else COL["RED"]
            self._mb.create_rectangle(0,0,fw,5, fill=c, outline="")

    # ── Network panel ─────────────────────────────────────────────────────────
    def _build_net(self, p):
        nf = tk.Frame(p, bg=COL["BG"])
        nf.pack(fill="both", expand=True)
        hdr = tk.Frame(nf, bg=COL["PANEL"])
        hdr.pack(fill="x", padx=8, pady=(7,0))
        tk.Label(hdr, text="Connections & Ports #GitHub @Gauravxo", bg=COL["PANEL"],
                 fg=COL["TEXT"], font=(F,9,"bold")).pack(side="left")
        self._cnt = tk.Label(hdr, text="", bg=COL["PANEL"], fg=COL["TXT2"], font=(F,7))
        self._cnt.pack(side="right", pady=3)
        ft = tk.Frame(nf, bg=COL["PANEL"])
        ft.pack(fill="x", padx=8, pady=(4,6))
        for nm in ("ALL","LISTEN","ESTABLISHED","TIME_WAIT","CLOSE_WAIT"):
            b = tk.Label(ft, text=nm, cursor="hand2",
                         bg=COL["CARD2"] if nm=="ALL" else COL["CARD"],
                         fg=COL["TEXT"] if nm=="ALL" else COL["TXT2"],
                         font=(F,7), padx=5, pady=2)
            b.pack(side="left", padx=1)
            b.bind("<Button-1>", lambda e, n=nm: self._flt(n))
            self._fbtns[nm] = b
        cols, widths, heads = ("pid","process","port","remote","status"), (40,108,48,126,60), ("PID","Process","Port","Remote","Status")
        tf = tk.Frame(nf, bg=COL["BG"])
        tf.pack(fill="both", expand=True, padx=8, pady=(0,4))
        self._tv = ttk.Treeview(tf, columns=cols, show="headings", height=9,
                                style="W.Treeview", selectmode="browse")
        for c,w,h in zip(cols, widths, heads):
            self._tv.heading(c, text=h, command=lambda x=c: self._sort(x))
            self._tv.column(c, width=w, minwidth=w, stretch=False)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self._tv.yview,
                            style="S.Vertical.TScrollbar")
        self._tv.configure(yscrollcommand=vsb.set)
        self._tv.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")

        for st,cl in S_CLR.items():
            self._tv.tag_configure(st, foreground=cl)
        self._tv.tag_configure("r0", background=COL["CARD"])
        self._tv.tag_configure("r1", background=COL["CARD2"])
        self._tv.tag_configure("danger",
            foreground=COL["RED"],
            background=COL["DANGER_BG"],
            font=(FM,8,"bold"))
        self._tv.tag_configure("warning",
            foreground=COL["WARN"],
            font=(FM,8,"bold"))

        self._tv.bind("<<TreeviewSelect>>", self._sel)
        self._ctx_menu = tk.Menu(self, tearoff=0)
        self._ctx_menu.add_command(label="End Process", command=self._end_selected_process)
        self._tv.bind("<Button-3>", self._popup_context)

        self._det = tk.Label(nf, text="  Click a row for details", bg=COL["BG"],
                             fg=COL["TXT3"], font=(F,7), anchor="w")
        self._det.pack(fill="x", padx=10, pady=(0,3))

    def _flt(self, name):
        self.flt = name
        for n,b in self._fbtns.items():
            b.config(bg=COL["CARD2"] if n==name else COL["CARD"],
                     fg=COL["TEXT"] if n==name else COL["TXT2"])
        self._redraw()

    def _sort(self, col):
        self._sr = (not self._sr) if self._sc == col else False
        self._sc = col
        self._redraw()

    def _sel(self, _):
        sel = self._tv.selection()
        if not sel: return
        v = self._tv.item(sel[0], "values")
        self._det.config(text=f"  PID {v[0]}  ·  {v[1]}  ·  Port {v[2]}  ·  {v[3]}  ·  {v[4]}")

    def _popup_context(self, event):
        sel = self._tv.selection()
        if not sel: return
        self._ctx_pid = int(self._tv.item(sel[0], "values")[0])
        self._ctx_menu.tk_popup(event.x_root, event.y_root)

    def _end_selected_process(self):
        pid = self._ctx_pid
        try:
            psutil.Process(pid).terminate()
            self._set_op_status(f"✓ Process {pid} terminated", COL["GRN"])
        except Exception as e:
            self._set_op_status(f"✗ Can't terminate PID {pid}: {e}", COL["RED"])
        self.after(5000, lambda: self._set_op_status("", ""))

    def _security_analyse(self, connections):
        risk = 0
        for c in connections:
            c["_danger"] = False
            c["_warn"] = False
            if c["st"] == "LISTEN":
                try:
                    port = int(c["lp"])
                    if port in DANGER_PORTS:
                        c["_danger"] = True
                        risk = max(risk, 2)
                except: pass
            proc_lower = c["proc"].lower().strip()
            for bad in SUSPICIOUS_PROCS:
                if bad in proc_lower:
                    c["_danger"] = True
                    risk = max(risk, 2)
                    break
            if c["st"] == "ESTABLISHED" and c["ra"] != "—":
                ip = c["ra"].split(":")[-1] if ":" in c["ra"] else c["ra"]
                if ip.startswith("[") and ip.endswith("]"):
                    ip = ip[1:-1]
                if not ip.startswith(("10.","192.168.","172.","127.")) and ip != "::1":
                    c["_warn"] = True
                    risk = max(risk, 1)
        return risk

    def _redraw(self):
        data = [c for c in self.conns if self.flt == "ALL" or c["st"] == self.flt]
        if self._sc:
            km = {"pid":"pid","process":"proc","port":"lp","remote":"ra","status":"st"}
            k  = km.get(self._sc, "st")
            data = sorted(data, key=lambda x: str(x.get(k, "")), reverse=self._sr)
        self._tv.delete(*self._tv.get_children())

        risk = self._security_analyse(data)

        if risk == 0:
            self._sec_lbl.config(text="🔒", fg=COL["GRN"])
        elif risk == 1:
            self._sec_lbl.config(text="⚠", fg=COL["AMB"])
        else:
            self._sec_lbl.config(text="🔴", fg=COL["RED"])

        for i, c in enumerate(data):
            row_tag = f"r{i%2}"
            if c.get("_danger"):
                tags = ("danger", row_tag)
            elif c.get("_warn"):
                tags = ("warning", row_tag)
            else:
                st = c["st"] if c["st"] in S_CLR else "NONE"
                tags = (st, row_tag)
            self._tv.insert("", "end",
                values=(c["pid"], c["proc"], c["lp"], c["ra"], c["st"]),
                tags=tags)
        self._cnt.config(text=f"{len(data)}/{len(self.conns)}")

    def _build_bottom(self, p):
        bot = tk.Frame(p, bg=COL["BG"])
        bot.pack(fill="x")
        self._st = tk.Label(bot, text="  All systems normal",
                            bg=COL["BG"], fg=COL["TXT3"], font=(F,7), anchor="w")
        self._st.pack(side="left", fill="x", expand=True, padx=6, pady=5)
        
        gr = tk.Label(bot, text="◢", bg=COL["BG"], fg=COL["TXT3"],
                      font=(F,12), cursor="size_nw_se")
        gr.pack(side="right", padx=4, pady=2)

    def _set_op_status(self, text, fg):
        self._op_status.config(text=text, fg=fg or COL["TEXT"])

    def _mk_btn(self, parent, text, fg, cmd):
        f  = tk.Frame(parent, bg=COL["CARD2"], cursor="hand2")
        lb = tk.Label(f, text=text, bg=COL["CARD2"], fg=fg,
                      font=(F,8,"bold"), cursor="hand2")
        lb.pack()
        for w in (f, lb):
            w.bind("<Button-1>", lambda e: cmd())
            w.bind("<Enter>",    lambda e: (f.config(bg=COL["CARD"]), lb.config(bg=COL["CARD"])))
            w.bind("<Leave>",    lambda e: (f.config(bg=COL["CARD2"]), lb.config(bg=COL["CARD2"])))
        return f

    # ── Device status (camera, mic, location) ─────────────────────────────────
    @staticmethod
    def _is_capability_in_use(capability):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 rf"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\{capability}",
                                 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)
                    try:
                        start, _ = winreg.QueryValueEx(subkey, "LastUsedTimeStart")
                        stop, _  = winreg.QueryValueEx(subkey, "LastUsedTimeStop")
                        if start > 0 and stop == 0:
                            winreg.CloseKey(subkey)
                            winreg.CloseKey(key)
                            return True
                    except:
                        pass
                    winreg.CloseKey(subkey)
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except:
            pass
        return False

    def _t_devices(self):
        while self.running:
            cam = mic = loc = False
            if IS_WIN:
                try:
                    cam = self._is_capability_in_use("webcam")
                except: pass
                try:
                    mic = self._is_capability_in_use("microphone")
                except: pass
                try:
                    loc = self._is_capability_in_use("location")
                except: pass
            self.after(0, self._update_device_indicators, cam, mic, loc)
            time.sleep(2)

    def _update_device_indicators(self, cam, mic, loc):
        self._cam_active, self._mic_active, self._loc_active = cam, mic, loc
        self._cam_dot.config(fg=COL["RED"] if cam else COL["GRN"])
        self._mic_dot.config(fg=COL["RED"] if mic else COL["GRN"])
        self._loc_dot.config(fg=COL["RED"] if loc else COL["GRN"])

    # ── Background threads ────────────────────────────────────────────────────
    def _t_cpu_mem(self):
        while self.running:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            self.after(0, self._a_cpu, cpu)
            self.after(0, self._a_mem, mem)

    def _t_net(self):
        while self.running:
            data = self._fetch()
            self.after(0, self._a_net, data)
            time.sleep(2)

    def _a_cpu(self, pct):
        self._lc = pct
        self._ring(self._cc, pct)

    def _a_mem(self, m):
        pct = m.percent
        self._lm = pct
        self._mp.config(text=f"{pct:.0f}%")
        self._bar(pct)
        self._mu.config(text=f"{m.used/1e9:.1f}G")
        self._mf.config(text=f"{m.available/1e9:.1f}G")
        self._mt.config(text=f"{m.total/1e9:.0f}G")

    def _a_net(self, data):
        self.conns = data
        self._redraw()

    def _fetch(self):
        out, cache = [], {}
        try:
            for c in psutil.net_connections(kind="all"):
                pid = c.pid or 0
                if pid not in cache:
                    try: cache[pid] = psutil.Process(pid).name() if pid else "System"
                    except: cache[pid] = "—"
                lp = str(c.laddr.port) if c.laddr else "—"
                ra = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "—"
                st = (c.status or "NONE").upper()
                out.append({"pid": pid, "proc": cache[pid][:16], "lp": lp, "ra": ra, "st": st})
        except: pass
        pri = {"LISTEN": 0, "ESTABLISHED": 1}
        return sorted(out, key=lambda x: (pri.get(x["st"], 9), x["proc"].lower()))

    # ── Clean & Boost ─────────────────────────────────────────────────────────
    def run_clean(self):
        self._set_op_status("⏳ Cleaning…", COL["AMB"])
        def _w():
            try:
                drive = os.environ.get("SystemDrive", "C:") + "\\"
                try: before = psutil.disk_usage(drive).free
                except: before = None
                def clean_dir(path):
                    if not os.path.isdir(path): return
                    for root, dirs, files in os.walk(path, topdown=True, followlinks=False, onerror=lambda e: None):
                        for f in files:
                            try: os.remove(os.path.join(root, f))
                            except: pass
                targets = [
                    tempfile.gettempdir(),
                    os.path.expandvars(r"%WINDIR%\Temp"),
                    os.path.expandvars(r"%WINDIR%\Prefetch"),
                    os.path.expandvars(r"%WINDIR%\SoftwareDistribution\Download"),
                    os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Recent"),
                    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\DirectX Shader Cache"),
                    os.path.expandvars(r"%LOCALAPPDATA%\CrashDumps"),
                    os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\WER\ReportQueue"),
                ]
                thumb = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Explorer")
                if os.path.isdir(thumb):
                    for f in os.listdir(thumb):
                        if f.startswith(("thumbcache","iconcache")):
                            try: os.remove(os.path.join(thumb,f))
                            except: pass
                browser_paths = []
                for browser in ["Google","Microsoft"]:
                    base = os.path.expandvars(rf"%LOCALAPPDATA%\{browser}")
                    if os.path.isdir(base):
                        for sub in os.listdir(base):
                            for cache in ["Cache","Code Cache"]:
                                browser_paths.append(os.path.join(base, sub, "User Data", "Default", cache))
                ff = os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")
                if os.path.isdir(ff):
                    for profile in os.listdir(ff):
                        browser_paths.append(os.path.join(ff, profile, "cache2"))
                for p in browser_paths: clean_dir(p)
                for p in targets: clean_dir(p)
                try:
                    subprocess.run(["ipconfig","/flushdns"], capture_output=True, timeout=5,
                                   creationflags=subprocess.CREATE_NO_WINDOW if IS_WIN else 0)
                except: pass
                if before is not None:
                    try: after = psutil.disk_usage(drive).free; freed = max(0, after-before)
                    except: freed = 0
                else: freed = 0
                freed_mb = freed/(1024*1024)
                self.after(0, lambda: self._set_op_status(
                    f"✓ Cleaned {freed_mb:.1f} MB — emptying Recycle Bin…", COL["AMB"]))
                def _empty_bin():
                    try:
                        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x0007)
                        self.after(0, lambda: self._set_op_status(
                            f"✓ Cleaned {freed_mb:.1f} MB", COL["GRN"]))
                    except:
                        self.after(0, lambda: self._set_op_status(
                            f"✓ Cleaned {freed_mb:.1f} MB (Recycle Bin needs Admin rights)", COL["GRN"]))
                    self.after(7000, lambda: self._set_op_status("", ""))
                threading.Thread(target=_empty_bin, daemon=True).start()
            except Exception as e:
                self.after(0, lambda: self._set_op_status(f"✗ Clean failed: {e}", COL["RED"]))
                self.after(7000, lambda: self._set_op_status("", ""))
        threading.Thread(target=_w, daemon=True).start()

    def run_boost(self):
        self._set_op_status("⚡ Freeing memory…", COL["AMB"])
        def _w():
            before = psutil.virtual_memory().available
            gc.collect()
            if IS_WIN:
                try:
                    for proc in psutil.process_iter(["pid"]):
                        try:
                            h = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, proc.pid)
                            if h:
                                ctypes.windll.psapi.EmptyWorkingSet(h)
                                ctypes.windll.kernel32.CloseHandle(h)
                        except: pass
                except: pass
            time.sleep(0.6)
            freed = max(0, psutil.virtual_memory().available - before)
            freed_mb = freed/(1024*1024)
            self.after(0, lambda: self._set_op_status(f"✓ Freed ~{freed_mb:.0f} MB", COL["GRN"]))
            self.after(6000, lambda: self._set_op_status("", ""))
        threading.Thread(target=_w, daemon=True).start()

    # ── Edge resize ───────────────────────────────────────────────────────────
    def _get_edge(self, x, y):
        w, h = self.winfo_width(), self.winfo_height()
        edge = ""
        if x <= EDGE_WIDTH:   edge += "w"
        elif x >= w - EDGE_WIDTH: edge += "e"
        if y <= EDGE_WIDTH:   edge += "n"
        elif y >= h - EDGE_WIDTH: edge += "s"
        return edge or None

    def _on_motion(self, event):
        edge = self._get_edge(event.x, event.y)
        if edge in ("n", "s"): self.config(cursor="sb_v_double_arrow")
        elif edge in ("e", "w"): self.config(cursor="sb_h_double_arrow")
        elif edge in ("nw", "se"): self.config(cursor="size_nw_se")
        elif edge in ("ne", "sw"): self.config(cursor="size_ne_sw")
        else: self.config(cursor="arrow")

    def _on_button_down(self, event):
        edge = self._get_edge(event.x, event.y)
        if edge:
            self._resize_edge = edge
            self._resize_start_geom = (self.winfo_x(), self.winfo_y(),
                                       self.winfo_width(), self.winfo_height())
            self._resize_start_root = (event.x_root, event.y_root)
            self._drag_active = False
        else:
            self._resize_edge = None
            self._drag_active = True
            self._drag_start_x = event.x_root - self.winfo_x()
            self._drag_start_y = event.y_root - self.winfo_y()

    def _on_button_motion(self, event):
        if self._resize_edge:
            dx = event.x_root - self._resize_start_root[0]
            dy = event.y_root - self._resize_start_root[1]
            x, y, w, h = self._resize_start_geom
            if "e" in self._resize_edge: w = max(380, w + dx)
            if "s" in self._resize_edge: h = max(500, h + dy)
            if "w" in self._resize_edge:
                w = max(380, w - dx)
                x = self._resize_start_geom[0] + dx
            if "n" in self._resize_edge:
                h = max(500, h - dy)
                y = self._resize_start_geom[1] + dy
            self.geometry(f"{w}x{h}+{x}+{y}")
        elif self._drag_active:
            nx = event.x_root - self._drag_start_x
            ny = event.y_root - self._drag_start_y
            self.geometry(f"+{nx}+{ny}")

    def _on_button_release(self, event):
        self._resize_edge = None
        self._drag_active = False
        self._apply_rounded_corners(CORNER_RADIUS)

    # ── Misc ──────────────────────────────────────────────────────────────────
    def _ttk_styles(self):
        s = ttk.Style()
        s.theme_use("default")
        s.configure("W.Treeview",
            background=COL["CARD"], fieldbackground=COL["CARD"],
            foreground=COL["TEXT"], rowheight=20, font=(FM,8), borderwidth=0)
        s.configure("W.Treeview.Heading",
            background=COL["CARD2"], foreground=COL["TXT2"],
            font=(F,8,"bold"), relief="flat", borderwidth=0)
        s.map("W.Treeview",
            background=[("selected", "#1a3a5c")], foreground=[("selected", COL["TEXT"])])
        s.configure("S.Vertical.TScrollbar",
            background=COL["CARD2"], troughcolor=COL["CARD"],
            arrowcolor=COL["TXT3"], borderwidth=0, width=7)

    def _quit(self):
        self.running = False
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()