import sys
from PyQt5.QtWidgets import *
import win32com.client
import math
import telegram


# 설명: 주식 계좌잔고 종목(최대 200개)을 가져와 현재가  실시간 조회하는 샘플
# CpEvent: 실시간 현재가 수신 클래스
# CpStockCur : 현재가 실시간 통신 클래스
# Cp6033 : 주식 잔고 조회
# CpMarketEye: 복수 종목 조회 서비스 - 200 종목 현재가를 조회 함.

# CpEvent: 실시간 이벤트 수신 클래스
class CpEvent:
    def set_params(self, client):
        self.client = client

    def OnReceived(self):
        code = self.client.GetHeaderValue(0)  # 초
        name = self.client.GetHeaderValue(1)  # 초
        timess = self.client.GetHeaderValue(18)  # 초
        exFlag = self.client.GetHeaderValue(19)  # 예상체결 플래그
        cprice = self.client.GetHeaderValue(13)  # 현재가
        diff = self.client.GetHeaderValue(2)  # 대비
        cVol = self.client.GetHeaderValue(17)  # 순간체결수량
        vol = self.client.GetHeaderValue(9)  # 거래량

        if (exFlag == ord('1')):  # 동시호가 시간 (예상체결)
            print("실시간(예상체결)", name, timess, "*", cprice, "대비", diff, "체결량", cVol, "거래량", vol)
        elif (exFlag == ord('2')):  # 장중(체결)
            print("실시간(장중 체결)", name, timess, cprice, "대비", diff, "체결량", cVol, "거래량", vol)


# CpStockCur: 실시간 현재가 요청 클래스
class CpStockCur:
    def Subscribe(self, code):
        self.objStockCur = win32com.client.Dispatch("DsCbo1.StockCur")
        handler = win32com.client.WithEvents(self.objStockCur, CpEvent)
        self.objStockCur.SetInputValue(0, code)
        handler.set_params(self.objStockCur)
        self.objStockCur.Subscribe()

    def Unsubscribe(self):
        self.objStockCur.Unsubscribe()


