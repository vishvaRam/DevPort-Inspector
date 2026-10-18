import sys
import os
import json
import signal
import platform
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional

import psutil
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QCheckBox,
    QMessageBox,
    QInputDialog,
    QStatusBar,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TAGS_FILE = os.path.join(BASE_DIR, "port_tags.json")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

DEFAULT_TAGS = {
    3000: "React / Next.js",
    3001: "Dev Server",
    5000: "Flask / .NET",
    5050: "PgAdmin / App",
    5173: "Vite",
    5432: "PostgreSQL",
    3306: "MySQL / MariaDB",
    27017: "MongoDB",
    6379: "Redis",
    6333: "Qdrant Vector DB",
    8000: "FastAPI / Django",
    8080: "Tomcat / Proxy",
    8081: "Metro / React Native",
    8501: "Streamlit",
    8888: "Jupyter",
    11434: "Ollama",
    1234: "LM Studio",
}

IS_WINDOWS = platform.system().lower() == "windows"

WINDOWS_CORE_SYSTEM = {
    "system",
    "svchost.exe",
    "lsass.exe",
    "wininit.exe",
    "services.exe",
    "spoolsv.exe",
    "smss.exe",
    "csrss.exe",
}


def get_app_icon() -> QIcon:
    """Returns platform-specific QIcon with graceful fallback."""
    icon_filename = "icon.ico" if IS_WINDOWS else "icon.png"
    icon_path = os.path.join(ASSETS_DIR, icon_filename)

    # Secondary fallback if preferred format is absent
    if not os.path.exists(icon_path):
        alt_filename = "icon.png" if IS_WINDOWS else "icon.ico"
        icon_path = os.path.join(ASSETS_DIR, alt_filename)

    if os.path.exists(icon_path):
        return QIcon(icon_path)
    return QIcon()


