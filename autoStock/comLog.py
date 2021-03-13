import time
from sendMsg import telegram_bot

class comLog:
    def __init__(self):
        t = time.strftime('%Y%m%d')
        # 로그데이터 파일 생성
        # Trading 관련 로그
        self.fd = open('C:\SDS\\autoStockLog\\' + t + '_trade.txt', mode='a', encoding='utf-8')

    def writeTradeLog(self, text):
        # 현재시간
        s = time.strftime('[%H:%M:%S]')
        # s = "[" + now[0:2] + "시" + now[2:4] + "분" + now[4:6] + "초" + "]"
        for t in text:
            s += str(t)
        print(s)
        self.fd.write(s+'\n')
        self.fd.flush()

    def writeTelegramLog(self, text):
        # 현재시간
        s = time.strftime('[%H:%M:%S]')
        # s = "[" + now[0:2] + "시" + now[2:4] + "분" + now[4:6] + "초" + "]"
        for t in text:
            s += str(t)
        print(s)
        self.fd.write(s+'\n')
        self.fd.flush()
        telegram_bot.sendMsg()