# Cp6033 : 주식 잔고 조회
class Cp6033:
    def __init__(self):
        # 통신 OBJECT 기본 세팅
        self.objTrade = win32com.client.Dispatch("CpTrade.CpTdUtil")
        initCheck = self.objTrade.TradeInit(0)
        if (initCheck != 0):
            print("주문 초기화 실패")
            return

        #
        acc = self.objTrade.AccountNumber[0]  # 계좌번호
        accFlag = self.objTrade.GoodsList(acc, 1)  # 주식상품 구분
        print(acc, accFlag[0])

        self.objRq = win32com.client.Dispatch("CpTrade.CpTd6033")
        self.objRq.SetInputValue(0, acc)  # 계좌번호
        self.objRq.SetInputValue(1, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
        self.objRq.SetInputValue(2, 50)  # 요청 건수(최대 50)

    # 실제적인 6033 통신 처리
    def rq6033(self, retcode):
        self.objRq.BlockRequest()

        # 통신 및 통신 에러 처리
        rqStatus = self.objRq.GetDibStatus()
        rqRet = self.objRq.GetDibMsg1()
        print("통신상태", rqStatus, rqRet)
        if rqStatus != 0:
            return False

        cnt = self.objRq.GetHeaderValue(7)
        print("종목코드 종목명 체결잔고수량 ")
        for i in range(cnt):

            code = self.objRq.GetDataValue(12, i)  # 종목코드
            name = self.objRq.GetDataValue(0, i)  # 종목명
            amount = self.objRq.GetDataValue(7, i)  # 체결잔고수량
            buyPrice = self.objRq.GetDataValue(17, i)  # 체결장부단가
            tmp = {'code':code, 'name' : name, 'amount' : amount, 'buyPrice': buyPrice}
            retcode.append(tmp)
            print(code, name, amount, buyPrice)

    def Request(self, retCode):
        self.rq6033(retCode)

        # 연속 데이터 조회 - 200 개까지만.
        while self.objRq.Continue:
            self.rq6033(retCode)
            # print(len(retCode))
            if len(retCode) >= 200:
                break


# CpMarketEye : 복수종목 현재가 통신 서비스
class CpMarketEye:
    def Request(self, codes, rqField):
        # 연결 여부 체크
        objCpCybos = win32com.client.Dispatch("CpUtil.CpCybos")
        bConnect = objCpCybos.IsConnect
        if (bConnect == 0):
            print("PLUS가 정상적으로 연결되지 않음. ")
            return False

        # 관심종목 객체 구하기
        objRq = win32com.client.Dispatch("CpSysDib.MarketEye")
        # 요청 필드 세팅 - 종목코드, 종목명, 시간, 대비부호, 대비, 현재가, 거래량
        # rqField = [0,17, 1,2,3,4,10]
        objRq.SetInputValue(0, rqField)  # 요청 필드
        objRq.SetInputValue(1, codes)  # 종목코드 or 종목코드 리스트
        objRq.BlockRequest()

        # 현재가 통신 및 통신 에러 처리
        rqStatus = objRq.GetDibStatus()
        rqRet = objRq.GetDibMsg1()
        print("통신상태", rqStatus, rqRet)
        if rqStatus != 0:
            return False

        cnt = objRq.GetHeaderValue(2)

        for i in range(cnt):
            rpCode = objRq.GetDataValue(0, i)  # 코드
            rpName = objRq.GetDataValue(1, i)  # 종목명
            rpTime = objRq.GetDataValue(2, i)  # 시간
            rpDiffFlag = objRq.GetDataValue(3, i)  # 대비부호
            rpDiff = objRq.GetDataValue(4, i)  # 대비
            rpCur = objRq.GetDataValue(5, i)  # 현재가
            rpVol = objRq.GetDataValue(6, i)  # 거래량
            print(rpCode, rpName, rpTime, rpDiffFlag, rpDiff, rpCur, rpVol)

        return True


class MyWindow(QMainWindow):

    def __init__(self):

        codes = []
        print("시작")
        obj6033 = Cp6033()
        if obj6033.Request(codes) == False:
            return

        print("잔고 종목 개수:", len(codes))

        # # 요청 필드 배열 - 종목코드, 시간, 대비부호 대비, 현재가, 거래량, 종목명
        # rqField = [0, 1, 2, 3, 4, 10, 17]  # 요청 필드
        # objMarkeyeye = CpMarketEye()
        # if (objMarkeyeye.Request(codes, rqField) == False):
        #     exit()


    def StopSubscribe(self):
        if self.isSB:
            cnt = len(self.objCur)
            for i in range(cnt):
                self.objCur[i].Unsubscribe()
            print(cnt, "종목 실시간 해지되었음")
        self.isSB = False

        self.objCur = []

    def btnStart_clicked(self):
        print("시작")
        self.StopSubscribe();
        codes = []
        print("시작")
        obj6033 = Cp6033()
        if obj6033.Request(codes) == False:
            return

        print("잔고 종목 개수:", len(codes))

        # 요청 필드 배열 - 종목코드, 시간, 대비부호 대비, 현재가, 거래량, 종목명
        rqField = [0, 1, 2, 3, 4, 10, 17]  # 요청 필드
        objMarkeyeye = CpMarketEye()
        if (objMarkeyeye.Request(codes, rqField) == False):
            exit()

        cnt = len(codes)
        for i in range(cnt):
            self.objCur.append(CpStockCur())
            self.objCur[i].Subscribe(codes[i])

        print("빼기빼기================-")
        print(cnt, "종목 실시간 현재가 요청 시작")
        self.isSB = True

    def btnStop_clicked(self):
        self.StopSubscribe()

    def btnExit_clicked(self):
        self.StopSubscribe()
        exit()


def a(status):
    s = 'AAA'
    s += 'BBB : '
    s += status
    print(s)

    k = 26912 / 26600.95845
    print(k)

if __name__ == "__main__":
    # app = QApplication(sys.argv)
    # myWindow = MyWindow()
    #myWindow.__init__
    ##myWindow.show()
    #myWindow.btnStart_clicked();
    # app.exec_()

    # ## 주문테스트
    # stocks = []
    #
    # obj6033 = Cp6033()
    # if obj6033.Request(stocks) == False:
    #     print('통신에러')
    # else:
    #     for stock in stocks:
    #         print('code : ' + stock['code'] + "name : " + stock['name'] )

    # ## TELEGRAM TEST
    # ID = '1561306520'
    # k_token = "1643866184:AAFmTNRv4qy23joXaqcXd95SEYNA2SOFNGU"
    # chat = telegram.Bot(token=k_token)
    # chat.sendMessage(chat_id = "1561306520", text="HI")

    T = [1000,1500,1900,2200,2400,2500,2550]
    L = [500,400,300,200,100,50]
    # T = [0]*len(L)
    # T[0:len(L)-1] = L[1:]
    # print(T)
    # print(L)
    # L = L[1:]
    # L[-1] = 99
    # print(L)

    # gap = [0,0,0,0,0,0]
    # dev_gap = [0]*(len(gap)-1)
    #
    # for i in L:
    #     gap[0:-1] = gap [1:]
    #     gap[-1] = i
    #
    #     dev_gap[0:-1] = dev_gap[1:]
    #     dev_gap[-1] = gap[-1] - gap[-2]
    #
    #     avg = round(sum(dev_gap[1:]) / len(dev_gap)-1, 2)
    #     print(gap,"->",dev_gap,":",avg)
    print(math.floor(7.05))

    a('MINUS')


