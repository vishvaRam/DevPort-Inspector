# DevPort Inspector & Zombie Process Killer ⚡

[![Release](https://img.shields.io/badge/Release-v1.0.0-7aa2f7?style=for-the-badge&logo=github)](https://github.com/vishvaRam/devport-inspector/releases/latest)
[![Platform](<https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-bb9af7?style=for-the-badge&logo=linux&logoColor=white>)](https://github.com/vishvaRam/devport-inspector/releases)
[![Python](https://img.shields.io/badge/Python-3.9%2B-7dcfff?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/UI-PyQt6-f7768e?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-9ece6a?style=for-the-badge)](LICENSE)

A modern, lightning-fast desktop GUI utility built with **Python 3** and **PyQt6** for inspecting active TCP listening ports, identifying lingering developer servers, and terminating or restarting zombie processes with a single click.

---

## 📥 Downloads (v1.0.0)

Grab the pre-built, standalone binaries directly from the [GitHub Releases](https://github.com/vishvaRam/devport-inspector/releases/latest) page:

| Platform             | Download Link                                                                                                                                     | Description                              |
| :------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------ | :--------------------------------------- |
| **🐧 Linux**   | [`devport-inspector_1.0.0_amd64.deb`](https://github.com/vishvaRam/devport-inspector/releases/download/v1.0.0/devport-inspector_1.0.0_amd64.deb) | Debian / Ubuntu native package installer |
| **🪟 Windows** | [`DevPortInspector_1.0.0.exe`](https://github.com/vishvaRam/devport-inspector/releases/download/v1.0.0/DevPortInspector_1.0.0.exe)               | Portable single-file executable          |

---

## 🌟 Key Features

- **⚡ Real-Time Port Inspection**

  - Continuous asynchronous background scanning of all active TCP `LISTEN` sockets without UI freeze.
  - Displays Port Number, Process Name, PID, RSS Memory Consumption (MB), and Process Start Time.
- **🏷️ Intelligent Service Tagging**

  - Preloaded with known development defaults (`3000` React/Next.js, `5173` Vite, `8000` FastAPI/Django, `5432` PostgreSQL, `6379` Redis, `11434` Ollama, `1234` LM Studio, etc.).
  - **Inline Editing**: Double-click any tag field to add or edit custom labels; stored permanently in `port_tags.json`.
- **💀 One-Click Zombie Process Killer**

  - Effortlessly terminate orphaned or stuck development servers occupying your required ports.
  - Safe, two-tier cross-platform termination: sends graceful `SIGTERM`, falling back to forceful `SIGKILL` (Linux) / `taskkill /F /T /PID` (Windows).
- **🔄 Instant Process Restart**

  - Automatically captures the working directory (`cwd`) and complete execution arguments (`cmdline`).
  - Restarts the process in a clean, detached session with one click.
- **🛡️ Built-in System Protection**

  - Automatically flags and locks critical operating system processes (`svchost.exe`, `lsass.exe`, `system`, PIDs `<= 4`) to prevent accidental system instability.
  - **Hide System Ports** toggle keeps your view focused strictly on user-space dev servers.
- **🔍 Live Filter & Search**

  - Instant filtering across port numbers, service names, PIDs, and custom tags.
- **🎨 Sleek Tokyo Night Dark Theme**

  - Ergonomic, high-contrast dark theme engineered for long developer sessions.

---

## 📁 Project Structure

```plaintext
devport-inspector/
├── assets/                 # App icon files (.ico and .png)
│   ├── icon.ico
│   └── icon.png
├── scripts/
│   └── build_deb.sh        # Automated Debian (.deb) packaging script
├── Test/
│   └── ports.py            # Multi-threaded dummy TCP socket test suite
├── app.py                  # Main PyQt6 application & process manager engine
├── generate_icons.py       # Programmatic vector icon generator
├── port_tags.json          # Persistent custom user port tags
├── requirements.txt        # Python dependency manifest
└── README.md               # Project documentation
```

---

## 🚀 Quick Start (Running from Source)

### 1. Clone the Repository

```bash
git clone https://github.com/vishvaRam/devport-inspector.git
cd devport-inspector
```

### 2. Set Up Virtual Environment

```bash
# Standard venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

*Or with [`uv`](https://github.com/astral-sh/uv) (recommended):*

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 3. Launch the Application

```bash
python app.py
```

---

## 🧪 Testing with Dummy Servers

A built-in dummy server script is provided in `Test/ports.py` to simulate active listening ports (`4000`, `4001`, `7070`, `9999`):

```bash
python Test/ports.py
```

Open **DevPort Inspector** to see the test ports appear live, test the restart action, or terminate them with the **Kill** button.

---

## 📦 Building Standalone Binaries

### 🐧 Build Linux `.deb` Package

```bash
chmod +x ./scripts/build_deb.sh
./scripts/build_deb.sh
```

Install the compiled package:

```bash
sudo apt install ./releases/devport-inspector_1.0.0_amd64.deb
```

### 🪟 Build Windows `.exe` Executable

Run PyInstaller via PowerShell or Command Prompt:

```bash
pyinstaller --noconfirm --onefile --windowed \
    --name "DevPortInspector_1.0.0" \
    --specpath "build" \
    --distpath "releases" \
    --icon "$(pwd -W)/assets/icon.ico" \
    --hidden-import "psutil" \
    --hidden-import "PyQt6.QtCore" \
    --hidden-import "PyQt6.QtGui" \
    --hidden-import "PyQt6.QtWidgets" \
    --add-data "$(pwd -W)/assets;assets" \
    app.py
```

The resulting standalone executable will be located in `releases/DevPortInspector_1.0.0.exe`.

---

## ⚙️ Configuration & Tag Management

Custom tags are saved locally in `port_tags.json`. You can modify them directly inside the app by **double-clicking on the Service / Tag column** for any port, or by editing `port_tags.json`:

```json
{
  "3000": "React / Next.js",
  "5173": "Vite",
  "8000": "FastAPI / Django",
  "5432": "PostgreSQL",
  "6379": "Redis",
  "11434": "Ollama"
}
```

---

## 📄 License

This project is open-source software licensed under the [MIT License](LICENSE).
