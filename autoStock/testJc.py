from stock.services import investment_service
import time
from autoStock import daishinTrade
from autoStock import Log
from sendMsg import telegram_bot
import psutil

# #거래마다 갱신되는 global 변수
BUY = 4  # 매수기준
SELL = 4  # 매도기준
JUST = 3  # 관망기준

buy_cnt = 0  # 매수시점 체크
sell_cnt = 0  # 매도시점 체크
just_cnt = 0  # 관망시점 체크

etfLeverage = ['A122630']  # KODEX 레버리지
etfInverse = ['A252670']  # KODEX 200선물인버스2X
# etfOther = ['A005930','A000270']    #삼성전자(A005930),기아차(A000270)
etfOther = []

# 연속성이 있는 global 변수
lastData = {}

# 개인 추세를 알수있도록 하기위한
gap_peo_list = [0, 0, 0, 0, 0, 0]
dev_gap_peo_list = [0] * (len(gap_peo_list) - 1)
dev_avg = 0.0

START_TIME = '091000'
FINAL_TIME = '151500'
END_TIME = '153000'

# 가감비율
RATE = 2

# 테스트용
isTest = True
dt = 0


def kospi_trade():  # 대신증권 크레온으로 주식거래
    writeLog('거래시작')

    global lastData
    res = None
    # tmpRes는 Real 작업 시 사용 변수
    tmpRes = lastData

    # 가장 최신 데이터 가져오기
    if len(lastData) == 0:  # 첫 거래의 경우
        writeLog("첫 데이터를 가져옵니다")
        res = investment_service.get_lasttime()

        if res is None:  # DB에 데이터가 없는경우
            writeLog("DB에 데이터가 존재하지 않습니다.")
            return
        else:
            # 일단 lastData에 백업
            lastData = res
            # # 테스트용

            if isTest:
                lastData = {'time': '090000',
                            'individual': 0,
                            'foreign': 0,
                            'institution': 0,
                            'kospi': 3200.0}
            return
    else:
        # 최신 데이터 가져오기 (where 이전데이터 보다 큰것만)
        res = investment_service.get_after_data(tmpRes['time'])

    # 최신 데이터와 이전데이터 비교
    for idx, data in enumerate(res):  # 데이터 복수 일 수 있음

        global dt
        global gap_peo_list
        global dev_gap_peo_list
        global dev_avg

        dt = data['time']
        # print(dt)

        # 개인
        now_people = data['individual']
        last_people = tmpRes['individual']
        gap_people = now_people - last_people

        # 외인
        now_for = data['foreign']
        last_for = tmpRes['foreign']
        gap_for = now_for - last_for

        # 기관
        now_ins = data['institution']
        last_ins = tmpRes['institution']
        gap_ins = now_ins - last_ins

        # KOSPI
        now_kospi = data['kospi']
        last_kospi = tmpRes['kospi']
        gap_kospi = now_kospi - last_kospi

        # 개인 추세
        # 개인 매수세 차이를 업데이트
        gap_peo_list[0:-1] = gap_peo_list[1:]
        gap_peo_list[-1] = gap_people

        # 개인 추세 반영전 평균 추세확보
        dev_avg = round(sum(dev_gap_peo_list) / len(dev_gap_peo_list), 2)

        # 개인 추세 반영 업데이트
        dev_gap_peo_list[0:-1] = dev_gap_peo_list[1:]
        dev_gap_peo_list[-1] = gap_peo_list[-1] - gap_peo_list[-2]

        # 개인 증가 또는 유지
        if now_people > last_people:
            # 기관, 외국인 감소
            if now_for < last_for and now_ins < last_ins and gap_kospi < 0:
                add_sell(2)  # 매도포지션 증가
            # 기관, 외국인 중 한곳만 증가 시 개인보다 작으면
            elif (RATE * gap_people) > (gap_for + gap_ins) and gap_kospi < 0:
                # print("[sell]",dt, " : ", gap_kospi, gap_people, (gap_for + gap_ins), gap_for, gap_ins)
                add_sell(1)
            # 기관, 외국인 증가
            elif now_for > last_for and now_ins > last_ins and gap_kospi > 0:
                add_buy(1)  # 매수포지션 증가
            # 그외
            else:
                add_just(1)  # 관망포지션 증가
        # 개인 감소
        elif now_people < last_people:
            # 기관, 외국인 증가
            if now_for > last_for and now_ins > last_ins and gap_kospi > 0:
                add_buy(2)  # 매수포지션 증가
            # 기관, 외국인 중 한곳만 감소 시 개인보다 작으면
            elif (RATE * gap_people) < (gap_for + gap_ins) and gap_kospi > 0:
                # print("[buy]",dt, " : ", gap_kospi, gap_people, (gap_for + gap_ins), gap_for, gap_ins)
                add_buy(1)
            # 기관, 외국인 감소
            elif now_for < last_for and now_ins < last_ins and gap_kospi < 0:
                add_sell(1)  # 매도포지션 증가
            # 그외
            else:
                add_just(1)  # 관망포지션 증가
        # 개인 유지
        else:
            # 기관, 외국인 증가
            if now_for > last_for and now_ins > last_ins and gap_kospi > 0:
                add_buy(1)  # 매수포지션 증가
            # 기관, 외국인 감소
            elif now_for < last_for and now_ins < last_ins and gap_kospi < 0:
                add_sell(1)  # 매도포지션 증가
            # 그외
            else:
                add_just(1)  # 관망포지션 증가

        # 임시데이터 <- 최신데이터
        tmpRes = data

    # 이전데이터 <- 임시데이터 <- 최신데이터
    lastData = tmpRes


