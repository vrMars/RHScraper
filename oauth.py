import requests
import os.path as path
import time
import gmail

url = "https://api.robinhood.com/oauth2/token/"
rhUsername, rhPassword = open('rh_creds.txt', 'r').read().split()

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

def getToken():
    # check if token exists
    if path.exists("rhtoken"):
        file_time = path.getmtime("rhtoken")
        if (time.time() - file_time) / 3600 > 23:
            # older than 23 hours; refresh
            print("token expired; refreshing...")
            return refreshToken()
        f = open("rhtoken", "r")
        bearer = f.readline()
        f.close()
        return str(bearer)
    else:
        return refreshToken()

def genToken(mfa):
    payload = "{\"grant_type\":\"password\",\"scope\":\"internal\",\"client_id\":\"c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS\",\"expires_in\":86400,\"device_token\":\"4dfc5356-bd56-41c2-85a6-f1da6c499200\",\"username\":\"%s\",\"password\":\"%s\", \"mfa_code\":\"%s\"}" % (rhUsername, rhPassword, mfa)

    response = requests.request("POST", url, headers=headers, data = payload)

    newBearer = "Bearer " + (response.json())["access_token"]
    newRefresh = (response.json())["refresh_token"]
    f = open("rhtoken", "w")
    f.write(newBearer)
    f.write('\n')
    f.write(newRefresh)
    f.close()
    return newBearer

def genMfa():
    payload = "{\"grant_type\":\"password\",\"scope\":\"internal\",\"client_id\":\"c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS\",\"expires_in\":86400,\"device_token\":\"4dfc5356-bd56-41c2-85a6-f1da6c499200\",\"username\":\"%s\",\"password\":\"%s\"}" % (rhUsername, rhPassword)

    response = requests.request("POST", url, headers=headers, data=payload)
    print("gen mfa...." + response.text)

def refreshToken():
    # check if token exists
    if path.exists("rhtoken"):
        f = open("rhtoken", "r")
        oldBearer = f.readline()
        oldRefresh = f.readline()
        f.close()

        payload = "{\"grant_type\":\"refresh_token\",\"scope\":\"internal\",\"client_id\":\"c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS\",\"expires_in\":86400,\"device_token\":\"4dfc5356-bd56-41c2-85a6-f1da6c499200\",\"username\":\"%s\",\"password\":\"%s\", \"refresh_token\":\"%s\"}" % (rhUsername, rhPassword, oldRefresh)

        response = requests.request("POST", url, headers=headers, data=payload)

        newBearer = "Bearer " + (response.json())["access_token"]
        newRefresh = (response.json())["refresh_token"]

        f = open("rhtoken", "w")
        f.write(newBearer)
        f.write('\n')
        f.write(newRefresh)
        f.close()

        return str(newBearer)
    else:
        # bad 2fa method to gen inital token
        oldMfa = gmail.main()
        print('old mfa', oldMfa)
        genMfa()
        time.sleep(5)
        newMfa = gmail.main()
        while (newMfa == oldMfa):
            newMfa = gmail.main()
        print('new mfa', newMfa)
        newBearer = genToken(newMfa)
        return str(newBearer)


