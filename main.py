import sys
import json

import tiktoken
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QFontDatabase, QIcon, QTextCursor
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog,
                               QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                               QMainWindow, QMenu, QMenuBar, QPushButton,
                               QSplitter, QTabWidget, QTextEdit, QVBoxLayout,
                               QWidget)

from InterfaceUtility import ChatInput, ChatModel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.input_text_list = []
        self.assistant_response = []
        self.init_ui()
        self.setWindowIcon(QIcon("img/icon.ico"))

    def init_ui(self):
        fontdb = QFontDatabase()
        chat_font, console_font, info_font = (
            QFont(
                fontdb.applicationFontFamilies(
                    fontdb.addApplicationFont("./fonts/Raleway-Regular.ttf")
                )
            ),
            QFont(
                fontdb.applicationFontFamilies(
                    fontdb.addApplicationFont("./fonts/ShareTechMono-Regular.ttf")
                )
            ),
            QFont(
                fontdb.applicationFontFamilies(
                    fontdb.addApplicationFont("./fonts/Figtree-Regular.ttf")
                )
            ),
        )

        self.response_font = chat_font
        self.response_font.setPointSize(11)

        self.input_text_font = chat_font
        self.input_text_font.setPointSize(11)

        self.history_font = console_font
        self.history_font.setPointSize(11)

        self.pil_font = info_font
        self.pil_font.setPointSize(9)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout()

        self.create_menu()

        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems(["gpt-3.5-turbo"])
        self.model_dropdown.setEnabled(False)
        self.current_model = self.model_dropdown.currentText()
        self.main_layout.addWidget(self.model_dropdown)

        self.context_label = QLabel("Number of messages to keep in context: ")
        self.context_label.setToolTip(
            "The number of messages to keep in context for the AI. \nThe more messages, the more context the AI has to work with, but the longer it takes to generate a response. \nThe default is 2 and is recommended for most use cases. Choice is reflected after pressing submit and is not retroactive."
        )
        self.context_label.toolTip
        self.context_label.setFont(self.pil_font)
        self.context_label.setAlignment(Qt.AlignRight)
        self.main_layout.addWidget(self.context_label)

        self.context_choice = QComboBox()
        for i in range(0, 11):
            self.context_choice.addItem(str(i))
        self.context_choice.setCurrentIndex(2)
        self.context_choice.setToolTip(self.context_label.toolTip())
        self.main_layout.addWidget(self.context_choice)

        self.splitter = QSplitter(Qt.Vertical)  # type: ignore

        self.chat = QTextEdit()
        self.chat.setFont(self.response_font)
        self.chat.setFontPointSize(11)
        self.chat.setPlaceholderText("Your assistant's response will appear here")
        self.chat.setAcceptRichText(True)
        self.chat.setReadOnly(True)
        self.chat.toMarkdown()
        self.splitter.addWidget(self.chat)

        self.size_button_widget = QWidget()
        self.size_button_layout = QHBoxLayout()
        self.size_button_layout.setAlignment(Qt.AlignRight)
        self.minus_button = QPushButton("-")
        self.minus_button.setFixedWidth(30)
        self.plus_button = QPushButton("+")
        self.plus_button.setFixedWidth(30)
        self.plus_button.clicked.connect(self.increase_font_size)
        self.minus_button.clicked.connect(self.decrease_font_size)
        self.size_button_layout.addWidget(self.minus_button)
        self.size_button_layout.addWidget(self.plus_button)
        self.size_button_widget.setLayout(self.size_button_layout)
        self.splitter.addWidget(self.size_button_widget)

        self.input_text_edit = ChatInput(self.submit_text)
        self.input_text_edit.setFont(self.input_text_font)
        self.input_text_edit.setPlaceholderText("Enter your text here")
        self.input_text_edit.textChanged.connect(self.parse_text)  # type: ignore
        self.input_text_edit.setAcceptRichText(False)
        self.splitter.addWidget(self.input_text_edit)

        self.parsed_info_label = QLabel(
            f"Token Counts are estimated with Tiktoken and don't include special tokens or tokens added by the model and its response"
        )
        self.parsed_info_label.setWordWrap(True)
        self.parsed_info_label.setFont(self.pil_font)
        self.splitter.addWidget(self.parsed_info_label)

        self.tab_widget = QTabWidget()
        self.first_tab_widget = QWidget()
        self.first_tab_layout = QVBoxLayout()
        self.first_tab_layout.addWidget(self.splitter)
        self.splitter.setSizes([600, 10, 210, 80])

        self.bottom_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit")
        self.bottom_layout.addWidget(self.submit_button)

        self.submit_button.clicked.connect(self.submit_text)  # type: ignore
        self.submit_button.setAutoDefault(True)
        self.submit_button.setShortcut("Ctrl+Enter")
        self.submit_button.keyPressEvent = self.submit_text  # type: ignore

        self.first_tab_layout.addLayout(self.bottom_layout)
        self.first_tab_widget.setLayout(self.first_tab_layout)
        self.tab_widget.addTab(self.first_tab_widget, self.model_dropdown.currentText())

        self.history = QTextEdit()

        self.history.setFont(self.history_font)
        self.history.setReadOnly(True)
        self.history.setPlaceholderText(
            "Your assistant's raw responses will appear here"
        )

        self.second_tab_widget = QWidget()
        self.second_tab_layout = QVBoxLayout()
        self.second_tab_layout.addWidget(self.history)
        self.second_tab_widget.setLayout(self.second_tab_layout)
        self.tab_widget.addTab(self.second_tab_widget, "Raw History")

        self.main_layout.addWidget(self.tab_widget)
        self.central_widget.setLayout(self.main_layout)

    def increase_font_size(self):
        # Get the current font size and increase it by 1
        current_size = self.chat.fontPointSize()
        self.chat.setVisible(False)
        self.chat.selectAll()
        new_size = current_size + 1
        # Set the new font size for the QTextEdit widget
        font = self.chat.currentFont()
        font.setPointSize(new_size)
        self.chat.setCurrentFont(font)
        self.chat.moveCursor(QTextCursor.End)
        self.chat.setVisible(True)

    def decrease_font_size(self):
        # Get the current font size and decrease it by 1
        current_size = self.chat.fontPointSize()
        self.chat.setVisible(False)
        self.chat.selectAll()
        new_size = current_size - 1 if current_size >= 1 else 1
        # Set the new font size for the QTextEdit widget
        font = self.chat.currentFont()
        font.setPointSize(new_size)
        self.chat.setCurrentFont(font)
        self.chat.setCurrentFont(font)
        self.chat.moveCursor(QTextCursor.End)
        self.chat.setVisible(True)

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
            self, "Save Chat", "", "MD Files (*.MD);;All Files (*)"
        )

        if file_path:
            with open(file_path, "w") as file:
                file.write(self.chat.toMarkdown())

    def export_history(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Raw History", "", "JSON Files (*.json);;All Files (*)"
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
        self.input_text_list = []
        self.assistant_response = []
        self.history.clear()
        self.chat.clear()

    def parse_text(self):
        input_text = self.input_text_edit.toPlainText()
        parsed_info = self.parse_information(input_text)
        self.parsed_info_label.setText(parsed_info)

    @staticmethod
    def parse_information(text, model="cl100k_base"):
        encoding = tiktoken.get_encoding(model)
        assert encoding.decode(encoding.encode(text)) == text
        num_tokens = len(encoding.encode(text))
        return f"Token count: {num_tokens}\tWord count: {len(text.split())},\tCharacter count: {len(text)}"
    
    def submit_text(self):
        self.input_text_list.append(self.input_text_edit.toPlainText())
        self.num_contexts = self.context_choice.currentIndex() + 1
        response = ChatModel().submit_text(
            self.input_text_list[-1 * self.num_contexts :],
            self.assistant_response[-1 * (self.num_contexts - 1) :],
        )
        self.assistant_response.append(response.choices[0].message.content)
        token_usage = self.token_count(response)
        self.parse_response(response, token_usage)
        self.history.append(json.dumps(response, indent=4))
        self.input_text_edit.clear()

    def parse_response(self, response, token_usage):
        print(self.input_text_list[-1])
        print(self.assistant_response[-1])
        self.chat.append(f"{self.input_text_list[-1]}")
        self.chat.append("\n\t" + "-" * 60 + "\n")
        self.chat.append(f"{self.assistant_response[-1]}")
        self.chat.moveCursor(QTextCursor.End)
        self.chat.append("\n")
        self.chat.append(token_usage)
        self.chat.append("\t" + "-" * 60 + "\n")
        self.chat.toMarkdown()

    def token_count(self, response):
        # Get usage information from the API response
        completion_tokens = response.usage.completion_tokens
        prompt_tokens = response.usage.prompt_tokens
        total_tokens = response.usage.total_tokens
        token_usage = f"Completion tokens: {completion_tokens}\tPrompt tokens: {prompt_tokens}\nTotal tokens: {total_tokens}\n"
        return token_usage


if __name__ == "__main__":
    app = QApplication(sys.argv)
    color_scheme = {
        "primary": "#95a5a6",
        "secondary": "#1c1c24",
        "success": "#28a745",
        "danger": "#dc3545",
        "warning": "#ffc107",
        "info": "#869495",
        "light": "#f8f9fa",
        "dark": "#343a40",
    }
    style_sheet = (
        """
    QPushButton {
        background-color: %(primary)s;
        color: white;
        border: 1px solid %(primary)s;
        padding: 1px;
        border-radius: 10px;
    }
    QPushButton:hover {
        background-color: %(info)s;
    }
    QPushButton:pressed {
        background-color: %(secondary)s;
    }
    """
        % color_scheme
    )
    app.setStyleSheet(style_sheet)

    main_window = MainWindow()
    main_window.setWindowTitle("OpenAI API - GPT3.5-Turbo")
    main_window.setGeometry(400, 100, 600, 900)

    main_window.show()

    sys.exit(app.exec())
