import sys

from PyQt6.QtCore import Qt
from PyQt6 import QtWidgets

username_input_var = ""


# Subclass QMainWindow to customize your application's main window
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")
        self.setFixedWidth(250)

        global username_input_var

        page_layout = QtWidgets.QVBoxLayout()
        page_layout.setContentsMargins(20, 20, 20, 20)
        layout_1 = QtWidgets.QHBoxLayout()
        layout_2 = QtWidgets.QHBoxLayout()
        layout_3 = QtWidgets.QHBoxLayout()

        page_layout.addLayout(layout_1)
        page_layout.addLayout(layout_2)
        page_layout.addLayout(layout_3)

        self.username_label = QtWidgets.QLabel("Username:")
        layout_1.addWidget(self.username_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.username_input = QtWidgets.QLineEdit()
        layout_1.addWidget(self.username_input)
        username_input_var = self.username_input.text()

        self.password_label = QtWidgets.QLabel("Password:")
        layout_2.addWidget(self.password_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        layout_2.addWidget(self.password_input)

        self.run_button = QtWidgets.QPushButton("Run")
        self.run_button.clicked.connect(QtWidgets.QApplication.instance().quit)
        layout_3.addWidget(self.run_button)

        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.quit_script)
        layout_3.addWidget(cancel_button)

        widget = QtWidgets.QWidget()
        widget.setLayout(page_layout)

        self.setCentralWidget(widget)

    @staticmethod
    def quit_script():
        sys.exit()


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec()

print(username_input_var)
