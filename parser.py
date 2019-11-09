import requests
from bs4 import BeautifulSoup


class Parser:

    def __init__(self, url_mask, fields):
        self.url_mask = url_mask
        self.fields = fields

    def get_html(self, url):
        r = requests.get(url)
        return r.text

    def get_field(self, html, field):
        soup = BeautifulSoup(html, "lxml")
        print(field)
        if field[1] == "Text":
            return soup.select_one(field[0]).getText()
        else:
            return soup.select_one(field[0])[field[1]]

    def get_fields(self, html):
        return [self.get_field(html, field) for field in self.fields]


# p = Parser("a", [["SPAN[class='title-info-title-text'][itemprop='name']", 'Text'], ["SPAN[class='js-item-price'][content='6500'][itemprop='price']", 'content']])
# html = p.get_html("https://www.avito.ru/novosibirsk/noutbuki/asus_k50ij_1824819749")
# print(p.get_fields(html))
# # print(html)
