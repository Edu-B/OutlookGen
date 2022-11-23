import ctypes
import os
import sys
import time
from contextlib import suppress
from json import load
from random import randint, choice
from typing import Any

import requests
from colorama import Fore
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from tqdm import tqdm
from twocaptcha import TwoCaptcha

import anycaptcha
from Utils import Utils, Timer

# Some Value
eGenerated = 0
solvedCaptcha = 0


class eGen:
    def __init__(self):
        self.Utils = Utils()  # Utils Module
        self.config: Any = load(open('config.json'))  # Config File
        self.checkConfig()  # Check Config File
        self.options = webdriver.ChromeOptions()  # Driver Options
        self.Timer = Timer()  # Timer

        self.driver = None
        self.capabilities = None
        self.first_name = None  # Generate First Name
        self.last_name = None  # Generate Last Name
        self.password = None  # Generate Password
        self.email = None  # Generate Email

        # Values About Captcha
        self.providers = self.config['Captcha']['providers']
        self.api_key = self.config["Captcha"]["api_key"]
        self.site_key = self.config["Captcha"]["site_key"]

        # Other
        self.proxies = [i.strip() for i in open(self.config['Common']['ProxyFile']).readlines()]  # Get Proxies
        for arg in tqdm(self.config["DriverArguments"], desc='Loading Arguments',
                        bar_format='{desc} | {l_bar}{bar:15} | {percentage:3.0f}%'):  # Get Driver Arguments
            self.options.add_argument(arg)  # Add Argument to option
            time.sleep(0.2)

        # More Options
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.options.add_experimental_option('useAutomationExtension', False)

    def solver(self, site_url, browser):
        # Solve Captcha Function
        global solvedCaptcha
        # TwoCaptcha
        if self.providers == 'twocaptcha':
            try:
                return TwoCaptcha(self.api_key).funcaptcha(sitekey=self.site_key, url=site_url)['code']
            except Exception as exp:
                self.print(exp)

            # AnyCaptcha
        elif self.providers == 'anycaptcha':
            client = anycaptcha.AnycaptchaClient(self.api_key)
            task = anycaptcha.FunCaptchaProxylessTask(site_url, self.site_key)
            job = client.createTask(task, typecaptcha="funcaptcha")
            self.print("Solving funcaptcha")
            job.join()
            result = job.get_solution_response()
            if result.find("ERROR") != -1:
                self.print(result)
                browser.quit()
            else:
                solvedCaptcha += 1
                return result

    def check_proxy(self, proxy):
        with suppress(Exception):
            requests.get("https://outlook.live.com", proxies={
                "http": "http://{}".format(proxy),
                "https": "http://{}".format(proxy)
            }, timeout=self.config["ProxyCheckTimeout"])
            return True
        return False

    def fElement(self, driver: WebDriver, by: By = By.ID, value=None, delay: float = 0.3):
        # Custom find Element Function
        count = 0
        while count <= 100:
            try:
                return driver.find_element(by, value)
            except:
                time.sleep(delay)
                count += 1
        self.print(f'tried 100 time to find element...')
        driver.quit()
        return

    def get_balance(self):
        # Check provider Balance Function
        if self.providers == 'twocaptcha':
            return TwoCaptcha(self.api_key).balance()
        elif self.providers == 'anycaptcha':
            return anycaptcha.AnycaptchaClient(self.api_key).getBalance()

    def update(self):
        # Update Title Function
        global eGenerated, solvedCaptcha
        title = f'Email Generated: {eGenerated} | Solved Captcha: {solvedCaptcha} | Balance: {self.get_balance()}'
        ctypes.windll.kernel32.SetConsoleTitleW(title) if os.name == 'nt' else print(f'\33]0;{title}\a', end='',
                                                                                     flush=True)

    def generate_info(self):
        # Generate Information Function
        self.email = self.Utils.eGen()
        self.password = self.Utils.makeString(self.config["EmailInfo"]["PasswordLength"])  # Generate Password
        self.first_name = self.Utils.makeString(self.config["EmailInfo"]["FirstNameLength"])  # Generate First Name
        self.last_name = self.Utils.makeString(self.config["EmailInfo"]["LastNameLength"])  # Generate Last Name

    def checkConfig(self):
        # Check Config Function
        captcha_sec = self.config['Captcha']
        if captcha_sec['api_key'] == "" or captcha_sec['providers'] == "anycaptcha/twocaptcha" or \
                self.config['EmailInfo']['Domain'] == "@hotmail.com/@outlook.com":
            self.print('Please Fix Config!')
            sys.exit()

    def print(self, text: object, end: str = "\n"):
        # Print With Prefix Function
        print(self.Utils.replace(f"{self.config['Common']['Prefix']}&f{text}",
                                 {
                                     '&a': Fore.LIGHTGREEN_EX,
                                     '&4': Fore.RED,
                                     '&2': Fore.GREEN,
                                     '&b': Fore.LIGHTCYAN_EX,
                                     '&c': Fore.LIGHTRED_EX,
                                     '&6': Fore.LIGHTYELLOW_EX,
                                     '&f': Fore.RESET,
                                     '&e': Fore.LIGHTYELLOW_EX,
                                     '&3': Fore.CYAN,
                                     '&1': Fore.BLUE,
                                     '&9': Fore.LIGHTBLUE_EX,
                                     '&5': Fore.MAGENTA,
                                     '&d': Fore.LIGHTMAGENTA_EX,
                                     '&8': Fore.LIGHTBLACK_EX,
                                     '&0': Fore.BLACK}), end=end)

    def CreateEmail(self, driver: WebDriver):
        # Create Email Function
        try:
            global eGenerated, solvedCaptcha
            self.update()
            driver.set_page_load_timeout(5)
            self.Timer.start(time.time()) if self.config["Common"]['Timer'] else ''
            driver.get("https://outlook.live.com/owa/?nlp=1&signup=1")
            assert 'Create' in driver.title
            if self.config['EmailInfo']['Domain'] == "@hotmail.com":
                domain = self.fElement(driver, By.ID, 'LiveDomainBoxList')
                time.sleep(0.1)
                domainObject = Select(domain)
                domainObject.select_by_value('hotmail.com')
            emailInput = self.fElement(driver, By.ID, 'MemberName')
            emailInput.send_keys(self.email)
            self.print(f"email: {self.email}{self.config['EmailInfo']['Domain']}")
            self.fElement(driver, By.ID, 'iSignupAction').click()
            with suppress(Exception):
                self.print(driver.find_element(By.ID, 'MemberNameError').text)
                self.print("email is already taken")
                driver.quit()
                return
            passwordinput = self.fElement(driver, By.ID, 'PasswordInput')
            passwordinput.send_keys(self.password)
            self.print("Password: %s" % self.password)
            self.fElement(driver, By.ID, 'iSignupAction').click()
            first = self.fElement(driver, By.ID, "FirstName")
            first.send_keys(self.first_name)
            last = self.fElement(driver, By.ID, "LastName")
            last.send_keys(self.last_name)
            self.fElement(driver, By.ID, 'iSignupAction').click()
            dropdown = self.fElement(driver, By.ID, "Country")
            dropdown.find_element(By.XPATH, "//option[. = 'Turkey']").click()
            birthMonth = self.fElement(driver, By.ID, "BirthMonth")
            objectMonth = Select(birthMonth)
            objectMonth.select_by_value(str(randint(1, 12)))
            birthMonth = self.fElement(driver, By.ID, "BirthDay")
            objectMonth = Select(birthMonth)
            objectMonth.select_by_value(str(randint(1, 28)))
            birthYear = self.fElement(driver, By.ID, "BirthYear")
            birthYear.send_keys(
                str(randint(self.config['EmailInfo']['minBirthDate'], self.config['EmailInfo']['maxBirthDate'])))
            self.fElement(driver, By.ID, 'iSignupAction').click()
            driver.switch_to.frame(self.fElement(driver, By.ID, 'enforcementFrame'))
            token = self.solver(driver.current_url, self.driver)
            time.sleep(0.5)
            driver.execute_script(
                'parent.postMessage(JSON.stringify({eventId:"challenge-complete",payload:{sessionToken:"' + token + '"}}),"*")')
            self.print("&aCaptcha Solved")
            self.update()
            self.fElement(driver, By.ID, 'idBtn_Back').click()
            self.print(f'Email Created in {str(self.Timer.timer(time.time())).split(".")[0]}s') if \
                self.config["Common"]['Timer'] else self.print('Email Created')
            eGenerated += 1
            self.Utils.logger(self.email + self.config['EmailInfo']['Domain'], self.password)
            self.update()
            driver.quit()
        except Exception as e:
            if e == KeyboardInterrupt:
                driver.quit()
                sys.exit(0)
            self.print("&4Something is wrong | %s" % str(e).split("\n")[0].strip())
        finally:
            driver.quit()

    def run(self):
        # Run Script Function
        self.print('&bCoded with &c<3&b by MatrixTeam')
        while True:
            self.generate_info()
            proxy = choice(self.proxies)  # Select Proxy
            if not self.check_proxy(proxy):
                self.print("&c%s &f| &4Invalid Proxy&f" % proxy)
                self.proxies.remove(proxy)
                continue
            self.print(proxy)
            self.options.add_argument("--proxy-server=http://%s" % proxy)
            self.CreateEmail(driver=webdriver.Chrome(options=self.options, desired_capabilities=self.capabilities))


if __name__ == '__main__':
    eGen().run()
