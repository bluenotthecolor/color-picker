import sys
import ctypes
from dataclasses import dataclass

from mss import mss

from PySide6.QtCore import Qt, QRect, QPoint, Signal, QTimer
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QPixmap,
    QPainter,
    QPen,
    QAction,
    QIcon,
    QImage,
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QSystemTrayIcon,
    QMenu,
    QFrame,
)


@dataclass
class ScreenCapture:
    geometry: QRect
    pixmap: QPixmap


def capture_all_screens():
    """
    Capture every connected monitor using MSS.

    MSS gives us the actual screen pixels and avoids the
    black/incorrect screenshot issue that can happen with
    QScreen.grabWindow() on Windows.
    """

    captures = []

    with mss() as sct:


        for monitor in sct.monitors[1:]:

            left = monitor["left"]
            top = monitor["top"]
            width = monitor["width"]
            height = monitor["height"]

            screenshot = sct.grab(monitor)


            image = QImage(
                screenshot.rgb,
                screenshot.width,
                screenshot.height,
                screenshot.width * 3,
                QImage.Format.Format_RGB888,
            ).copy()

            pixmap = QPixmap.fromImage(
                image
            )

            captures.append(
                ScreenCapture(
                    geometry=QRect(
                        left,
                        top,
                        width,
                        height,
                    ),
                    pixmap=pixmap,
                )
            )

    return captures


def sample_at_global_position(captures, position):
    """
    Find the monitor underneath the cursor and return the
    underlying screenshot image, the exact pixel coordinates
    within it, and the color at that pixel.

    Handles different Windows display scaling values
    on different monitors. Returns None if the position
    isn't over any captured monitor.
    """

    for capture in captures:

        geometry = capture.geometry

        if not geometry.contains(position):
            continue


        local_x = position.x() - geometry.x()
        local_y = position.y() - geometry.y()

        image = capture.pixmap.toImage()

        if (
            geometry.width() <= 0
            or geometry.height() <= 0
        ):
            continue


        scale_x = (
            image.width()
            / geometry.width()
        )

        scale_y = (
            image.height()
            / geometry.height()
        )

        pixel_x = int(
            local_x * scale_x
        )

        pixel_y = int(
            local_y * scale_y
        )

        if (
            0 <= pixel_x < image.width()
            and 0 <= pixel_y < image.height()
        ):
            return (
                image,
                pixel_x,
                pixel_y,
                image.pixelColor(
                    pixel_x,
                    pixel_y,
                ),
            )

    return None


def color_at_global_position(captures, position):
    """
    Convenience wrapper around sample_at_global_position
    that just returns the color.
    """

    sample = sample_at_global_position(
        captures,
        position,
    )

    return sample[3] if sample else None


MAGNIFIER_SIZE = 140
MAGNIFIER_PIXELS = 11
MAGNIFIER_OFFSET = 26


