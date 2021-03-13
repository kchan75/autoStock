from stock.services import market_data_service

if __name__ == '__main__':
    data_val = '2016.01.18'
    k_date, g_date, d_date = [],[],[]
    del_k_date, del_g_date, del_d_date = [],[],[]

    res_kospi, res_gold, res_dollar = market_data_service.get_data(data=data_val)

    for data in res_kospi:
        k_date.append(data['date'])

    for data in res_gold:
        g_date.append(data['date'])

    for data in res_dollar:
        d_date.append(data['date'])

    # KOSPI 정리 SET
    for date in k_date:
        if date not in g_date or date not in d_date:
            del_k_date.append(date)

    # GOLD 정리 SET
    for date in g_date:
        if date not in k_date or date not in d_date:
            del_g_date.append(date)

    # DOLLAR 정리 SET
    for date in d_date:
        if date not in k_date or date not in g_date:
            del_d_date.append(date)

    market_data_service.remove_kospi_by_date(datelist=del_k_date)   # KOSPI 정리
    market_data_service.remove_gold_by_date(datelist=del_g_date)    # GOLD 정리
    market_data_service.remove_dollar_by_date(datelist=del_d_date)  # DOLLAR 정리