import os
import sys
from PyQt6 import QtCore, QtGui, QtWidgets


def generate_devport_icon():
    app = (
        QtWidgets.QApplication.instance()
        or QtWidgets.QApplication(sys.argv)
    )

    os.makedirs("assets", exist_ok=True)
    size = 512
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)

    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

    # 1. Outer Squircle Badge (#16161e -> #1a1b26)
    bg_path = QtGui.QPainterPath()
    bg_path.addRoundedRect(24.0, 24.0, float(size - 48), float(size - 48), 110.0, 110.0)

    bg_grad = QtGui.QLinearGradient(0, 0, size, size)
    bg_grad.setColorAt(0.0, QtGui.QColor("#1f2335"))
    bg_grad.setColorAt(0.5, QtGui.QColor("#16161e"))
    bg_grad.setColorAt(1.0, QtGui.QColor("#0f0f14"))
    painter.fillPath(bg_path, bg_grad)

    # Subtle metallic border
    border_pen = QtGui.QPen(QtGui.QColor("#414868"), 6.0)
    painter.setPen(border_pen)
    painter.drawPath(bg_path)

    # 2. Port Inspector Ring (Radar / Port Hub)
    center_x, center_y = size / 2.0, size / 2.0

    radar_pen = QtGui.QPen(QtGui.QColor("#24283b"), 4.0, QtCore.Qt.PenStyle.DashLine)
    painter.setPen(radar_pen)
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    painter.drawEllipse(QtCore.QPointF(center_x, center_y), 170.0, 170.0)

    # Outer network node satellites (representing ports like 8000, 5432, 11434)
    nodes = [
        (center_x, center_y - 170),  # Top
        (center_x + 170, center_y),  # Right
        (center_x, center_y + 170),  # Bottom
        (center_x - 170, center_y),  # Left
    ]

    for i, (nx, ny) in enumerate(nodes):
        # Glow ring
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        node_color = QtGui.QColor("#7aa2f7" if i % 2 == 0 else "#bb9af7")
        painter.setBrush(QtGui.QColor(node_color.red(), node_color.green(), node_color.blue(), 50))
        painter.drawEllipse(QtCore.QPointF(nx, ny), 18.0, 18.0)

        # Core dot
        painter.setBrush(node_color)
        painter.drawEllipse(QtCore.QPointF(nx, ny), 8.0, 8.0)

    # 3. Inner Port Socket Chamber (Dark Recessed Circle)
    socket_path = QtGui.QPainterPath()
    socket_path.addEllipse(QtCore.QPointF(center_x, center_y), 115.0, 115.0)

    socket_grad = QtGui.QRadialGradient(center_x, center_y, 115.0)
    socket_grad.setColorAt(0.0, QtGui.QColor("#13141c"))
    socket_grad.setColorAt(0.85, QtGui.QColor("#1a1b26"))
    socket_grad.setColorAt(1.0, QtGui.QColor("#292e42"))
    painter.fillPath(socket_path, socket_grad)

    socket_border = QtGui.QPen(QtGui.QColor("#7aa2f7"), 4.0)
    painter.setPen(socket_border)
    painter.drawPath(socket_path)

    # 4. Killer Lightning Bolt & Crosshair Laser (#f7768e Coral Red to #ff9eaf)
    bolt_path = QtGui.QPainterPath()
    # Sharp, energetic dev bolt cutting across the port socket
    bolt_points = [
        QtCore.QPointF(270, 160),  # Top tip
        QtCore.QPointF(200, 260),  # Mid bend left
        QtCore.QPointF(248, 260),  # Horizontal step
        QtCore.QPointF(232, 352),  # Bottom sharp tip
        QtCore.QPointF(312, 242),  # Mid bend right
        QtCore.QPointF(264, 242),  # Horizontal step inward
    ]
    bolt_path.moveTo(bolt_points[0])
    for pt in bolt_points[1:]:
        bolt_path.lineTo(pt)
    bolt_path.closeSubpath()

    # Lightning Bolt Gradient
    bolt_grad = QtGui.QLinearGradient(200, 160, 312, 352)
    bolt_grad.setColorAt(0.0, QtGui.QColor("#ff9eaf"))
    bolt_grad.setColorAt(0.5, QtGui.QColor("#f7768e"))  # Signature action red
    bolt_grad.setColorAt(1.0, QtGui.QColor("#e0af68"))  # Amber spark

    painter.fillPath(bolt_path, bolt_grad)

    bolt_pen = QtGui.QPen(QtGui.QColor("#ffffff"), 3.0)
    painter.setPen(bolt_pen)
    painter.drawPath(bolt_path)

    # 5. Crosshair Target Reticle over the core
    reticle_pen = QtGui.QPen(QtGui.QColor("#f7768e"), 3.5, QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap)
    painter.setPen(reticle_pen)
    # Top reticle notch
    painter.drawLine(int(center_x), 105, int(center_x), 125)
    # Bottom reticle notch
    painter.drawLine(int(center_x), 387, int(center_x), 407)
    # Left reticle notch
    painter.drawLine(105, int(center_y), 125, int(center_y))
    # Right reticle notch
    painter.drawLine(387, int(center_y), 407, int(center_y))

    painter.end()

    # Output Paths
    png_path = os.path.join("assets", "icon.png")
    ico_path = os.path.join("assets", "icon.ico")

    # 1. Save PNG (Master 512x512)
    pixmap.save(png_path, "PNG")
    print(f"✅ Generated Master PNG: {png_path}")

    # 2. Save Multi-resolution ICO (16, 24, 32, 48, 64, 128, 256)
    icon = QtGui.QIcon()
    for s in [16, 24, 32, 48, 64, 128, 256]:
        scaled = pixmap.scaled(
            s,
            s,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        icon.addPixmap(scaled)

    # Write multi-layer icon to disk
    pixmap_256 = pixmap.scaled(256, 256, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
    pixmap_256.save(ico_path, "ICO")
    print(f"✅ Generated Windows ICO: {ico_path}")


if __name__ == "__main__":
    generate_devport_icon()