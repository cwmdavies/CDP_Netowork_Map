import sys

from PyQt6.QtCore import Qt
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton


# Subclass QMainWindow to customize your application's main window
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")
        self.setFixedWidth(250)

        page_layout = QtWidgets.QVBoxLayout()
        page_layout.setContentsMargins(20, 20, 20, 20)
        layout_1 = QtWidgets.QHBoxLayout()
        layout_2 = QtWidgets.QHBoxLayout()
        layout_3 = QtWidgets.QHBoxLayout()

        page_layout.addLayout(layout_1)
        page_layout.addLayout(layout_2)
        page_layout.addLayout(layout_3)

        username_label = QtWidgets.QLabel("Username:")
        layout_1.addWidget(username_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        username_input = QtWidgets.QLineEdit()
        self.username_var = username_input
        layout_1.addWidget(username_input)

        password_label = QtWidgets.QLabel("Password:")
        layout_2.addWidget(password_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        password_input = QtWidgets.QLineEdit()
        password_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        layout_2.addWidget(password_input)

        run_button = QtWidgets.QPushButton("Run")
        run_button.clicked.connect(QtWidgets.QApplication.instance().quit)
        layout_3.addWidget(run_button)

        widget = QtWidgets.QWidget()
        widget.setLayout(page_layout)

        self.setCentralWidget(widget)


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec()

print(window.username_var)
