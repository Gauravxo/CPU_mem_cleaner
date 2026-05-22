# 🖥️ CPU & mem – Windows 11 System Monitor Widget

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Windows](https://img.shields.io/badge/platform-Windows%2010%2F11-blue?logo=windows)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue?logo=python)](https://python.org)

**A beautiful, dark‑themed system monitor widget for Windows 11, packed with live metrics, security insights, and privacy indicators – all in a tiny, rounded‑corner overlay.**  

No console. No clutter. Just pure system awareness at a glance.  


---

## ✨ Features

- **📊 Live CPU & Memory**  
  Real‑time usage rings, memory bar, core/thread info, and frequency display.

- **🌐 Network Connections**  
  View all active connections with **PID, process, local/remote ports, and status**.  
  Filter by state (LISTEN, ESTABLISHED, etc.) and sort columns.

- **🔒 Security Analysis**  
  Automatic risk assessment:  
  - 🔴 **Dangerous listening ports** (RDP, SMB, FTP…)  
  - 🚨 **Suspicious processes** (mimikatz, netcat, powershell…)  
  - ⚠️ **Unexpected external connections**  
  Security indicator shows the overall threat level.

- **📷🎤📍 Privacy Sensors**  
  Live dots (🟢/🔴) indicate if **camera, microphone, or location** is currently being used by any app.  
  *Uses Windows Capability Access Manager – no extra tools required.*

- **🧹 System Clean‑Up**  
  One‑click “Clean Temp” removes junk from temporary folders, browser caches, Windows updates, DNS flush, and empties the Recycle Bin.

- **⚡ Memory Booster**  
  “Boost Memory” aggressively frees RAM by calling garbage collection and trimming working sets of background processes.

- **🎨 Dark Theme Only**  
  Sleek, modern dark palette that blends with Windows 11 aesthetics. No unnecessary light mode.

- **🖱️ Fully Interactive**  
  - Drag to move anywhere on the desktop.  
  - Resize from any edge or corner.  
  - Rounded corners that adapt after resizing.  
  - Right‑click on a network row to **end the process**.

- **🔒 Single Instance**  
  Only one widget can run. Trying to open a second one brings the existing window to the front.

- **🚫 No Console Window**  
  Runs silently as a `.pyw` file – no terminal flash, no command prompt.

- **📌 Always on Top?**  
  You can toggle (or keep it as a normal window) – pinning is just a line edit away.

---

## 📸 Screenshots

| Dashboard | Network Details |
|-----------|-----------------|
| ![Main View](https://github.com/Gauravxo/CPU_mem_cleaner/blob/main/CPU_MEM.png) 

---

## 🚀 Getting Started

### Prerequisites

- **Windows 10 or Windows 11**  
- **Python 3.8+** (with Tkinter – usually included)  
- **psutil** (`pip install psutil`)  
- **Administrator rights** (optional, only for Recycle Bin emptying and some process management)

### Installation

```bash
https://github.com/Gauravxo/CPU_mem_cleaner.git
cd CPU_mem_cleaner
pip install -r requirements.txt