class ScreenPicker(QWidget):

    colorPicked = Signal(QColor)
    cancelled = Signal()

    def __init__(self, captures):

        super().__init__()

        self.captures = captures

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True,
        )


        self.setCursor(
            Qt.CursorShape.BlankCursor
        )

        virtual_geometry = (
            self.virtual_desktop_geometry()
        )

        self.setGeometry(
            virtual_geometry
        )

        self.setMouseTracking(
            True
        )

        self.current_color = QColor(
            "#FFFFFF"
        )


        self.current_sample = None


        self.current_local_pos = QPoint(0, 0)


        self.has_moved = False

    def virtual_desktop_geometry(self):

        screens = QGuiApplication.screens()

        if not screens:
            return QRect(
                0,
                0,
                1,
                1,
            )

        geometry = screens[0].geometry()

        for screen in screens[1:]:

            geometry = geometry.united(
                screen.geometry()
            )

        return geometry

    def paintEvent(self, event):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )


        painter.fillRect(
            self.rect(),
            QColor(
                0,
                0,
                0,
                1,
            ),
        )

        if self.has_moved:

            self.draw_crosshair(
                painter
            )

        if self.current_sample:

            self.draw_magnifier(
                painter
            )

        painter.end()

    def draw_crosshair(self, painter):


        x = self.current_local_pos.x()
        y = self.current_local_pos.y()

        arm = 9
        gap = 3

        def draw_arms(pen):

            painter.setPen(pen)

            painter.drawLine(x - arm, y, x - gap, y)
            painter.drawLine(x + gap, y, x + arm, y)
            painter.drawLine(x, y - arm, x, y - gap)
            painter.drawLine(x, y + gap, x, y + arm)
        draw_arms(
            QPen(
                Qt.GlobalColor.black,
                3,
            )
        )
        draw_arms(
            QPen(
                Qt.GlobalColor.white,
                1,
            )
        )

    def draw_magnifier(self, painter):

        image, pixel_x, pixel_y, color = (
            self.current_sample
        )

        half = MAGNIFIER_PIXELS // 2

        src_rect = QRect(
            pixel_x - half,
            pixel_y - half,
            MAGNIFIER_PIXELS,
            MAGNIFIER_PIXELS,
        ).intersected(
            QRect(
                0,
                0,
                image.width(),
                image.height(),
            )
        )

        if src_rect.isEmpty():
            return

        cropped = image.copy(
            src_rect
        )


        zoomed = cropped.scaled(
            MAGNIFIER_SIZE,
            MAGNIFIER_SIZE,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )

        box_x = self.current_local_pos.x() + MAGNIFIER_OFFSET
        box_y = self.current_local_pos.y() + MAGNIFIER_OFFSET

        if box_x + MAGNIFIER_SIZE > self.width():
            box_x = (
                self.current_local_pos.x()
                - MAGNIFIER_OFFSET
                - MAGNIFIER_SIZE
            )

        if box_y + MAGNIFIER_SIZE > self.height():
            box_y = (
                self.current_local_pos.y()
                - MAGNIFIER_OFFSET
                - MAGNIFIER_SIZE
            )

        painter.drawImage(
            box_x,
            box_y,
            zoomed,
        )

        painter.setPen(
            QPen(
                Qt.GlobalColor.white,
                2,
            )
        )
        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )
        painter.drawRect(
            box_x,
            box_y,
            MAGNIFIER_SIZE,
            MAGNIFIER_SIZE,
        )


        cell = MAGNIFIER_SIZE / MAGNIFIER_PIXELS

        painter.setPen(
            QPen(
                Qt.GlobalColor.red,
                2,
            )
        )
        painter.drawRect(
            int(box_x + cell * half),
            int(box_y + cell * half),
            int(cell),
            int(cell),
        )


        label_rect = QRect(
            box_x,
            box_y + MAGNIFIER_SIZE + 6,
            MAGNIFIER_SIZE,
            26,
        )

        painter.fillRect(
            label_rect,
            QColor(
                0,
                0,
                0,
                190,
            ),
        )

        painter.setPen(
            Qt.GlobalColor.white
        )
        painter.drawText(
            label_rect,
            Qt.AlignmentFlag.AlignCenter,
            color.name().upper(),
        )

    def mouseMoveEvent(self, event):

        local_pos = (
            event.position().toPoint()
        )

        global_position = (
            self.mapToGlobal(
                local_pos
            )
        )

        sample = (
            sample_at_global_position(
                self.captures,
                global_position,
            )
        )

        self.current_local_pos = local_pos
        self.current_sample = sample
        self.has_moved = True

        if sample:

            self.current_color = sample[3]

        self.update()

    def mousePressEvent(self, event):

        if (
            event.button()
            != Qt.MouseButton.LeftButton
        ):
            return

        global_position = (
            self.mapToGlobal(
                event.position().toPoint()
            )
        )

        sample = (
            sample_at_global_position(
                self.captures,
                global_position,
            )
        )

        if sample:

            self.colorPicked.emit(
                sample[3]
            )

        self.close()

    def keyPressEvent(self, event):

        if (
            event.key()
            == Qt.Key.Key_Escape
        ):

            self.cancelled.emit()

            self.close()

            return

        super().keyPressEvent(
            event
        )

