import requests
from bs4 import BeautifulSoup


class Parser:

    def get_html(self, url):
        r = requests.get(url)
        return r.text

    def get_field(self, html):
        soup = BeautifulSoup(html, "lxml")
        print(soup.select("li.b-menu__item.menu-item-3"))


p = Parser()
html = p.get_html("https://www.avito.ru/novosibirsk/noutbuki/asus_k50ij_1824819749")
# p.get_field(html)
print(html)
