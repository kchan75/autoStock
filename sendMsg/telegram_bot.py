from . import chat, ID

def sendMsg(text):
    chat.sendMessage(chat_id=ID, text=text)
