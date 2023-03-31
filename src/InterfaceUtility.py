import os

import openai
from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QErrorMessage,
                               QFileDialog, QInputDialog, QLabel, QLineEdit,
                               QListWidget, QMessageBox, QSizePolicy,
                               QSplitter, QTextEdit, QVBoxLayout, QWidget)


class ChatInput(QTextEdit):
    def __init__(self, submit_text, parent=None):
        super().__init__(parent)
        self.submit_text = submit_text

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:  # type: ignore
            self.submit_text()
        else:
            super().keyPressEvent(event)


class ChatModel(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    def message_context(self, input_text: list = None, assistant_response: list = None):
        num_inputs = len(input_text)
        messages = [
            {
                "role": "system",
                "content": "You're an ML model designed to answer questions.",
            }
        ]
        for i in range(num_inputs):
            messages.append({"role": "user", "content": input_text[i]})
            if i < num_inputs - 1:
                messages.append({"role": "assistant", "content": assistant_response[i]})
        return messages

    def submit_text(
        self, OPENAI_API_KEY, input_text, assistant_response, model="gpt-3.5-turbo"
    ):
        if OPENAI_API_KEY is None:
            print("No API key. Please set one in the menu.")
            error_box = QMessageBox()
            error_box.setIcon(QMessageBox.Critical)
            error_box.setText("Invalid API key. Please set one in the menu.")
            error_box.setWindowTitle("Invalid API key")
            error_box.setStandardButtons(QMessageBox.Ok)
            error_box.exec()
            return

        openai.api_key = OPENAI_API_KEY
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=self.message_context(input_text, assistant_response),
                temperature=0.6,
            )
        except openai.error.AuthenticationError:
            print("Invalid API key. Please set one in the menu.")
            error_box = QMessageBox()
            error_box.setIcon(QMessageBox.Critical)
            error_box.setText("Invalid API key. Please set one in the menu.")
            error_box.setWindowTitle("Invalid API key")
            error_box.setStandardButtons(QMessageBox.Ok)
            error_box.exec()
            return
        except Exception as e:
            return f"Request failed: {e}"
        return response


class ApiWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Key Manager")
        self.resize(500, 300)
        self.list_widget = QListWidget()
        self.list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if os.environ.get("OPENAI_API_KEY") and os.environ.get("OPENAI_API_KEY") != "":
            if self.list_widget.findItems(
                str(os.environ.get("OPENAI_API_KEY")), Qt.MatchExactly
            ):
                pass
            self.list_widget.addItem(str(os.environ.get("OPENAI_API_KEY")))
        elif os.path.isfile("api_key.aik"):
            with open("api_key.txt", "r") as f:
                key = f.read()
            if self.list_widget.findItems(key, Qt.MatchExactly):
                pass
            self.list_widget.addItem(key)
        elif self.key:
            if self.list_widget.findItems(self.key, Qt.MatchExactly):
                pass
            self.list_widget.addItem(self.key)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.handle_accept)
        button_box.rejected.connect(self.reject)
        second_button_box = QDialogButtonBox()
        add_key = second_button_box.addButton("Add Key", QDialogButtonBox.ActionRole)
        add_key.clicked.connect(self.handle_add)
        remove_key = second_button_box.addButton(
            "Remove Key", QDialogButtonBox.ActionRole
        )
        remove_key.clicked.connect(self.remove_selected)
        browse = second_button_box.addButton("Browse", QDialogButtonBox.ActionRole)
        browse.clicked.connect(self.open)
        layout = QVBoxLayout()
        splitter = QSplitter(Qt.Vertical)
        label = QLabel("Enter your API key:")
        layout.addWidget(label)
        self.text_edit = QLineEdit()
        layout.addWidget(self.list_widget)
        layout.addWidget(self.text_edit)
        splitter.addWidget(second_button_box)
        splitter.addWidget(button_box)
        layout.addWidget(splitter)
        self.list_widget.mouseDoubleClickEvent = self.handle_accept
        self.key = None
        self.setLayout(layout)
        self.exec()

    def validate_input(self):
        if (
            self.text_edit == "" or self.text_edit.text() == ""
        ) and self.none_selected():
            return False
        return True

    def handle_double_click(self):

        self.handle_accept()

    def handle_accept(self, event=None):
        if self.validate_input():
            try:
                self.key = self.get_selected_key()
                self.key = str(self.key)
                self.done(QDialog.Accepted)
                self.result()

            except Exception as e:
                print(e)
        elif self.none_selected():
            error_dialog = QErrorMessage()
            error_dialog.showMessage("No API key selected")
            error_dialog.setWindowTitle("Error")

    def result(self):
        return self.key

    def get_selected_key(self):
        self.selected_key = self.list_widget.selectedItems()[0].text()
        return self.selected_key

    def handle_add(self):
        if len(self.text_edit.text()) > 0 and " " not in self.text_edit.text():
            self.add_to_list(str(self.text_edit.text()))
            self.text_edit.clear()

    def open(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name = QFileDialog.getOpenFileName(
            None,
            "QFileDialog.getOpenFileName()",
            ".aik",
            "AI Key Files (*.aik);;All Files(*)",
            options=options,
        )

        if file_name[0]:
            with open(file_name[0], "r") as file:
                for line in file.readlines():
                    key = line.strip()
                    if self.list_widget.findItems(key, Qt.MatchExactly):
                        error_dialog = QErrorMessage()
                        error_dialog.showMessage("Key already exists in the list.")
                        error_dialog.setWindowTitle("Error")
                        error_dialog.exec()
                    else:
                        self.add_to_list(key)

    def add_to_list(self, text):
        self.list_widget.addItem(text)

    def remove_selected(self):
        selected = self.list_widget.selectedItems()
        for item in selected:
            self.list_widget.takeItem(self.list_widget.row(item))

    def none_selected(self):
        return self.list_widget.selectedItems() == []


class SmallKeyManager(QWidget):
    def set_key(self):
        api_key, ok = QInputDialog.getText(
            self, "QInputDialog.getText()", "API Key:", QLineEdit.Normal  # type: ignore
        )
        if ok and api_key:
            OPENAI_API_KEY = api_key
            return OPENAI_API_KEY

    def save_api_key(self, key):
        with open("api_key.aik", "w") as file:
            file.write(key)