def isReal():
    # 마지막 추세가 이전의 추세의 방향이 같으면 인정한다
    if dev_gap_peo_list[-1] * dev_avg >= 0:
        return True

    return False


def add_buy(cnt):
    global buy_cnt
    global sell_cnt
    global just_cnt

    # 추세여부에 대한검증
    res = isReal()
    if res is False:
        # writeLog(dt, 'PASS - [매수]레버리지 매수 & 인버스매도')
        return
    else:
        buy_cnt = buy_cnt + cnt
        sell_cnt = 0
        just_cnt = 0
        # 테스트인 경우
        if isTest is False:
            writeLog('매수시점 증가 ', buy_cnt, ', ', sell_cnt, ', ', just_cnt)

        # buy_or_sell()
        if buy_cnt >= BUY:
            # 매수
            buy_kospi()


def add_sell(cnt):
    global buy_cnt
    global sell_cnt
    global just_cnt

    # 추세여부에 대한검증
    res = isReal()
    if res is False:
        # writeLog(dt, 'PASS - [매도]인버스매수 & 레버리지매도')
        return
    else:
        buy_cnt = 0
        sell_cnt = sell_cnt + cnt
        just_cnt = 0
        if isTest is False:
            writeLog('매도시점 증가 ', buy_cnt, ', ', sell_cnt, ', ', just_cnt)

        # buy_or_sell()
        if sell_cnt >= SELL:
            # 매도
            sell_kospi()


def add_just(cnt):
    global buy_cnt
    global sell_cnt
    global just_cnt
    buy_cnt = 0
    sell_cnt = 0
    just_cnt = just_cnt + cnt
    if isTest is False:
        writeLog('관망시점 증가 ', buy_cnt, ', ', sell_cnt, ', ', just_cnt)

    # 관망은 추세에 대한 검증 없다.

    # buy_or_sell()
    if just_cnt >= JUST:
        sell_just_kospi()


def buy_or_sell():
    if buy_cnt >= BUY:
        # 매수
        buy_kospi()
    elif sell_cnt >= SELL:
        # 매도
        sell_kospi()
    elif just_cnt >= JUST:
        # 매도하고 관망
        sell_just_kospi()


def buy_kospi():
    writeLog(dt, '[매수]레버리지 매수 & 인버스매도')
    # 테스트인 경우
    if isTest:
        return

    goto_buy = []

    # 현재 보유종목 가져오기
    stock_code, stocks = daishinTrade.getJango()

    # 미체결 있으면 해당 종목취소
    # 좀 나중에 개발..

    # 인버스 매도
    for etf in etfInverse:  # 인버스 대상매도
        if etf in stock_code:

            # 보유수량 확인
            amount = 0
            buyPrice = 0
            for s in stocks:
                if s['code'] == etf:
                    amount = s['amount']
                    buyPrice = s['buyPrice']
                    break

            writeLog(" - 인버스(", etf, ") 매도 : ", amount, '주, 매입가격 : ', buyPrice)

            # 임시
            s = time.strftime('[%H:%M:%S]')
            s += '[매수]레버리지 매수 & 인버스매도'
            telegram_bot.sendMsg(s)

            # 메도주문
            daishinTrade.goTrade(code=etf, bs='1', cnt=amount)

        else:
            writeLog(" - 인버스(", etf, ")는 잔고에 존재하지 않습니다.")

    # 레버리지 매수
    for etf in etfLeverage:  # 레버리지 대상구매
        if etf in stock_code:
            writeLog(" - 레버리지(", etf, ")는 잔고에 존재합니다.")
        else:
            goto_buy.append(etf)

    for other in etfOther:  # 레버리지 외의 다른종목 대상구매
        if other in stock_code:
            writeLog(" - ", other, "종목은 잔고에 존재합니다.")
        else:
            goto_buy.append(other)

    # 매수(어떤가격으로 매수를 해야할지..)
    # goto_buy 매수
    writeLog(" - 매수대상 : ", goto_buy.__str__())
    for stock in goto_buy:
        # 레버리지는 70주 나머지 종목은 10주
        amount = 10
        if stock == 'A122630':
            amount = 70

        daishinTrade.goTrade(code=stock, bs='2', cnt=amount)

    # 초기화
    init_tran_val()


