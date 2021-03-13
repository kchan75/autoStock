import win32com.client
# from . import Log
import time
import ctypes
from sendMsg import telegram_bot

g_objCodeMgr = win32com.client.Dispatch('CpUtil.CpCodeMgr')
g_objCpStatus = win32com.client.Dispatch('CpUtil.CpCybos')
g_objCpTrade = win32com.client.Dispatch('CpTrade.CpTdUtil')


# CpEvent: 실시간 이벤트 수신 클래스
class CpEvent:
    def set_params(self, client, name, parent):
        self.client = client  # CP 실시간 통신 object
        self.name = name  # 서비스가 다른 이벤트를 구분하기 위한 이름
        self.parent = parent  # callback 을 위해 보관

        # 구분값 : 텍스트로 변경하기 위해 딕셔너리 이용
        self.dicflag12 = {'1': '매도', '2': '매수'}
        self.dicflag14 = {'1': '체결', '2': '확인', '3': '거부', '4': '접수'}
        self.dicflag15 = {'00': '해당없음', '01': '유통융자', '02': '자기융자', '03': '유통대주',
                          '04': '자기대주', '05': '주식담보대출'}
        self.dicflag16 = {'1': '정상주문', '2': '정정주문', '3': '취소주문'}
        self.dicflag17 = {'1': '현금', '2': '신용', '3': '선물대용', '4': '공매도'}
        self.dicflag18 = {'01': '보통', '02': '임의', '03': '시장가', '05': '조건부지정가'}
        self.dicflag19 = {'0': '없음', '1': 'IOC', '2': 'FOK'}

    # PLUS 로 부터 실제로 시세를 수신 받는 이벤트 핸들러
    def OnReceived(self):
        print(self.name)
        if self.name == 'conclution':
            # 주문 체결 실시간 업데이트
            conc = {}

            # 체결 플래그
            conc['체결플래그'] = self.dicflag14[self.client.GetHeaderValue(14)]

            conc['주문번호'] = self.client.GetHeaderValue(5)  # 주문번호
            conc['주문수량'] = self.client.GetHeaderValue(3)  # 주문/체결 수량
            conc['주문가격'] = self.client.GetHeaderValue(4)  # 주문/체결 가격
            conc['원주문'] = self.client.GetHeaderValue(6)
            conc['종목코드'] = self.client.GetHeaderValue(9)  # 종목코드
            conc['종목명'] = g_objCodeMgr.CodeToName(conc['종목코드'])

            conc['매수매도'] = self.dicflag12[self.client.GetHeaderValue(12)]

            flag15 = self.client.GetHeaderValue(15)  # 신용대출구분코드
            if (flag15 in self.dicflag15):
                conc['신용대출'] = self.dicflag15[flag15]
            else:
                conc['신용대출'] = '기타'

            conc['정정취소'] = self.dicflag16[self.client.GetHeaderValue(16)]
            conc['현금신용'] = self.dicflag17[self.client.GetHeaderValue(17)]
            conc['주문조건'] = self.dicflag19[self.client.GetHeaderValue(19)]

            conc['체결기준잔고수량'] = self.client.GetHeaderValue(23)
            conc['대출일'] = self.client.GetHeaderValue(20)
            flag18 = self.client.GetHeaderValue(18)
            if (flag18 in self.dicflag18):
                conc['주문호가구분'] = self.dicflag18[flag18]
            else:
                conc['주문호가구분'] = '기타'

            conc['매도가능수량'] = self.client.GetHeaderValue(22)

            print(conc)

            return


# CpPBConclusion: 실시간 주문 체결 수신 클래그
class CpPBConclusion:
    def __init__(self):
        self.name = 'conclution'
        self.obj = win32com.client.Dispatch('DsCbo1.CpConclusion')

    def Subscribe(self, parent):
        self.parent = parent
        handler = win32com.client.WithEvents(self.obj, CpEvent)
        handler.set_params(self.obj, self.name, parent)
        self.obj.Subscribe()

    def Unsubscribe(self):
        self.obj.Unsubscribe()

# Cp6033 : 주식 잔고 조회
class Cp6033:
    def __init__(self):
        # 통신 OBJECT 기본 세팅
        self.objTrade = win32com.client.Dispatch("CpTrade.CpTdUtil")
        initCheck = self.objTrade.TradeInit(0)
        if (initCheck != 0):
           writeLog("주문 초기화 실패")
           return

        acc = self.objTrade.AccountNumber[0]  # 계좌번호
        accFlag = self.objTrade.GoodsList(acc, 1)  # 주식상품 구분
        # writeLog("계좌번호 : ", acc, " 상품구분 : ",accFlag[0])

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
        writeLog("잔고조회 : ", rqStatus, ", ",rqRet)
        if rqStatus != 0:
            return False

        cnt = self.objRq.GetHeaderValue(7)
        writeLog( "종목코드 종목명 체결잔고수량 매입가격" )
        for i in range(cnt):

            code = self.objRq.GetDataValue(12, i)  # 종목코드
            name = self.objRq.GetDataValue(0, i)  # 종목명
            amount = self.objRq.GetDataValue(7, i)  # 체결잔고수량
            buyPrice = self.objRq.GetDataValue(17, i)  # 체결장부단가
            tmp = {'code':code, 'name' : name, 'amount' : amount, 'buyPrice': buyPrice}
            retcode.append(tmp)
            writeLog(code, name, amount, buyPrice)

    def Request(self, retCode):
        self.rq6033(retCode)

        # 연속 데이터 조회 - 200 개까지만.
        while self.objRq.Continue:
            self.rq6033(retCode)
            # print(len(retCode))
            if len(retCode) >= 200:
                break

