import requests
from bs4 import BeautifulSoup


url = 'https://grls.rosminzdrav.ru/PriceLims.aspx?Torg=квамател&Mnn=&RegNum=&Mnf=&Barcode=&Order=&OuterState=60&PageSize=8&orderby=pklimprice&orderType=desc&pagenum=1'
r = requests.get(url)
soup = BeautifulSoup(r.text, 'lxml')
# soup.find('div', class_='block-row product')
title = soup
print(title)