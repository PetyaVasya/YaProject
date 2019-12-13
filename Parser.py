from threading import Thread

import requests
from requests.exceptions import ProxyError, ConnectionError, RetryError
from bs4 import BeautifulSoup
import re


class Parser:
    """
        Proxie:
        After 21:00
    """
    ERRORS = ["ConnectionError", "MaxRetryError", "GeneralProxyError", "UrlError"]

    def __init__(self, proxies=[]):
        self.proxies = {proxie: 0 for proxie in proxies}

    def get_get(self, url, headers=None, proxies=None):
        try:
            r = requests.get(url, headers=headers, proxies=proxies)
        except ConnectionError as e:
            return "ConnectionError"
        except RetryError:
            return "MaxRetryError"
        except ProxyError:
            return "GeneralProxyError"
        except Exception as e:
            print(e)
            return ""
        print("I'm all")
        return r

    def get_html(self, url):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
                          " like Gecko) Chrome/74.0.3729.157 Safari/537.36"
        }
        while True:
            proxie = None
            proxies = {}
            if self.proxies:
                proxie = min(self.proxies.items(), key=lambda x: x[1])[0]
                proxies['https'] = proxie
                proxies['http'] = proxie
                self.proxies[proxie] += 1
                print(proxie)
            thread = ThreadWithReturnValue(target=self.get_get, args=(url, headers, proxies))
            thread.daemon = True
            thread.start()
            r = thread.join(10)
            break
        if r and r not in self.ERRORS:
            return r.text
        return r

    def get_field(self, html, field, multiple=False):
        print(multiple)
        soup = BeautifulSoup(html, "lxml")
        if field[1] == "Text":
            if multiple:
                select = soup.select(field[0])
                if select:
                    return [i.get_text(separator="\n", strip=True) for i in select]
                else:
                    return ["None"]
            else:
                select = soup.select_one(field[0])
                if select:
                    return [select.get_text(separator="\n", strip=True)]
                else:
                    return ["None"]
        else:
            if multiple:
                select = soup.select(re.sub("\[" + field[1] + "='.*?'\]", "", field[0]))
                if select:
                    return [i[field[1]] for i in select]
                else:
                    return ["None"]
            else:
                select = soup.select_one(re.sub("\[" + field[1] + "='.*?'\]", "", field[0]))
                if select:
                    return [select[field[1]]]
                else:
                    return ["None"]

    def parse_url(self, url, fields):
        html = self.get_html(url)
        if html == "Timeout" or html in self.ERRORS:
            return [html]
        elif not html:
            return ["UrlError"]
        return [self.get_field(html, field, field[2]) for field in fields]

    def parse_urls(self, links, fields):
        if fields[2]:
            return zip(*[self.parse_url(url, fields) for url in links])
        else:
            return [self.parse_url(url, fields) for url in links]


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args,
                                        **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return
