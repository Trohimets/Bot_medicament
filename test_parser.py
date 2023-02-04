import requests


search_name = 'Квамател'
package = 'таблетки, покрытые пленочной оболочкой, 20 мг, 14 шт. - блистер (2)  - пачка картонная'

def get_json(search_name):
    url = f'https://jnvlpcalc.spbeias.ru/api/JNVLP/GetFilteredData?chunkName={search_name}&chunkPackage=&chunkProducer='
    r = requests.get(url)
    data = r.json()
    return data

def get_package(data):
    result = []
    for element in data:
        result.append(element['package'])
    return result

def get_producer(data, package):
    result = []
    i = 1
    for element in data:
        if element['package'] == package:
            result.append(element['producer'])
    print(len(result))

data = get_json(search_name)
get_producer(data, package)