class DraggableFrame(QFrame):
    """
    A QFrame that drags its top-level window around when clicked
    and dragged. Used as the main window's background container
    since the window itself is frameless and has no title bar.

    Child widgets (buttons, etc.) still get their own clicks first;
    this only takes over when a press lands on empty frame space.
    """

    def __init__(self, parent=None):

        super().__init__(parent)

        self._drag_offset = None

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            self._drag_offset = (
                event.globalPosition().toPoint()
                - self.window().frameGeometry().topLeft()
            )

            event.accept()

        else:

            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):

        if (
            self._drag_offset is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):

            self.window().move(
                event.globalPosition().toPoint()
                - self._drag_offset
            )

            event.accept()

        else:

            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):

        self._drag_offset = None

        super().mouseReleaseEvent(event)


class ColorPicker(QWidget):

    def __init__(self):

        super().__init__()

        self.color = QColor(
            "#E8A7D1"
        )

        self.picker = None

        self.setWindowTitle(
            "Color Picker"
        )

        self.setFixedSize(
            340,
            330,
        )

        self.setWindowIcon(
            QIcon("icon.ico")
        )


        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.build_ui()

        self.tray = (
            self.create_tray()
        )

        self.update_display()

    def build_ui(self):

        container = DraggableFrame(
            self
        )

        container.setGeometry(
            0,
            0,
            340,
            330,
        )

        container.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1px solid #dddddd;
                border-radius: 16px;
            }
        """)

        self.close_button = QPushButton(
            "×",
            container,
        )


        self.close_button.setGeometry(
            302,
            -5,
            30,
            30,
        )

        self.close_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.close_button.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )

        self.close_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #999999;
                border: none;
                border-radius: 8px;
                font-size: 22px;
                font-weight: 400;
                padding: 0px;
                margin: 0px;
            }

            QPushButton:hover {
                background: #f0f0f0;
                color: #222222;
            }

            QPushButton:pressed {
                background: #e4e4e4;
                color: #111111;
            }
        """)

        self.close_button.clicked.connect(
            self.hide_to_tray
        )

        layout = QVBoxLayout(
            container
        )

        layout.setContentsMargins(
            20,
            18,
            20,
            20,
        )

        layout.setSpacing(
            10
        )

        title = QLabel(
            "Color Picker"
        )

        title.setStyleSheet("""
            QLabel {
                color: #222222;
                font-size: 19px;
                font-weight: 700;
            }
        """)

        subtitle = QLabel(
            "Pick any pixel from your screen"
        )

        subtitle.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
            }
        """)

        self.preview = QLabel()

        self.preview.setFixedHeight(
            105
        )

        self.preview.setStyleSheet("""
            QLabel {
                border-radius: 11px;
                border: 1px solid #dddddd;
            }
        """)

        self.hex_label = QLabel()

        self.hex_label.setStyleSheet("""
            QLabel {
                color: #222222;
                font-size: 23px;
                font-weight: 700;
            }
        """)


        self.rgb_label = QLabel()
        self.hsl_label = QLabel()

        for label in (
            self.rgb_label,
            self.hsl_label,
        ):

            label.setStyleSheet("""
                QLabel {
                    color: #666666;
                    font-size: 13px;
                }
            """)


        self.pick_button = QPushButton(
            "Pick color"
        )

        self.copy_button = QPushButton(
            "Copy HEX"
        )

        self.pick_button.clicked.connect(
            self.start_pick
        )

        self.copy_button.clicked.connect(
            self.copy_hex
        )

        self.pick_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.copy_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.pick_button.setStyleSheet("""
            QPushButton {
                background: #eeeeee;
                color: #222222;
                border: none;
                border-radius: 9px;
                padding: 10px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #dddddd;
            }

            QPushButton:pressed {
                background: #cccccc;
            }
        """)

        self.copy_button.setStyleSheet("""
            QPushButton {
                background: #222222;
                color: #ffffff;
                border: none;
                border-radius: 9px;
                padding: 10px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #444444;
            }

            QPushButton:pressed {
                background: #111111;
            }
        """)

        buttons = QHBoxLayout()

        buttons.setSpacing(
            8
        )

        buttons.addWidget(
            self.pick_button
        )

        buttons.addWidget(
            self.copy_button
        )


        layout.addWidget(
            title
        )

        layout.addWidget(
            subtitle
        )

        layout.addWidget(
            self.preview
        )

        layout.addWidget(
            self.hex_label
        )

        layout.addWidget(
            self.rgb_label
        )

        layout.addWidget(
            self.hsl_label
        )

        layout.addStretch()

        layout.addLayout(
            buttons
        )

    def update_display(self):

        self.preview.setStyleSheet(
            f"""
            QLabel {{
                background: {self.color.name()};
                border-radius: 11px;
                border: 1px solid #dddddd;
            }}
            """
        )

        self.hex_label.setText(
            self.color.name().upper()
        )

        self.rgb_label.setText(
            f"RGB  "
            f"{self.color.red()}, "
            f"{self.color.green()}, "
            f"{self.color.blue()}"
        )

        h, s, l, _ = (
            self.color.getHsl()
        )

        if h < 0:
            h = 0

        self.hsl_label.setText(
            f"HSL  "
            f"{h}°, "
            f"{round(s / 255 * 100)}%, "
            f"{round(l / 255 * 100)}%"
        )

        if hasattr(
            self,
            "tray",
        ):

            self.tray.setIcon(
                self.create_icon()
            )

    def start_pick(self):


        self.hide()

        QApplication.processEvents()

        captures = (
            capture_all_screens()
        )

        if not captures:

            self.show_window()

            return

        self.picker = ScreenPicker(
            captures
        )

        self.picker.colorPicked.connect(
            self.on_color_picked
        )

        self.picker.cancelled.connect(
            self.on_picker_cancelled
        )

        self.picker.show()

        self.picker.activateWindow()
        self.picker.raise_()

    def on_color_picked(
        self,
        color,
    ):

        self.color = QColor(
            color
        )

        self.update_display()

        self.show_window()

        self.copy_hex()

    def on_picker_cancelled(
        self,
    ):

        self.show_window()

    def copy_hex(self):

        value = (
            self.color.name()
            .upper()
            .lstrip("#")
        )

        QGuiApplication.clipboard().setText(
            value
        )

        self.copy_button.setText(
            "Copied!"
        )

        QTimer.singleShot(
            1000,
            lambda: self.copy_button.setText(
                "Copy HEX"
            ),
        )

    def create_tray(self):

        tray = QSystemTrayIcon(
            self
        )

        tray.setIcon(
            self.create_icon()
        )

        tray.setToolTip(
            "Color Picker"
        )

        tray.activated.connect(
            self.tray_activated
        )

        menu = QMenu()

        show_action = QAction(
            "Show",
            self,
        )

        pick_action = QAction(
            "Pick color",
            self,
        )

        exit_action = QAction(
            "Exit",
            self,
        )

        show_action.triggered.connect(
            self.show_window
        )

        pick_action.triggered.connect(
            self.start_pick
        )

        exit_action.triggered.connect(
            QApplication.quit
        )

        menu.addAction(
            show_action
        )

        menu.addAction(
            pick_action
        )

        menu.addSeparator()

        menu.addAction(
            exit_action
        )

        tray.setContextMenu(
            menu
        )

        tray.show()

        return tray

    def tray_activated(
        self,
        reason,
    ):

        if (
            reason
            == QSystemTrayIcon.ActivationReason.DoubleClick
        ):

            self.show_window()

    def create_icon(self):

        pixmap = QPixmap(
            32,
            32,
        )

        pixmap.fill(
            self.color
        )

        painter = QPainter(
            pixmap
        )

        painter.setPen(
            QPen(
                Qt.GlobalColor.white,
                2,
            )
        )

        painter.drawRect(
            1,
            1,
            30,
            30,
        )

        painter.end()

        return QIcon(
            pixmap
        )

    def show_window(self):

        self.show()

        self.setWindowState(
            self.windowState()
            & ~Qt.WindowState.WindowMinimized
        )

        self.activateWindow()

        self.raise_()

    def hide_to_tray(self):

        self.hide()

    def closeEvent(
        self,
        event,
    ):

        event.ignore()

        self.hide_to_tray()

def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass

    app = QApplication(
        sys.argv
    )

    app.setQuitOnLastWindowClosed(
        False
    )

    picker = ColorPicker()

    picker.show()

    sys.exit(
        app.exec()
    )

if __name__ == "__main__":
    main()