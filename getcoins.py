import json
import os
import time
from hashlib import sha256

import requests
from dateutil import parser
from dotenv import load_dotenv

load_dotenv()

host = "https://www.universal-cdn.com"

hanime_email = os.getenv('hanime_email')
hanime_password = os.getenv('hanime_password')


def getSHA256(to_hash):
    """Get SHA256 hash."""
    m = sha256()
    m.update(to_hash.encode())
    return m.hexdigest()


def getXHeaders():
    """
    These Xheaders were mainly used to authenticate whether the requests were coming from the actual hanime app and not a script like this one.
    The authentication wasn't that secure tho and reverse engineering it wasn't that difficult.
    """
    XClaim = str(int(time.time()))
    XSig = getSHA256(f"9944822{XClaim}8{XClaim}113")
    headers = {"X-Signature-Version": "app2", "X-Claim": XClaim, "X-Signature": XSig}
    return headers


def login(s: requests.Session, email, password):
    """Login into your hanime account."""
    s.headers.update(getXHeaders())
    response = s.post(f"{host}/rapi/v4/sessions",
                      headers={"Content-Type": "application/json;charset=utf-8"},
                      data=f'{{"burger":"{email}","fries":"{password}"}}')

    if '{"errors":["Unauthorized"]}' in response.text:
        raise SystemExit("[!!!] Login failed, please check your credentials.")

    return getInfo(response.text)


def getInfo(response):
    """Parse out only relevant info."""
    received = json.loads(response)

    ret = {
        "session_token": received["session_token"],
        "uid": received["user"]["id"],
        "name": received["user"]["name"],
        "coins": received["user"]["coins"],
        "last_clicked": received["user"]["last_rewarded_ad_clicked_at"]
    }

    available_keys = list(received["env"]["mobile_apps"].keys())

    if "_build_number" in available_keys:
        ret["version"] = received["env"]["mobile_apps"]["_build_number"]
    elif "osts_build_number" in available_keys:
        ret["version"] = received["env"]["mobile_apps"]["osts_build_number"]
    elif "severilous_build_number" in available_keys:
        ret["version"] = received["env"]["mobile_apps"]["severilous_build_number"]
    else:
        raise SystemExit("[!!!] Unable to find the build number for the latest mobile app, please report an issue on github.")

    return ret


def getCoins(s: requests.Session, version, uid):
    """
    Send a request to claim your coins, this request is forged and we are not actually clicking the ad.
    Again, reverse engineering the mechanism of generating the reward token wasn't much obfuscated.
    """
    s.headers.update(getXHeaders())

    curr_time = str(int(time.time()))
    to_hash = f"coins{version}|{uid}|{curr_time}|coins{version}"

    data = {"reward_token": getSHA256(to_hash) + f"|{curr_time}", "version": f"{version}"}

    response = s.post(f"{host}/rapi/v4/coins", data=data)

    if '{"errors":["Unauthorized"]}' in response.text:
        raise SystemExit("[!!!] Something went wrong, please report issue on github")
    print(f"You received {json.loads(response.text)['rewarded_amount']} coins.")


def main():
    s = requests.Session()

    info = login(s, hanime_email, hanime_password)

    s.headers.update({"X-Session-Token": info["session_token"]})

    print(f"[*] Logged in as {info['name']}")
    print(f"[*] Coins count: {info['coins']}")

    if info['last_clicked'] is not None:
        print(f"[*] Last clicked on {parser.parse(info['last_clicked']).ctime()} UTC")

        previous_time = parser.parse(info["last_clicked"]).timestamp()
        if time.time() - previous_time < 3 * 3600:
            raise SystemExit("[!!!] You've already clicked on an ad less than 3 hrs ago.")
    else:
        print(f"[*] Never clicked on an ad")

    getCoins(s, info["version"], info["uid"])


if __name__ == "__main__":
    main()
