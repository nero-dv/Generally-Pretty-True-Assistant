# Generally-Pretty-True-Assistant

![GUI](img/gpt-a_screenshot.png)

This Python program uses the OpenAI API to create a chat window that can be customized to meet the user's needs. 

It includes features such as saving chat history, viewing raw outputs from the API, and setting an API key. The program is designed to be user-friendly and helpful, allowing users to easily interact with the OpenAI API and receive responses in real-time. Overall, this program is a useful tool for anyone looking to leverage the power of the OpenAI API for their projects.

Please note that you must enter your own OpenAI API key either through the File Menu > Set API Key, or by setting the following environment variable (and logging out then back in for your login shell to recognize it)


```shell
OPENAI_API_KEY = yourAPIkeyhere
```

At the moment, you can run this program by running the following commands:


```shell
pip install --requirement=requirements.txt && python3 main.py
```

After installing the python requirements, you can just run "python3 main.py" by itself to run this program.