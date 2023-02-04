import requests
from bs4 import BeautifulSoup


search_name = 'Квамател'
url = f'https://jnvlpcalc.spbeias.ru/api/JNVLP/GetFilteredData?chunkName={search_name}&chunkPackage=&chunkProducer='
r = requests.get(url)
data = r.json()
for element in data:
    print(element['producer'], element['package'])