def sell_kospi():  # 1:매도, 2: 매수

    writeLog(dt, '[매도]인버스매수 & 레버리지매도')
    # 테스트인 경우
    if isTest:
        return

    goto_sell = []
    # 현재 보유종목 가져오기
    stock_code, stocks = daishinTrade.getJango()

    # 미체결 있으면 해당 종목취소
    # 좀 나중에 개발..

    # 레버리지 매도
    for etf in etfLeverage:  # 레버리지 대상구매
        if etf in stock_code:
            goto_sell.append(etf)
        else:
            writeLog(" - 레버리지(", etf, ")는 잔고에 존재하지않습니다.")

    for other in etfOther:  # 레버리지 외의 다른종목 대상구매
        if other in stock_code:
            goto_sell.append(other)
        else:
            writeLog(" - ", other, "종목은 잔고에 존재하지않습니다.")

    # 매도(어떤가격으로 매도를 해야할지..)
    # goto_sell 매도
    writeLog(" - 매도대상 : ", goto_sell.__str__())

    # 1:매도, 2: 매수
    for sellCode in goto_sell:

        # 보유수량 확인
        amount = 0
        for s in stocks:
            if s['code'] == sellCode:
                amount = s['amount']
                break

        # 임시
        s = time.strftime('[%H:%M:%S]')
        s += '[매도]인버스매수 & 레버리지매도'
        telegram_bot.sendMsg(s)

        daishinTrade.goTrade(code=sellCode, bs='1', cnt=amount)

    # 인버스 매수
    for etf in etfInverse:  # 레버리지 대상구매
        if etf in stock_code:
            writeLog(" - 인버스(", etf, ")는 잔고에 존재합니다.")
        else:
            # 인버스 1000주 매수
            writeLog(" - 인버스 매수")
            daishinTrade.goTrade(code=etf, bs='2', cnt=1000)

    # 초기화
    init_tran_val()


# sell_all_kospi 와 로직 같음. 로그만 다름
def sell_just_kospi():
    writeLog(dt, '[관망]매도')
    # 테스트인 경우
    if isTest:
        return

    # 현재 보유종목 가져오기
    stock_code, stocks = daishinTrade.getJango()

    # 1:매도, 2: 매수
    for sellCode in stock_code:
        # 보유수량 확인
        amount = 0
        for s in stocks:
            if s['code'] == sellCode:
                amount = s['amount']
                break

        daishinTrade.goTrade(code=sellCode, bs='1', cnt=amount)

    if len(stock_code) == 0:
        writeLog('관망을 위해 매도할 종목이 없습니다.')
    else:
        # 임시
        s = time.strftime('[%H:%M:%S]')
        s += '[관망]매도'
        telegram_bot.sendMsg(s)

    # 초기화
    init_tran_val()


def sell_all_kospi():
    writeLog('[전량매도]')

    # 현재 보유종목 가져오기
    stock_code, stocks = daishinTrade.getJango()

    # 1:매도, 2: 매수
    for sellCode in stock_code:
        # 보유수량 확인
        amount = 0
        for s in stocks:
            if s['code'] == sellCode:
                amount = s['amount']
                break

        daishinTrade.goTrade(code=sellCode, bs='1', cnt=amount)

    if len(stock_code) == 0:
        writeLog('매도할 종목이 없습니다.')
    else:
        # 임시
        s = time.strftime('[%H:%M:%S]')
        s += '[전량매도]'
        telegram_bot.sendMsg(s)


def writeLog(*text):
    Log.writeTradeLog(text)


# def writeTLog(*text):
#     Log.writeTelegramLog(text)

def init_tran_val():
    global buy_cnt  # 매수시점 체크
    global sell_cnt  # 매도시점 체크
    global just_cnt  # 매도시점 체크
    buy_cnt = 0
    sell_cnt = 0
    just_cnt = 0


def init_other_val():
    # 연속성이 있는 global 변수
    global lastData
    lastData = {}


if __name__ == '__main__':

    # 초기 글로벌 데이터 초기화
    init_tran_val()

    # 일괄매도 변수 초기화(False)
    init_other_val()

    # # 주문체결은 실시간요청. 테스트 필요함
    # 참고 : https://money2.creontrade.com/e5/mboard/ptype_basic/plusPDS/DW_Basic_Read.aspx?boardseq=299&seq=73&page=1&searchString=%eb%a7%a4%ec%88%98&prd=&lang=7&p=8833&v=8639&m=9505
    # conclution = daishinTrade.CpPBConclusion()
    # conclution.Subscribe(self)

    # START
    while True:
        now = time.strftime('%H%M%S')

        if isTest is False:
            if START_TIME > now:
                writeLog("거래 시작전입니다.")
                time.sleep(10)
                continue

            if END_TIME < now:
                writeLog("거래장이 마감되었습니다. 종료합니다.")
                break

            if FINAL_TIME < now:
                # 일괄매도
                sell_all_kospi()
                time.sleep(60)
                continue

        # Lets START
        kospi_trade()

        writeLog("거래대기중입니다.")
        time.sleep(10)
