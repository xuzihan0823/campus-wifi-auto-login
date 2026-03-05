import os
import time
import subprocess
import requests

CHECK_INTERVAL = int(os.environ.get("CAMPUS_CHECK_INTERVAL", "30"))

def is_online():
    try:
        r = requests.get("http://www.baidu.com", timeout=3, allow_redirects=False)
        return r.status_code == 200
    except:
        return False

def run_login():
    subprocess.call(["python", "login.py"])

def main():

    if not is_online():
        run_login()

    while True:
        time.sleep(CHECK_INTERVAL)

        if not is_online():
            run_login()

if __name__ == "__main__":
    main()