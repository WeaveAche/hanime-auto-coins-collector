from contextlib import suppress
import os
import time
from hashlib import sha256
import requests
from dateutil import parser
from dotenv import load_dotenv

load_dotenv()

HOST = "https://www.universal-cdn.com"
HANIME_EMAIL = os.getenv("hanime_email")
HANIME_PASSWORD = os.getenv("hanime_password")


def getSHA256(to_hash) -> str:
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
    return {"X-Signature-Version": "app2", "X-Claim": XClaim, "X-Signature": XSig}


def get_info(response_json: list[dict] | dict):
    """Parse out only relevant info."""

    ret = {
        "session_token": response_json["session_token"],
        "uid": response_json["user"]["id"],
        "name": response_json["user"]["name"],
        "coins": response_json["user"]["coins"],
        "last_clicked": response_json["user"]["last_rewarded_ad_clicked_at"],
    }

    available_keys = list(response_json["env"]["mobile_apps"].keys())

    if "_build_number" in available_keys:
        ret["version"] = response_json["env"]["mobile_apps"]["_build_number"]
    elif "osts_build_number" in available_keys:
        ret["version"] = response_json["env"]["mobile_apps"]["osts_build_number"]
    elif "severilous_build_number" in available_keys:
        ret["version"] = response_json["env"]["mobile_apps"]["severilous_build_number"]
    else:
        print(
            "[!!!] Unable to find the build number for the latest mobile app, please report an issue on github."
        )

    return ret


def login(session: requests.Session, email: str, password: str) -> dict:
    """Login into your hanime account."""
    session.headers.update(getXHeaders())
    response = session.post(
        f"{HOST}/rapi/v4/sessions",
        headers={"Content-Type": "application/json;charset=utf-8"},
        data=f'{{"burger":"{email}","fries":"{password}"}}',
    )
    if '{"errors":["Unauthorized"]}' in response.text:
        print("[!!!] Login failed, please check your credentials.")

    return get_info(response.json())


def get_coins(session: requests.Session, version: str, uid: str) -> None:
    """
    Send a request to claim your coins, this request is forged and we are not actually clicking the ad.
    Again, reverse engineering the mechanism of generating the reward token wasn't much obfuscated.
    """
    session.headers.update(getXHeaders())

    current_time = str(int(time.time()))
    to_hash = f"coins{version}|{uid}|{current_time}|coins{version}"

    data = {
        "reward_token": f"{getSHA256(to_hash)}|{current_time}",
        "version": f"{version}",
    }

    response = session.post(f"{HOST}/rapi/v4/coins", data=data)

    if '{"errors":["Unauthorized"]}' not in response.text:
        print(f"You received {response.json()['rewarded_amount']} coins.")


def main():
    session = requests.Session()

    info = login(session, HANIME_EMAIL, HANIME_PASSWORD)

    session.headers.update({"X-Session-Token": info["session_token"]})

    print(f"[*] Logged in as {info['name']}")
    print(f"[*] Coins count: {info['coins']}")

    if info["last_clicked"] is not None:
        print(f"[*] Last clicked on {parser.parse(info['last_clicked']).ctime()} UTC")

        previous_time = parser.parse(info["last_clicked"]).timestamp()
        if time.time() - previous_time < 3 * 3600:
            print("[!!!] You've already clicked on an ad less than 3 hrs ago.")
    else:
        print("[*] Never clicked on an ad")
        get_coins(session, info["version"], info["uid"])


class Generator:
    def __init__(
        self, interval: float = 1 * 60 * 60, exception_handling: bool = True
    ) -> None:
        self.interval = interval
        self.exception_handling = exception_handling

    def run(self) -> None:
        while True:
            if not self.exception_handling:
                main()
            else:
                with suppress(Exception):
                    main()

            print(f"sleeping for {self.interval} seconds")
            time.sleep(self.interval)
