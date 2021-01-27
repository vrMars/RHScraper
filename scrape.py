import requests
import os.path as path
import time
import oauth

rhUsername, rhPassword = open('rh_creds.txt', 'r').read().split()

token = (oauth.getToken()).rstrip()

url = "https://api.robinhood.com/oauth2/token/"

ordersUrl = "https://api.robinhood.com/orders/"

optionsOrdersUrl = "https://api.robinhood.com/options/orders/"

optionsPositionsUrl = "https://api.robinhood.com/options/positions/"

optionsMarketDataUrl = "https://api.robinhood.com/marketdata/options/"

quotesUrl = "https://api.robinhood.com/quotes/"


headers = {
    'authority': 'api.robinhood.com',
    'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
    'x-robinhood-api-version': '1.411.9',
    'dnt': '1',
    'authorization': token,
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
    'accept': '*/*',
    'origin': 'https://robinhood.com',
    'sec-fetch-site': 'same-site',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://robinhood.com/',
    'accept-language': 'en-US,en;q=0.9',
}

def getProfits(holdings, token):
    headers = {
        'authority': 'api.robinhood.com',
        'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
        'x-robinhood-api-version': '1.411.9',
        'dnt': '1',
        'authorization': token,
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
        'accept': '*/*',
        'origin': 'https://robinhood.com',
        'sec-fetch-site': 'same-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://robinhood.com/',
        'accept-language': 'en-US,en;q=0.9',
    }
    
    out = []
    for (ticker, pos) in holdings:
        posRes = requests.get(pos, headers=headers)
        posJson = posRes.json()

        quoteRes = requests.get(quotesUrl + ticker + '/', headers=headers)
        quoteJson = quoteRes.json()
        curPrice = 0.0
        if quoteJson["last_extended_hours_trade_price"] != None:
            curPrice = float(quoteJson["last_extended_hours_trade_price"])
        else:
            curPrice = float(quoteJson["last_trade_price"])

        if float(posJson["quantity"]) != 0:
            numProfits = (curPrice - float(posJson["average_buy_price"])) * float(posJson["quantity"])
            profits = '$' + str("{:.2f}".format(abs(numProfits)))
            if numProfits > 0:
                profits = '+' + profits
            else:
                profits = '-' + profits

            percent = curPrice / float(posJson["average_buy_price"])
            if percent < 1:
                percent = -(1-percent) * 100
            else:
                percent = (percent - 1) * 100
            percent = str("{:.2f}".format(percent))
            percent = percent + '%'
            out.append(('$' + ticker, profits, percent))
    return out

def getOptionsProfits(holdings_options, token):
    out = []
    for (ticker, id, premium, quantity, timestamp) in holdings_options:
        totalCost = float(quantity)*float(premium)
        posRes = requests.get(optionsMarketDataUrl + id + '/', headers=headers)
        posJson = posRes.json()
        profits = float(posJson["adjusted_mark_price"]) * 100 * float(quantity)
        curPrice = '$' + str("{:.2f}".format(abs(profits - totalCost)))
        if profits > 0:
            curPrice = '+' + curPrice
        else:
            curPrice = '-' + curPrice

        percent = profits / totalCost
        if percent < 1:
            percent = -(1-percent) * 100
        else:
            percent = (percent - 1) * 100
        percent = str("{:.2f}".format(percent))
        percent = percent + '%'
        out.append(('@' + ticker, curPrice, percent))
    return out


def getOrders(token):
    headers = {
        'authority': 'api.robinhood.com',
        'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
        'x-robinhood-api-version': '1.411.9',
        'dnt': '1',
        'authorization': token,
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
        'accept': '*/*',
        'origin': 'https://robinhood.com',
        'sec-fetch-site': 'same-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://robinhood.com/',
        'accept-language': 'en-US,en;q=0.9',
    }

    response = requests.get(ordersUrl, headers=headers)
    out = response.json()
    nxt = out["next"]
    results = out["results"]
    while nxt != None:
        response = requests.get(nxt, headers=headers)
        out = response.json()
        nxt = out["next"]
        results += out["results"]
    instruments = set()
    for res in results:
        if res["state"] != "cancelled" and res["side"] == "buy":
            instruments.add((res["instrument"], res["last_transaction_at"], res["position"]))
    instruments = list(sorted(list(instruments), key=lambda x: x[1], reverse=True))
    holdings = set()
    output = []
    for (i,v, pos) in instruments:
        response = requests.get(i, headers=headers)
        out = response.json()
        if out["symbol"] in holdings:
            continue
        holdings.add(out["symbol"])
        output.append((out["symbol"], pos))
    f = open('holdings', 'w')
    f.write("\n".join('{} {}'.format(x[0], x[1]) for x in output))
    f.close()
    return output

def getOptionsOrders(token):
    response = requests.get(optionsOrdersUrl, headers=headers)
    out = response.json()
    nxt = out["next"]
    results = out["results"]

    while nxt != None:
        response = requests.get(nxt, headers=headers)
        out = response.json()
        nxt = out["next"]
        results += out["results"]

    closedSet = set()
    resSet = set()

    def getOptionId(res):
        idUrl = (res["legs"][0]["option"]).split('/')
        return idUrl[-2]

    for result in results:
        idUrl = getOptionId(result)
        if result["closing_strategy"] != None or float(result["canceled_quantity"]) != 0:
            closedSet.add(idUrl)
        elif idUrl not in closedSet:
            # closing strat is none; not previously closed
            # [optionId, premium, quantity, last_updated]
            resSet.add((result["chain_symbol"], idUrl, result["premium"], result["quantity"], result["updated_at"]))
    resSet = list(sorted(list(resSet), key=lambda x: x[4], reverse=True))
    f = open('holdings_options', 'w')
    f.write("\n".join('{} {} {} {} {}'.format(x[0], x[1], x[2], x[3], x[4]) for x in resSet))
    f.close()
    return resSet


holdings = []
optionsHoldings = []

if path.exists("holdings") == False or path.exists("optionsHoldings") == False:
    # print("holdings path does not exist")
    holdings = getOrders(token)
    optionsHoldings = getOptionsOrders(token)
else:
    f = open("holdings", "r")
    file_time = path.getmtime("holdings")
    if (time.time() - file_time) / 3600 > 1:
        # print("remaking holding")
        # older than 1 hour; remake
        f.close()
        holdings = getOrders(token)
    else:
        # print("reusing old holdings")
        lines = f.readlines()
        for l in lines:
            holdings.append(tuple(l.split()))
        f.close()

    f = open("optionsHoldings", "r")
    file_time = path.getmtime("optionsHoldings")
    if (time.time() - file_time) / 3600 > 1:
        f.close()
        optionsHoldings = getOptionsOrders(token)
    else:
        lines = f.readlines()
        for l in lines:
            optionsHoldings.append(tuple(l.split()))
        f.close()

profits = getOptionsProfits(optionsHoldings, token)
profits += getProfits(holdings, token)
f = open('profits', 'w')
for p in profits:
    f.write("  ".join(p))
    f.write("\n")
f.close()

