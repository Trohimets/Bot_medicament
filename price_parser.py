import requests



# search_name = 'Ацетилсалициловая кислота'
search_name = 'АЦЦ 200'

package = 'таблетки, покрытые пленочной оболочкой, 20 мг, 14 шт. - блистер (2)  - пачка картонная'
producer = 'Вл.Общество с ограниченной ответственностью "ПФКО-1", Россия (5404070404); Вып.к.Перв.Уп.Втор.Уп.Пр.Акционерное общество "Производственная фармацевтическая компания Обновление" (АО "ПФК Обновление"), Россия (5408151534); '

def get_json(search_name):
    url = f'https://jnvlpcalc.spbeias.ru/api/JNVLP/GetFilteredData?chunkName={search_name}&chunkPackage=&chunkProducer='
    r = requests.get(url)
    try:
        data = r.json()
    except requests.exceptions.JSONDecodeError:
        return 'сервис проверки временно не доступен'
    return data

def get_json_alternative(search_name):
    url = f'https://jnvlpcalc.spbeias.ru/api/JNVLP/GetName?chunkName={search_name}&chunkPackage=&chunkProducer='
    r = requests.get(url)
    try:
        data = r.json()
        del data[10:]
    except requests.exceptions.JSONDecodeError:
        return 'сервис проверки временно не доступен'
    return data

# print(get_json_alternative('инсулин'))

def get_package(data, producer):
    result = []
    for element in data:
        if element['producer'] == producer:
            result.append(element['package'])
    return result

def get_producer(data):
    result = []
    for element in data:
        if element['producer'] not in result:
            result.append(element['producer'])
    return result

def get_price(data, producer, package):
    for medicine in data:
        if medicine['producer'] == producer and medicine['package'] == package:
            result_medicine = medicine
    prices = []
    prices.append(float(result_medicine['finalPriceOsnFromOsn']))
    prices.append(float(result_medicine['finalPriceOsnFromUsn']))
    prices.append(float(result_medicine['finalPriceUsnFromUsn']))
    prices.append(float(result_medicine['finalPriceUsnFromOsn']))
    return max(prices)

# print(get_json(search_name))
# data = get_json(search_name)
# print(data)
# print(get_producer(data))
# print(get_package(data, producer))