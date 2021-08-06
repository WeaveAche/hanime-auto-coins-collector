import requests,json,time
from hashlib import sha256
from dateutil import parser

host = "http://www.universal-cdn.com"

# enter your hanime credentials here
with open("credentials.txt","r") as f:
    creds = json.loads(f.read())

hanime_email = creds["hanime_email"]
hanime_password = creds["hanime_password"]

# get SHA256 hash
def getSHA256(to_hash):
    m = sha256()
    m.update(to_hash.encode())
    return m.hexdigest()    

# these Xheaders were mainly used to authenticate whether the requests were coming from the actual hanime app and not a script like this one
# the authentication wasn't that secure tho and reverse engineering it wasn't that difficult
def getXHeaders():
    XClaim = str(int(time.time()))
    XSig = getSHA256(f"9944822{XClaim}8{XClaim}113")
    headers = {"X-Signature-Version": "app2","X-Claim": XClaim,"X-Signature": XSig}
    return headers

# login into your hanime account
def login(s:requests.Session, email,password):
    s.headers.update(getXHeaders())
    response = s.post(f"{host}/rapi/v4/sessions",headers={"Content-Type":"application/json;charset=utf-8"},data=f'{{"burger":"{email}","fries":"{password}"}}')
    
    if '{"errors":["Unauthorized"]}' in response.text:
        print("[!!!] Login failed, please check your credentials.")
        exit()
    else:
        return getInfo(response.text)

# parse out only relevant info
def getInfo(response):
    received = json.loads(response)

    ret = {}

    ret["session_token"] = received["session_token"]
    ret["uid"] = received["user"]["id"]
    ret["name"] = received["user"]["name"]
    ret["coins"] = received["user"]["coins"]
    ret["last_clicked"] = received["user"]["last_rewarded_ad_clicked_at"]


    available_keys = list(received["env"]["mobile_apps"].keys())

    if "osts_build_number" in available_keys:
        ret["version"] = received["env"]["mobile_apps"]["osts_build_number"]
    else:
        ret["version"] = received["env"]["mobile_apps"]["severilous_build_number"]

    return ret

# send a request to claim your coins, this request is forged and we are not actually clicking the ad
# again, reverse engineering the mechanism of generating the reward token wasn't much obfuscated
def getCoins(s:requests.Session,version,uid):
    s.headers.update(getXHeaders())
    
    curr_time = str(int(time.time()))
    to_hash = f"coins{version}|{uid}|{curr_time}|coins{version}"

    data = {"reward_token": getSHA256(to_hash)+f"|{curr_time}" ,"version":"63"}

    response = s.post(f"{host}/rapi/v4/coins",data=data)
    
    if '{"errors":["Unauthorized"]}' in response.text:
        print("[!!!] Something went wrong, please report issue on github")
        exit()
    else:
        print(f"You received {json.loads(response.text)['rewarded_amount']} coins.")
    

def main():

    s = requests.Session()

    info = login(s,hanime_email, hanime_password)

    s.headers.update({"X-Session-Token":info["session_token"]})
    
    print(f"[*] Logged in as {info['name']}")
    print(f"[*] Coins count: {info['coins']}")
    print(f"[*] Last clicked on {parser.parse(info['last_clicked']).ctime()} UTC")

    # check whether if u already received a reward less than 3 hrs ago
    # the check also happens on server side so there is no apparent way to bypass it
    if time.time() - parser.parse(info["last_clicked"]).timestamp() < 3*3600:
        print("[!!!] You've already clicked on an ad less than 3 hrs ago.")
        exit()

    # finally, getCoins
    getCoins(s,info["version"],info["uid"])
    
if __name__ == "__main__":
    main()