def load_tags() -> Dict[int, str]:
    tags = DEFAULT_TAGS.copy()
    if os.path.exists(TAGS_FILE):
        try:
            with open(TAGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                for k, v in saved.items():
                    tags[int(k)] = str(v)
        except Exception:
            pass
    return tags


def save_tags(tags: Dict[int, str]):
    try:
        with open(TAGS_FILE, "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in tags.items()}, f, indent=2)
    except Exception as e:
        print(f"Failed to save tags: {e}")


class PortScannerThread(QThread):
    scan_completed = pyqtSignal(list)

    def __init__(self, port_tags: Dict[int, str]):
        super().__init__()
        self.port_tags = port_tags

    def update_tags(self, tags: Dict[int, str]):
        self.port_tags = tags

    def run(self):
        records = []
        try:
            connections = psutil.net_connections(kind="tcp")
        except (psutil.AccessDenied, PermissionError):
            connections = []

        seen_keys = set()

        for conn in connections:
            if conn.status == psutil.CONN_LISTEN:
                laddr = conn.laddr
                port = laddr.port
                pid = conn.pid

                dedup_key = (port, pid)
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)

                p_name = "N/A"
                ram_mb = 0.0
                start_time_str = "N/A"
                cmdline = []
                cwd = None

                if pid:
                    try:
                        proc = psutil.Process(pid)
                        p_name = proc.name()
                        mem_info = proc.memory_info()
                        ram_mb = round(mem_info.rss / (1024 * 1024), 1)
                        create_time = proc.create_time()
                        start_time_str = datetime.fromtimestamp(create_time).strftime(
                            "%H:%M:%S"
                        )

                        try:
                            cmdline = proc.cmdline()
                        except (psutil.AccessDenied, psutil.ZombieProcess):
                            cmdline = []

                        try:
                            cwd = proc.cwd()
                        except (psutil.AccessDenied, psutil.ZombieProcess):
                            cwd = None

                    except (
                        psutil.NoSuchProcess,
                        psutil.AccessDenied,
                        psutil.ZombieProcess,
                    ):
                        p_name = "[Privileged / System]"

                tag = self.port_tags.get(port, "")
                records.append(
                    {
                        "port": port,
                        "address": f"{laddr.ip}:{laddr.port}",
                        "pid": pid if pid else -1,
                        "name": p_name,
                        "ram": ram_mb,
                        "started": start_time_str,
                        "tag": tag,
                        "cmdline": cmdline,
                        "cwd": cwd,
                    }
                )

        records.sort(key=lambda x: x["port"])
        self.scan_completed.emit(records)


def terminate_process_cross_platform(pid: int) -> bool:
    if pid <= 0:
        return False

    try:
        proc = psutil.Process(pid)
        proc.terminate()
        try:
            proc.wait(timeout=1.5)
            return True
        except psutil.TimeoutExpired:
            if IS_WINDOWS:
                os.system(f"taskkill /F /T /PID {pid} >nul 2>&1")
            else:
                proc.send_signal(signal.SIGKILL)
            return True
    except psutil.NoSuchProcess:
        return True
    except (psutil.AccessDenied, PermissionError):
        if IS_WINDOWS:
            return os.system(f"taskkill /F /T /PID {pid} >nul 2>&1") == 0
        else:
            try:
                os.kill(pid, signal.SIGKILL)
                return True
            except Exception:
                return False
    except Exception:
        return False


def restart_process_cross_platform(
    pid: int, cmdline: List[str], cwd: Optional[str]
) -> bool:
    if not cmdline:
        return False

    success = terminate_process_cross_platform(pid)
    if not success:
        return False

    try:
        if IS_WINDOWS:
            flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            subprocess.Popen(
                cmdline,
                cwd=cwd,
                creationflags=flags,
                shell=False,
                close_fds=True,
            )
        else:
            subprocess.Popen(
                cmdline,
                cwd=cwd,
                start_new_session=True,
                close_fds=True,
            )
        return True
    except Exception as e:
        print(f"Failed to restart process: {e}")
        return False


class DevPortInspector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DevPort Inspector & Zombie Process Killer")
        self.resize(920, 560)
        self.setMinimumSize(750, 420)

        # Apply Window Icon
        app_icon = get_app_icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        self.port_tags = load_tags()
        self.current_data: List[Dict[str, Any]] = []
        self.search_term = ""

        self.scanner_thread = PortScannerThread(self.port_tags)
        self.scanner_thread.scan_completed.connect(self.on_scan_completed)

        self.init_ui()
        self.apply_theme()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.trigger_scan)
        self.refresh_timer.start(3000)

        self.trigger_scan()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(14, 14, 14, 10)
        main_layout.setSpacing(10)

        # Header bar
        header_layout = QHBoxLayout()
        title_label = QLabel("⚡ DevPort Inspector")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.clicked.connect(self.trigger_scan)
        header_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(header_layout)

        # Control row
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "🔍 Search port number, process name, PID, or tag..."
        )
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)

        self.chk_hide_system = QCheckBox("Hide System Ports")
        self.chk_hide_system.setChecked(True)
        self.chk_hide_system.toggled.connect(self.render_table)
        self.chk_hide_system.setStyleSheet(
            "color: #7aa2f7; font-weight: bold; margin-left: 6px;"
        )
        search_layout.addWidget(self.chk_hide_system)

        main_layout.addLayout(search_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "Port",
                "Service / Tag ✎",
                "PID",
                "Process Name",
                "RAM (MB)",
                "Started",
                "Actions",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeMode.Fixed
        )
        self.table.setColumnWidth(6, 190)

        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        main_layout.addWidget(self.table)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1b26;
            }
            QLabel {
                color: #c0caf5;
            }
            QLineEdit {
                background-color: #24283b;
                border: 1px solid #414868;
                border-radius: 6px;
                color: #c0caf5;
                padding: 7px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #7aa2f7;
            }
            QCheckBox {
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #414868;
                background-color: #24283b;
            }
            QCheckBox::indicator:checked {
                background-color: #7aa2f7;
                border: 1px solid #7aa2f7;
            }
            QPushButton {
                background-color: #24283b;
                border: 1px solid #414868;
                border-radius: 6px;
                color: #c0caf5;
                padding: 6px 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2f354f;
                border-color: #565f89;
            }
            QTableWidget {
                background-color: #1f2335;
                alternate-background-color: #1a1b26;
                color: #c0caf5;
                gridline-color: #292e42;
                border: 1px solid #292e42;
                border-radius: 6px;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #283457;
            }
            QHeaderView::section {
                background-color: #16161e;
                color: #7aa2f7;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QStatusBar {
                color: #7982a9;
                background-color: #16161e;
            }
        """)

    def trigger_scan(self):
        if not self.scanner_thread.isRunning():
            self.scanner_thread.update_tags(self.port_tags)
            self.scanner_thread.start()

    def on_search_changed(self, text: str):
        self.search_term = text.strip().lower()
        self.render_table()

    def on_scan_completed(self, records: List[Dict[str, Any]]):
        self.current_data = records
        self.render_table()
        self.status_bar.showMessage(
            f"Total listening ports: {len(records)} | System: {platform.system()}"
        )

    def render_table(self):
        filtered_records = []
        hide_system = self.chk_hide_system.isChecked()

        for item in self.current_data:
            port = item["port"]
            proc_lower = item["name"].lower()
            tag = item["tag"]

            if hide_system and not tag:
                if port < 1024:
                    continue
                if proc_lower in WINDOWS_CORE_SYSTEM:
                    continue
                if port >= 49152 and (
                    "svchost" in proc_lower
                    or "services" in proc_lower
                    or "lsass" in proc_lower
                ):
                    continue

            if self.search_term:
                searchable = f"{port} {item['name']} {item['pid']} {tag}".lower()
                if self.search_term not in searchable:
                    continue

            filtered_records.append(item)

        self.table.setRowCount(len(filtered_records))

        for row, rec in enumerate(filtered_records):
            port = rec["port"]
            proc_lower = rec["name"].lower()

            # Port
            port_item = QTableWidgetItem(str(port))
            port_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            port_item.setForeground(QColor("#bb9af7"))
            port_item.setFlags(port_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, port_item)

            # Service / Tag
            tag_text = self.port_tags.get(port, "")
            display_text = tag_text if tag_text else "+ Add Tag"
            tag_item = QTableWidgetItem(display_text)
            if tag_text:
                tag_item.setForeground(QColor("#7dcfff"))
            else:
                tag_item.setForeground(QColor("#565f89"))
            tag_item.setFlags(tag_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, tag_item)

            # PID
            pid_str = str(rec["pid"]) if rec["pid"] > 0 else "—"
            pid_item = QTableWidgetItem(pid_str)
            pid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            pid_item.setFlags(pid_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, pid_item)

            # Process Name
            name_item = QTableWidgetItem(rec["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if rec["pid"] <= 0:
                name_item.setForeground(QColor("#7982a9"))
            self.table.setItem(row, 3, name_item)

            # RAM
            ram_item = QTableWidgetItem(f"{rec['ram']} MB" if rec["ram"] > 0 else "—")
            ram_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            ram_item.setFlags(ram_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, ram_item)

            # Started
            start_item = QTableWidgetItem(rec["started"])
            start_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            start_item.setFlags(start_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, start_item)

            # Action Buttons Container
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(8, 0, 8, 0)
            action_layout.setSpacing(8)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            pid_val = rec["pid"]
            proc_name = rec["name"]
            cmdline = rec["cmdline"]
            cwd = rec["cwd"]

            is_critical = IS_WINDOWS and (
                proc_lower in WINDOWS_CORE_SYSTEM or pid_val <= 4
            )

            if is_critical:
                lbl_prot = QLabel("Protected")
                lbl_prot.setStyleSheet(
                    "color: #565f89; font-weight: bold; font-size: 11px;"
                )
                lbl_prot.setAlignment(Qt.AlignmentFlag.AlignCenter)
                action_layout.addWidget(lbl_prot)
            elif pid_val > 0:
                # 1. Restart Button
                btn_restart = QPushButton("Restart")
                btn_restart.setFixedHeight(26)
                btn_restart.setFixedWidth(78)
                can_restart = bool(cmdline)

                if can_restart:
                    btn_restart.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_restart.setStyleSheet("""
                        QPushButton {
                            background-color: #24283b;
                            color: #7aa2f7;
                            border: 1px solid #3b4261;
                            border-radius: 4px;
                            font-size: 11px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #3b4261;
                            border-color: #7aa2f7;
                            color: #c0caf5;
                        }
                    """)
                    btn_restart.clicked.connect(
                        lambda checked, p=pid_val, pt=port, n=proc_name, c=cmdline, d=cwd: (
                            self.restart_port(p, pt, n, c, d)
                        )
                    )
                else:
                    btn_restart.setEnabled(False)
                    btn_restart.setStyleSheet("""
                        QPushButton {
                            background-color: #1a1b26;
                            color: #414868;
                            border: 1px solid #24283b;
                            border-radius: 4px;
                            font-size: 11px;
                        }
                    """)
                action_layout.addWidget(btn_restart)

                # 2. Kill Button
                btn_kill = QPushButton("Kill")
                btn_kill.setFixedHeight(26)
                btn_kill.setFixedWidth(64)
                btn_kill.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_kill.setStyleSheet("""
                    QPushButton {
                        background-color: #3b243b;
                        color: #f7768e;
                        border: 1px solid #7a324b;
                        border-radius: 4px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #f7768e;
                        color: #1a1b26;
                        border-color: #f7768e;
                    }
                """)
                btn_kill.clicked.connect(
                    lambda checked, p=pid_val, pt=port, n=proc_name: self.kill_port(
                        p, pt, n
                    )
                )
                action_layout.addWidget(btn_kill)

            else:
                btn_sudo = QPushButton("Need Sudo")
                btn_sudo.setFixedHeight(26)
                btn_sudo.setStyleSheet("""
                    QPushButton {
                        background-color: #1f2335;
                        color: #7982a9;
                        border: 1px solid #292e42;
                        border-radius: 4px;
                        font-size: 11px;
                    }
                """)
                btn_sudo.clicked.connect(
                    lambda checked, pt=port: self.show_sudo_notice(pt)
                )
                action_layout.addWidget(btn_sudo)

            self.table.setCellWidget(row, 6, action_widget)

    def on_cell_double_clicked(self, row: int, column: int):
        if column != 1:
            return

        port_item = self.table.item(row, 0)
        if not port_item:
            return

        port = int(port_item.text())
        current_tag = self.port_tags.get(port, "")

        new_tag, ok = QInputDialog.getText(
            self,
            "Edit Service Tag",
            f"Enter custom label/tag for port {port}:",
            text=current_tag,
        )

        if ok:
            cleaned = new_tag.strip()
            if cleaned:
                self.port_tags[port] = cleaned
            else:
                self.port_tags.pop(port, None)

            save_tags(self.port_tags)
            self.render_table()

    def show_sudo_notice(self, port: int):
        QMessageBox.information(
            self,
            "Privilege Required",
            f"Port {port} is bound by a system daemon.\nRun terminal as Administrator/root to manage it.",
        )

    def kill_port(self, pid: int, port: int, name: str):
        reply = QMessageBox.question(
            self,
            "Confirm Kill Process",
            f"Are you sure you want to terminate:\n\n"
            f"• Process: {name}\n"
            f"• PID: {pid}\n"
            f"• Bound Port: {port}\n\n"
            f"This will send SIGTERM with SIGKILL / taskkill fallback.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = terminate_process_cross_platform(pid)
            if success:
                self.status_bar.showMessage(
                    f"Successfully killed PID {pid} (Port {port})", 4000
                )
                QTimer.singleShot(300, self.trigger_scan)
            else:
                QMessageBox.critical(
                    self,
                    "Termination Error",
                    f"Failed to terminate process {name} (PID: {pid}).\nRun terminal as Administrator.",
                )

    def restart_port(
        self, pid: int, port: int, name: str, cmdline: List[str], cwd: Optional[str]
    ):
        cmd_preview = " ".join(cmdline[:6]) + ("..." if len(cmdline) > 6 else "")
        reply = QMessageBox.question(
            self,
            "Confirm Restart Process",
            f"Are you sure you want to restart:\n\n"
            f"• Process: {name}\n"
            f"• PID: {pid}\n"
            f"• Bound Port: {port}\n"
            f"• Command: {cmd_preview}\n\n"
            f"The current process will be killed and re-launched in a detached session.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = restart_process_cross_platform(pid, cmdline, cwd)
            if success:
                self.status_bar.showMessage(f"Restarted {name} on port {port}", 4000)
                QTimer.singleShot(1000, self.trigger_scan)
            else:
                QMessageBox.critical(
                    self,
                    "Restart Error",
                    f"Failed to restart {name} (PID: {pid}).\nCould not spawn replacement process.",
                )


def main():
    # Fix for Windows Taskbar icon showing generic python executable
    if IS_WINDOWS:
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "devport.inspector.zombiekiller.v1"
            )
        except Exception:
            pass

    app = QApplication(sys.argv)

    # Set icon at the application level
    app_icon = get_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    window = DevPortInspector()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
