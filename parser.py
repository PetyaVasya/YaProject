import requests
from requests.exceptions import ProxyError
from bs4 import BeautifulSoup
import re


class Parser:
    """
        Proxie:
        After 21:00
    """

    def __init__(self, proxies=[]):
        self.proxies = {proxie: 0 for proxie in proxies}

    def get_html(self, url):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
                          " like Gecko) Chrome/74.0.3729.157 Safari/537.36"
        }
        while True:
            try:
                # print(1)
                proxies = {}
                if self.proxies:
                    proxie = min(self.proxies.items(), key=lambda x: x[1])[0]
                    proxies['https'] = proxie
                    proxies['http'] = proxie
                    self.proxies[proxie] += 1
                r = requests.get(url, headers=headers)  # , proxies=proxies)
                break
            except ProxyError as e:
                del self.proxies[proxie]
        return r.text

    def get_field(self, html, field):
        soup = BeautifulSoup(html, "lxml")
        if field[1] == "Text":
            select = soup.select_one(field[0])
            if select:
                return select.getText()
            else:
                return "None"
        else:
            select = soup.select_one(re.sub("\[" + field[1] + "='.*?'\]", "", field[0]))
            if select:
                return select[field[1]]
            else:
                return "None"

    def parse_url(self, url, fields):
        return [self.get_field(self.get_html(url), field) for field in fields]

    def parse_urls(self, links, fields):
        return [self.parse_url(self.get_html(url), fields) for url in links]
