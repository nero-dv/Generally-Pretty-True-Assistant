import os
import openai
from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import QMessageBox, QTextEdit


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
                "content": "You are an AI language model that is helpful and friendly.",
            }
        ]
        for i in range(num_inputs):
            messages.append({"role": "user", "content": input_text[i]})
            if i < num_inputs - 1:
                messages.append({"role": "assistant", "content": assistant_response[i]})
        return messages

    def submit_text(self, input_text, assistant_response, model="gpt-3.5-turbo"):
        try:
            if os.environ.get("OPENAI_API_KEY"):
                OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
            else:
                OPENAI_API_KEY = self.read_api_key()
        except:
            print("No API key found. Please set one in the menu.")
        openai.api_key = OPENAI_API_KEY
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=self.message_context(input_text, assistant_response),
                temperature=0.6,
            )
            return response
        except openai.error.AuthenticationError:
            print("Invalid API key. Please set one in the menu.")
            error_box = QMessageBox()
            error_box.setIcon(QMessageBox.Critical)
            error_box.setText("Invalid API key. Please set one in the menu.")
            error_box.setWindowTitle("Invalid API key")
            error_box.setStandardButtons(QMessageBox.Ok)
            error_box.exec()
            return
