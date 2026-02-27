import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter, QColor, QPen, QBrush, QPainterPath
from PyQt6.QtCore import Qt, QRectF

app = QApplication(sys.argv)

size = 256
image = QImage(size, size, QImage.Format.Format_ARGB32)
image.fill(Qt.GlobalColor.transparent)

painter = QPainter(image)
painter.setRenderHint(QPainter.RenderHint.Antialiasing)

# Draw Shield Base
path = QPainterPath()
path.moveTo(128, 20)
path.lineTo(220, 50)
path.lineTo(220, 130)
path.cubicTo(220, 190, 170, 230, 128, 240)
path.cubicTo(86, 230, 36, 190, 36, 130)
path.lineTo(36, 50)
path.closeSubpath()

# Fill Shield
gradient_color1 = QColor("#0EA5E9") # cyan from theme
gradient_color2 = QColor("#0284C7")
painter.setBrush(QBrush(gradient_color1))
painter.setPen(Qt.PenStyle.NoPen)
painter.drawPath(path)

# Draw inner check or lock or power
painter.setBrush(QBrush(QColor("#FFFFFF")))
inner_path = QPainterPath()
# Draw a simple check mark
inner_path.moveTo(90, 130)
inner_path.lineTo(120, 160)
inner_path.lineTo(170, 90)
inner_path.lineTo(150, 80)
inner_path.lineTo(120, 130)
inner_path.lineTo(105, 115)
inner_path.closeSubpath()

painter.drawPath(inner_path)
painter.end()

image.save("app.ico", "ICO")
print("app.ico created.")
