import requests


search_name = 'Ацетилсалициловая кислота'
package = 'таблетки, покрытые пленочной оболочкой, 20 мг, 14 шт. - блистер (2)  - пачка картонная'
producer = 'Вл.Общество с ограниченной ответственностью "ПФКО-1", Россия (5404070404); Вып.к.Перв.Уп.Втор.Уп.Пр.Акционерное общество "Производственная фармацевтическая компания Обновление" (АО "ПФК Обновление"), Россия (5408151534); '

def get_json(search_name):
    url = f'https://jnvlpcalc.spbeias.ru/api/JNVLP/GetFilteredData?chunkName={search_name}&chunkPackage=&chunkProducer='
    r = requests.get(url)
    data = r.json()
    return data

def get_package(data, producer):
    result = []
    for element in data:
        if element['producer'] == producer:
            result.append(element['package'])
    return result

def get_producer(data):
    result = []
    for element in data:
        result.append(element['producer'])
    return result

# print(get_json(search_name))
data = get_json(search_name)
# print(get_producer(data))
print(get_package(data, producer))