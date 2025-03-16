from PIL import Image
from pyzbar.pyzbar import decode
import requests
import re
import urllib.parse


header = r".*Артикли[\n\r]+=+[\n\r]+[^\n\r]+[\n\r]+"
body = r"(?:([^\r\n]+)[\r\n]+([^\r\n]+)[\r\n]+)+"

# Example:
"""
Касир:                           teodora
ЕСИР број:                      253/49.0
-------------ПРОМЕТ ПРОДАЈА-------------
Артикли
========================================
Назив   Цена         Кол.         Укупно
Krastavac dugi komad/KOM (Е)            
        99,99          1           99,99
Kinder Bueno 43g/KOM (Ђ)                
       109,99          1          109,99
Pasteta kokosija Argeta 95g/KOM (Ђ)     
       129,99          2          259,98
Paradajz ceri 250g/KOM (Е)              
       149,99          1          149,99
Prot.nap.cok.banana 0,5l PCT/KOM (Е)    
       249,99          2          499,98
Coko Smoki 150g/KOM (Ђ)                 
       299,99          1          299,99
Zlatiborac dimljeni vrat 125g/KOM (Ђ)   
       329,99          1          329,99
Kinder Bueno T5 107.5g/KOM (Ђ)          
       244,99          1          244,99
Min. voda NG Rosa pet 6l/KOM (Ђ)        
       248,99          1          248,99
Krompir beli opran/KG (Е)               
       119,99      1,032          123,83
Kesa tregerica Maxi/KOM (Ђ)             
        17,99          1           17,99
----------------------------------------
Укупан износ:                   2.385,71
Готовина:                       2.400,00
========================================
Ознака       Име      Стопа        Порез
Е           П-ПДВ   10,00%         79,44
Ђ           О-ПДВ   20,00%        251,99
----------------------------------------
Укупан износ пореза:              331,43
========================================
ПФР време:          04.03.2025. 19:01:36
ПФР број рачуна:  VB2RFWEP-VB2RFWEP-1301
Бројач рачуна:               1295/1301ПП
========================================
"""


def get_url_from_qr(filepath):
    if filepath is None:
        return None
    try:
        data = decode(Image.open('TestImages/photo_2025-03-08_10-46-15.jpg'))
        return data[0].data.decode("utf-8")
    finally:
        pass
    return None


def load_data_from_link(url):
    if url is None:
        return None
    r = requests.get(url)
    if r.status_code != 200:
        return None

    m = re.match(header, r.text)
    for group in m.groups():
        print(group)

    return None


def main():
    print('Hi VSauce! Michael here')

    url = get_url_from_qr('TestImages/photo_2025-03-08_10-46-15.jpg')
    data = load_data_from_link(url)

    print(data)


if __name__ == "__main__":
    main()
