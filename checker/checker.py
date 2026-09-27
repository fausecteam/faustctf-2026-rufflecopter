#!/usr/bin/env python3

from ctf_gameserver import checkerlib

import utils
import requests
import logging
from bs4 import BeautifulSoup
import random

# logging.getLogger().setLevel(logging.DEBUG)

class TemplateChecker(checkerlib.BaseChecker):

    def place_flag(self, tick):
        flag = checkerlib.get_flag(tick)
        
        session = requests.session()
        username = utils.rand_string_letters_numbers(random.randint(6,25))
        password = utils.rand_string_letters_numbers(random.randint(8,25))
        name = (utils.rand_string_letters(random.randint(6,25)),
                utils.rand_string_letters(random.randint(6,25)))
        
        try:
            utils.do_register(self, session, username, password)
            utils.do_login(self, session, username, password)
            utils.do_rent(self, session, name[0], name[1], utils.rand_date(), utils.rand_date(), utils.rand_flag_comment(flag))
        except ValueError as e:
            logging.error(F"Could not place flag: {type(e).__name__}: {e}")
            return checkerlib.CheckResult.FAULTY
        
        checkerlib.store_state(f"flag{tick}Account", {"username": username, "password": password})
        checkerlib.set_flagid(session.cookies.get_dict()["rufflecopter_user"])
        
        return checkerlib.CheckResult.OK
    
    def check_out_of_fuel(self):
        logging.info("Checking out-of-fuel page")
        session = requests.session()
        try:
            nonexistent_page = utils.get_nonexistent(self, session)
            if "out of fuel" in nonexistent_page.lower():
                return checkerlib.CheckResult.OK
            else:
                logging.error(F"Wrong out-of-fuel page: {nonexistent_page}")
        except ValueError as e:
            logging.error(F"Could not check out-of-fuel page: {type(e).__name__}: {e}")
        
        return checkerlib.CheckResult.FAULTY
    
    def check_garage(self):
        logging.info("Checking garage page")
        session = requests.session()
        try:
            garage_page = utils.get_garage(self, session)
            if all( s in garage_page for s in ["Gerald the plane", "Roflcopter", "Paper plane", "Lenny the rocket"]):
                return checkerlib.CheckResult.OK
            else:
                logging.error(F"Wrong garage page: {garage_page}")
        except ValueError as e:
            logging.error(F"Could not check garage page: {type(e).__name__}: {e}")
        
        return checkerlib.CheckResult.FAULTY
    
    def check_rent(self):
        logging.info("Checking rents/receipts")
        session = requests.session()
        username = utils.rand_string_letters_numbers(random.randint(6,25))
        password = utils.rand_string_letters_numbers(random.randint(8,25))
        
        rents = [
            {
                "name": [ utils.rand_string_letters(random.randint(6,25)).encode() for i in range(2) ],
                "duration": [ utils.rand_date() for i in range(2) ],
                "comment": utils.generate_message()[:105]
            } for _ in range(random.randint(1,3))
        ]
        
        try:
            utils.do_register(self, session, username, password)
            utils.do_login(self, session, username, password)
            for rent in rents:
                utils.do_rent(self, session, rent["name"][0], rent["name"][1], rent["duration"][0], rent["duration"][1], rent["comment"])
        except ValueError as e:
            logging.error(F"Could not place checker rents: {type(e).__name__}: {e}")
            return checkerlib.CheckResult.FAULTY
        
        try:
            receipts_html = utils.fetch_receipts(self, session)
            soup = BeautifulSoup(receipts_html, 'html.parser')
        except ValueError as e:
            logging.error(F"Could not check checker receipts: {type(e).__name__}: {e}")
            return checkerlib.CheckResult.FAULTY
        
        parsed_rents = []
        for card in soup.find_all(class_="card"):
            try:
                parsed_rents.append(
                    {
                        "name": card.find(class_="card-title").contents[0].encode().split(b", "),
                        "duration": card.find(class_="card-subtitle").contents[0].replace("From ", "").replace("T00:00:00", "").encode().split(b" to "),
                        "receiptcode": utils.read_receipt_img_soup(card.find(id="receiptcode"))
                    }
                )
            except Exception as e:
                logging.warning(F"Could not parse receipt card: {type(e).__name__}: {e}")
        
        for rent in rents:
            rent_found = False
            for parsed in parsed_rents:
                try:
                    if (
                        all(n in parsed["receiptcode"][0] for n in rent["name"]) and
                        all(d.isoformat().encode() in parsed["receiptcode"][1] for d in rent["duration"]) and
                        rent["comment"].decode("latin1").encode() in parsed["receiptcode"][2]
                    ):
                        rent_found = True
                        break
                except Exception as e:
                    logging.warning(F"Could not check parsed rent {parsed} against {rent}")
            if not rent_found:
                logging.error(F"Could not find checker rent {rent} in {parsed_rents}")
                return checkerlib.CheckResult.FAULTY
        
        return checkerlib.CheckResult.OK
    
    def check_logout(self):
        logging.info("Checking login/out")
        session = requests.session()
        
        username = utils.rand_string_letters_numbers(random.randint(6,25))
        password = utils.rand_string_letters_numbers(random.randint(8,25))

        try:
            utils.do_register(self, session, username, password)
            utils.do_login(self, session, username, password)
            utils.fetch_receipts(self, session)
        except ValueError as e:
            logging.error(F"Could not create account and view receipts: {type(e).__name__}: {e}")
            return checkerlib.CheckResult.FAULTY
        
        try:
            utils.do_logout(self, session)
        except ValueError as e:
            logging.error(F"Could not log out: {type(e).__name__}: {e}")
            return checkerlib.CheckResult.FAULTY
        
        try:
            utils.fetch_receipts(self, session)
            logging.error(F"Logout did not work")
            return checkerlib.CheckResult.FAULTY
        except ValueError as e:
            pass

        return checkerlib.CheckResult.OK

    def check_service(self):
        checks = [ self.check_out_of_fuel, self.check_garage, self.check_rent, self.check_logout ]
        random.shuffle(checks)

        for check in checks:
            result = check()
            if result != checkerlib.CheckResult.OK:
                return result
        
        return checkerlib.CheckResult.OK

    def check_flag(self, tick):
        session = requests.session()
        account = checkerlib.load_state(f"flag{tick}Account")
        if not account:
            return checkerlib.CheckResult.FLAG_NOT_FOUND
        
        try:
            utils.do_login(self, session, account["username"], account["password"])
        except ValueError as e:
            logging.error(F"Could not log in to check flag: {type(e).__name__}: {e}")
            return checkerlib.CheckResult.FLAG_NOT_FOUND
        
        try:
            receipts_html = utils.fetch_receipts(self, session)
            soup = BeautifulSoup(receipts_html, 'html.parser')
        except ValueError as e:
            logging.error(F"Could not view receipts: {type(e).__name__}: {e}")
            return checkerlib.CheckResult.FLAG_NOT_FOUND

        flag = checkerlib.get_flag(tick)
        
        for entry in soup.find_all(id="receiptcode"):
            try:
                receipt_data = utils.read_receipt_img_soup(entry)
                if flag.encode() in receipt_data[2]:
                    return checkerlib.CheckResult.OK
            except Exception as e:
                logging.warning(F"Could not check receipt code for flag: {type(e).__name__}: {e}")
        
        return checkerlib.CheckResult.FLAG_NOT_FOUND


if __name__ == '__main__':

    checkerlib.run_check(TemplateChecker)