## 주식현재가 조회
class CpStockMst:
    def Request(code):
        # 연결 여부 체크
        objCpCybos = win32com.client.Dispatch("CpUtil.CpCybos")
        bConnect = objCpCybos.IsConnect
        if (bConnect == 0):
            print("PLUS가 정상적으로 연결되지 않음. ")
            return 0, False

        # 현재가 객체 구하기
        objStockMst = win32com.client.Dispatch("DsCbo1.StockMst")
        objStockMst.SetInputValue(0, code)  # 종목 코드 - 삼성전자
        objStockMst.BlockRequest()

        # 현재가 통신 및 통신 에러 처리
        rqStatus = objStockMst.GetDibStatus()
        rqRet = objStockMst.GetDibMsg1()
        # print("통신상태", rqStatus, rqRet)
        if rqStatus != 0:
            return 0, False

        # 현재가 정보 조회
        code = objStockMst.GetHeaderValue(0)  # 종목코드
        name = objStockMst.GetHeaderValue(1)  # 종목명
        time = objStockMst.GetHeaderValue(4)  # 시간
        cprice = objStockMst.GetHeaderValue(11)  # 종가
        diff = objStockMst.GetHeaderValue(12)  # 대비
        open = objStockMst.GetHeaderValue(13)  # 시가
        high = objStockMst.GetHeaderValue(14)  # 고가
        low = objStockMst.GetHeaderValue(15)  # 저가
        offer = objStockMst.GetHeaderValue(16)  # 매도호가
        bid = objStockMst.GetHeaderValue(17)  # 매수호가
        vol = objStockMst.GetHeaderValue(18)  # 거래량
        vol_value = objStockMst.GetHeaderValue(19)  # 거래대금

        # print("코드 이름 시간 현재가 대비 시가 고가 저가 매도호가 매수호가 거래량 거래대금")
        # print(code, name, time, cprice, diff, open, high, low, offer, bid, vol, vol_value)
        return cprice, True


class CpRPCurrentPrice:
    def __init__(self):
        self.objStockMst = win32com.client.Dispatch("DsCbo1.StockMst")
        return

    def Request(self, code):
        # 수신 받은 현재가 정보를 rtMst 에 저장
        price = self.objStockMst.GetHeaderValue(11)  # 종가
        return price


def getCurPrice(code):
    cpr = CpRPCurrentPrice()
    return cpr.Request(code)


def getJango():
    stocks = []
    stock_code = []

    obj6033 = Cp6033()

    if obj6033.Request(stocks) == False:
        writeLog('통신에러')

    else:
        for stock in stocks:
            # print('code : ' + stock['code'] + "name : " + stock['name'])
            stock_code.append(stock['code'])
    return stock_code, stocks

## 현재가 조회
def getNowPrice(code):
    objStockMst = CpStockMst
    price, isSucc = objStockMst.Request(code)

    if isSucc is False:
        writeLog('현재가 조회에러')

    return price


def goTrade(code, bs, cnt):
    # 주문 초기화
    objTrade = win32com.client.Dispatch("CpTrade.CpTdUtil")
    initCheck = objTrade.TradeInit(0)

    if (initCheck != 0):
        writeLog("주문 초기화 실패")
        return True

    price = getCurPrice(code)

    # 주식 매수 주문
    acc = objTrade.AccountNumber[0]  # 계좌번호
    accFlag = objTrade.GoodsList(acc, 1)  # 주식상품 구분
    # print(acc, accFlag[0])
    objStockOrder = win32com.client.Dispatch("CpTrade.CpTd0311")
    objStockOrder.SetInputValue(0, bs)  # 1:매도, 2: 매수
    objStockOrder.SetInputValue(1, acc)  # 계좌번호
    objStockOrder.SetInputValue(2, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
    objStockOrder.SetInputValue(3, code)  # 종목코드 - 필요한 종목으로 변경 필요
    objStockOrder.SetInputValue(4, cnt)  # 매수수량 - 요청 수량으로 변경 필요
    objStockOrder.SetInputValue(5, price)  # 주문단가 - 필요한 가격으로 변경 필요
    objStockOrder.SetInputValue(7, "0")  # 주문 조건 구분 코드, 0: 기본 1: IOC 2:FOK
    objStockOrder.SetInputValue(8, "03")  # 주문호가 구분코드 - 01: 보통, 03:시장가

    # 매수 주문 요청
    nRet = objStockOrder.BlockRequest()
    if (nRet != 0):
        writeLog("주문요청 오류", nRet)
        # 0: 정상,  그 외 오류, 4: 주문요청제한 개수 초과
        return False

    rqStatus = objStockOrder.GetDibStatus()
    errMsg = objStockOrder.GetDibMsg1()
    if rqStatus != 0:
        writeLog("주문 실패: ", rqStatus, errMsg)
        return False

    return True

def writeLog(*text):
    # Log.writeTradeLog(text)
    print(text)

if __name__ == "__main__":

    if ctypes.windll.shell32.IsUserAnAdmin():
        print('정상: 관리자권한으로 실행된 프로세스입니다.')
    else:
        print('오류: 일반권한으로 실행됨. 관리자 권한으로 실행해 주세요')

    # 연결 여부 체크
    if (g_objCpStatus.IsConnect == 0):
        print("PLUS가 정상적으로 연결되지 않음. ")

    # 주문 관련 초기화
    if (g_objCpTrade.TradeInit(0) != 0):
        print("주문 초기화 실패")

    while True:
        stocks = []
        try:
            obj6033 = Cp6033()
            if obj6033.Request(stocks) == False:
                print('통신에러')
            else:
                for stock in stocks:
                    print('code : ' + stock['code'] + "name : " + stock['name'] )

            time.sleep(5)
            s = time.strftime('[%H:%M:%S]')
            print(s)
        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            print('예외가 발생했습니다.', e)

