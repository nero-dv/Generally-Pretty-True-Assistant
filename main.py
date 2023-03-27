import os
import sys

import openai
import tiktoken
from numpy import hsplit
from PySide6.QtCore import Qt, QEvent, QObject
from PySide6.QtGui import QAction, QFont, QFontDatabase, QShortcut, QKeyEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)




class ChatInput(QTextEdit):
    def __init__(self, submit_text, parent=None):
        super().__init__(parent)
        self.submit_text = submit_text

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier: # type: ignore
            self.submit_text()
        else:
            super().keyPressEvent(event)

class AuthenticationError(openai.error.AuthenticationError()):
    def __init__(self, parent=None):
        super().__init__(parent)
        print("Invalid API key. Please set one in the menu.")
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setText("Invalid API key. Please set one in the menu.")
        error_box.setWindowTitle("Invalid API key")
        error_box.setStandardButtons(QMessageBox.Ok)
        error_box.exec()
        return


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.first_message = True
        self.init_ui()
        self.setWindowIcon(QIcon('img/icon.ico'))

    def init_ui(self):
        fontdb = QFontDatabase()
        id1 = fontdb.addApplicationFont("./fonts/Raleway-Regular.ttf")
        id2 = fontdb.addApplicationFont("./fonts/ShareTechMono-Regular.ttf")
        id3 = fontdb.addApplicationFont("./fonts/Figtree-Regular.ttf")
        chat_font = QFont(fontdb.applicationFontFamilies(id1))
        console_font = QFont(fontdb.applicationFontFamilies(id2))
        info_font = QFont(fontdb.applicationFontFamilies(id3))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        self.create_menu()

        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems(["gpt-3.5-turbo"])
        self.model_dropdown.setEnabled(False)
        self.current_model = self.model_dropdown.currentText()
        main_layout.addWidget(self.model_dropdown)

        splitter = QSplitter(Qt.Vertical)  # type: ignore

        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        response_font = chat_font
        response_font.setPointSize(11)
        self.chat.setFont(response_font)
        self.chat.setPlaceholderText("Your assistant's response will appear here")
        splitter.addWidget(self.chat)

        self.input_text_edit = ChatInput(self.submit_text)
        input_text_font = chat_font
        input_text_font.setPointSize(11)
        self.input_text_edit.setFont(input_text_font)
        self.input_text_edit.setPlaceholderText("Enter your text here")
        self.input_text_edit.setFocus()
        self.input_text_edit.textChanged.connect(self.parse_text)  # type: ignore
        self.input_text_edit.setAcceptRichText(False)

        splitter.addWidget(self.input_text_edit)

        self.parsed_info_label = QLabel(
            f"Token count: 0\tWord count: 0,\tCharacter count: 0\n(Token Counts are estimated with Tiktoken and don't include special tokens or tokens added by the model and its response)"
        )
        self.parsed_info_label.setWordWrap(True)
        pil_font = info_font
        pil_font.setPointSize(9)
        self.parsed_info_label.setFont(pil_font)
        splitter.addWidget(self.parsed_info_label)

        tab_widget = QTabWidget()
        first_tab_widget = QWidget()
        first_tab_layout = QVBoxLayout()
        first_tab_layout.addWidget(splitter)
        splitter.setSizes([300, 100, 20])

        bottom_layout = QHBoxLayout()
        submit_button = QPushButton("Submit")
        plus_button = QPushButton("+")
        minus_button = QPushButton("-")
        
        bottom_layout.addWidget(submit_button)
        bottom_layout.addWidget(plus_button)
        bottom_layout.addWidget(minus_button)
        

        submit_button.clicked.connect(self.submit_text)  # type: ignore
        submit_button.setAutoDefault(True)
        submit_button.setShortcut("Ctrl+Enter")
        submit_button.keyPressEvent = self.submit_text  # type: ignore
        
        plus_button.clicked.connect(self.increase_font_size)
        minus_button.clicked.connect(self.decrease_font_size)

        first_tab_layout.addLayout(bottom_layout)
        first_tab_widget.setLayout(first_tab_layout)
        tab_widget.addTab(first_tab_widget, self.model_dropdown.currentText())

        self.history = QTextEdit()
        history_font = console_font
        self.history.setFont(history_font)
        history_font.setPointSize(11)
        self.history.setReadOnly(True)
        self.history.setPlaceholderText(
            "Your assistant's raw responses will appear here"
        )

        second_tab_widget = QWidget()
        second_tab_layout = QVBoxLayout()
        second_tab_layout.addWidget(self.history)
        second_tab_widget.setLayout(second_tab_layout)
        tab_widget.addTab(second_tab_widget, "Raw History")

        main_layout.addWidget(tab_widget)
        central_widget.setLayout(main_layout)
    

    def increase_font_size(self):
        # Get the current font size and increase it by 1
        current_size = self.chat.fontPointSize()
        new_size = current_size + 1
        # Set the new font size for the QTextEdit widget
        font = self.chat.currentFont()
        font.setPointSize(new_size)
        self.chat.setCurrentFont(font)
        
    def decrease_font_size(self):
        # Get the current font size and decrease it by 1
        current_size = self.chat.fontPointSize()
        new_size = current_size - 1
        # Set the new font size for the QTextEdit widget
        font = self.chat.currentFont()
        font.setPointSize(new_size)
        self.chat.setCurrentFont(font)

    def create_menu(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        # Menu one
        file_menu = QMenu("&File", self)
        menu_bar.addMenu(file_menu)

        def add_menu_action(parent, name, shortcut, func):
            action = QAction(name, self)
            action.setShortcut(shortcut)
            action.triggered.connect(func)  # type: ignore
            parent.addAction(action)

        # Menu one items
        self.save_chat_action = add_menu_action(
            file_menu, "&Save Chat", "Ctrl+S", self.save_chat
        )
        self.export_history_action = add_menu_action(
            file_menu, "&Export History", "Ctrl+E", self.export_history
        )
        self.set_api_action = add_menu_action(
            file_menu, "&Set API Key", "Ctrl+K", self.set_api_key
        )
        # self.api_key_option = add_menu_action(
        #     file_menu, "&API Key Manager", "Ctrl+M", self.api_key_manager
        # )
        self.quit_action = add_menu_action(file_menu, "&Quit", "Ctrl+Q", self.close)

        # Menu two
        edit_menu = QMenu("&Edit", self)
        menu_bar.addMenu(edit_menu)

        # Menu two items
        self.copy_action = add_menu_action(edit_menu, "&Copy", "Ctrl+C", self.copy_text)
        self.paste_action = add_menu_action(
            edit_menu, "&Paste", "Ctrl+V", self.paste_text
        )
        self.cut_action = add_menu_action(edit_menu, "&Cut", "Ctrl+X", self.cut_text)
        self.select_all_action = add_menu_action(
            edit_menu, "&Select All", "Ctrl+A", self.select_all_text
        )
        self.clear_chat_action = add_menu_action(
            edit_menu, "&Clear Chat", "Ctrl+W", self.clear_chat
        )

    def save_chat(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Chat", "", "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            with open(file_path, "w") as file:
                file.write(self.chat.toPlainText())

    def export_history(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Raw History", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            with open(file_path, "w") as file:
                file.write(self.history.toPlainText())

    def set_api_key(self):
        # Use a dialog to get the API key
        api_key, ok = QInputDialog.getText(
            self, "QInputDialog.getText()", "API Key:", QLineEdit.Normal  # type: ignore
        )
        if ok and api_key:
            self.save_api_key(api_key)

    def save_api_key(self, api_key):
        with open("api_key.txt", "w") as file:
            file.write(api_key)
        return api_key

    def read_api_key(self):
        try:
            with open("api_key.txt", "r") as file:
                return file.read()
        except FileNotFoundError:
            # Use a dialog to get the API key
            self.set_api_key()

    def api_key_manager(self):
        # TODO: Add a dialog to manage API keys along with a way to select which one to use and a way to delete them. API key utilization should be tracked and shown in the manager.
        pass

    def copy_text(self):
        self.input_text_edit.copy()

    def paste_text(self):
        self.input_text_edit.paste()

    def cut_text(self):
        self.input_text_edit.cut()

    def select_all_text(self):
        self.input_text_edit.selectAll()

    def clear_chat(self):
        self.chat.clear()

    def parse_text(self):
        input_text = self.input_text_edit.toPlainText()
        # if input_text.endswith("\n"):
        #     self.submit_text()
        parsed_info = self.parse_information(input_text)
        self.parsed_info_label.setText(parsed_info)
    
    def AuthenticationError(self):
        print("Invalid API key. Please set one in the menu.")
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setText("Invalid API key. Please set one in the menu.")
        error_box.setWindowTitle("Invalid API key")
        error_box.setStandardButtons(QMessageBox.Ok)
        error_box.exec()
        return

    @staticmethod
    def parse_information(text, model="cl100k_base"):
        encoding = tiktoken.get_encoding(model)
        assert encoding.decode(encoding.encode(text)) == text
        num_tokens = len(encoding.encode(text))
        return f"Token count: {num_tokens}\tWord count: {len(text.split())},\tCharacter count: {len(text)}"

    def submit_text(self):
        try:
            if os.environ.get("OPENAI_API_KEY"):
                OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
            else:
                OPENAI_API_KEY = self.read_api_key()
        except:
            print("No API key found. Please set one in the menu.")

        openai.api_key = OPENAI_API_KEY
        input_text = self.input_text_edit.toPlainText()
        if self.first_message == False:
            response = openai.ChatCompletion.create(
                model=self.model_dropdown.currentText(),
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI language model that is helpful and friendly. You are continuing a conversation.",
                    },
                    {"role": "user", "content": self.input_text_two},
                    {"role": "assistant", "content": self.first_response},
                    {"role": "user", "content": input_text},
                ],
                temperature=0.6,
            )
        else:
            try:
                response = openai.ChatCompletion.create(
                    # model="chatgpt-3.5-turbo",
                    model=self.model_dropdown.currentText(),
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an AI language model that is helpful and friendly.",
                        },
                        {"role": "user", "content": input_text},
                    ],
                    temperature=0.6,
                )
            except openai.error.AuthenticationError:
                self.AuthenticationError()
            except Exception() as e:
                print(e)

        # Get the parsed information from the API response
        parsed_info = response.choices[0].message.content

        # Get usage information from the API response
        completion_tokens = response.usage.completion_tokens
        prompt_tokens = response.usage.prompt_tokens
        total_tokens = response.usage.total_tokens
        token_usage = f"Completion tokens: {completion_tokens}\tPrompt tokens: {prompt_tokens}\nTotal tokens: {total_tokens}"

        print(parsed_info)
        print(response)
        self.input_text_two = input_text
        self.first_response = parsed_info

        # Append the chat text to the chat text edit
        self.chat.append(
            f"User: {input_text}\n\n\t{'-' * 60}\n\nAI: {parsed_info}\n\n\n{token_usage}\tFirst Message: {self.first_message}\n\n\t{'-' * 60}\n\n\n"
        )
        # self.chat.toMarkdown()
        # Clear the input text edit
        self.input_text_edit.clear()

        # Log the response
        self.history.append(f"{response},")
        self.first_message = False


if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.setWindowTitle("OpenAI API - GPT3.5-Turbo")
    main_window.setGeometry(400, 100, 600, 1200)

    main_window.show()

    sys.exit(app.exec())
