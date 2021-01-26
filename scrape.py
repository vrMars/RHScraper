import requests
import os.path as path
import gmail
import time

rhUsername, rhPassword = open('rh_creds.txt', 'r').read().split()


url = "https://api.robinhood.com/oauth2/token/"

ordersUrl = "https://api.robinhood.com/orders/"

quotesUrl = "https://api.robinhood.com/quotes/"

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


def genToken(mfa):
    payload = "{\"grant_type\":\"password\",\"scope\":\"internal\",\"client_id\":\"c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS\",\"expires_in\":86400,\"device_token\":\"4dfc5356-bd56-41c2-85a6-f1da6c499200\",\"username\":\"%s\",\"password\":\"%s\", \"mfa_code\":\"%s\"}" % (rhUsername, rhPassword, mfa)

    headers = {
        'authority': 'api.robinhood.com',
        'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
        'x-robinhood-api-version': '1.411.9',
        'dnt': '1',
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
        'content-type': 'application/json',
        'accept': '*/*',
        'origin': 'https://robinhood.com',
        'sec-fetch-site': 'same-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://robinhood.com/',
        'accept-language': 'en-US,en;q=0.9',
    }

    response = requests.request("POST", url, headers=headers, data = payload)

    token = "Bearer " + (response.json())["access_token"]
    print(token)
    return token

def genMfa():
    payload = "{\"grant_type\":\"password\",\"scope\":\"internal\",\"client_id\":\"c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS\",\"expires_in\":86400,\"device_token\":\"4dfc5356-bd56-41c2-85a6-f1da6c499200\",\"username\":\"%s\",\"password\":\"%s\"}" % (rhUsername, rhPassword)

    headers = {
        'authority': 'api.robinhood.com',
        'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
        'x-robinhood-api-version': '1.411.9',
        'dnt': '1',
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
        'content-type': 'application/json',
        'accept': '*/*',
        'origin': 'https://robinhood.com',
        'sec-fetch-site': 'same-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://robinhood.com/',
        'accept-language': 'en-US,en;q=0.9',
    }

    response = requests.request("POST", url, headers=headers, data = payload)
oldMfa = gmail.main()
genMfa()
time.sleep(5)
newMfa = gmail.main()
while (newMfa == oldMfa):
    newMfa = gmail.main()
token = genToken(newMfa)
holdings = []

if path.exists("holdings") == False:
    # print("holdings path does not exist")
    holdings = getOrders(token)
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

profits = getProfits(holdings, token)
f = open('profits', 'w')
for p in profits:
    f.write("  ".join(p))
    f.write("\n")
f.close()


