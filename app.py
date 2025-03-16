from PIL import Image
from pyzbar.pyzbar import decode
import requests
import re
import urllib.parse


# Headers for ajax
headers = {
    # ":authority": "suf.purs.gov.rs",
    # ":method": "POST",
    # ":path": "/specifications",
    # ":scheme": "https",

    "Host": "suf.purs.gov.rs",

    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6,zh-CN;q=0.5,zh;q=0.4",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    #  "cookie": "localization=sr-Cyrl-RS; .AspNetCore.Antiforgery.vSsOd73lLiA=CfDJ8EPX0z4NPwxHqyQ1MG4fX5f2A-7O1brdde-OUuGozo3jhyaj-jCvGOqEQTvBoufHtSysGVDivs1Lqn9-ubjEjIyO87So5zRhUMaj9jZEQO-XqyVT2im7oZd6rFRCuFG7Dp0PSSmqp_wUVTivf9U0Ulw",
    "origin": "https://suf.purs.gov.rs",
    "priority": "u=1, i",
    # "referer": "https://suf.purs.gov.rs/v/?vl=A1ZCMlJGV0VQVkIyUkZXRVAVBQAADwUAAMwHbAEAAAAAAAABlWJSAJ0AAAB8yx5fzCY1YwutXvoxW5VyKOXBtO1cps4ozG5KPpfmM0kBqGZX6NcVhzMiT4nrRdzN24nHC9ZHKZ%2BgJF3lFSyMllRJh37z4xmgB1bXOOqbFiF2goBc0czwPVUwOeddrCzqGcWPczburEPgwAFK6vdjpSPsyoVurCbep%2F0MK1K0giDfHolNNEA6SJ9oAIbz3Dt3t1YF2PFIl8EGtjQJoRT4v%2B4B82zFinQ%2Bqub8XA7HDtr%2BXLZqBbVzrKk7SkOcBl%2FBMmr7%2BOEkHSRH7bk%2FXthIyKgpAMvttn9FmkwWA6fGkiLTuTnG%2F1Ww71B7eugzh1xNafO7Q54CFO1eDNKcfqB7eY%2B2SZVv6mBMroJpRTnI5iUIBayebeTq3KUeQ3FTJ%2FYy9Ovp8eEjh7QEY9VtuiOdIcDcnE98TSyPWVTc%2FlKt6juvF9oVhYneTt5JmRQnsfTtmNNooOvrfW3M8WZmMn1mcVRvXk%2FC3qD1bWBOadDa1F%2F2KafTNvRLsBjxh%2BAoDWGzyzHXlPLt55vfHiXK9jFxK6DySkTO%2BqGR080nhG8aJp1jEMNN6YZuFaq8MEid36j3bv0z8uybpPaXQviTtHAqgEqtQ9zbqQc2d7hPBCGGt7ashWMJz4bHkLvDiGCnIph5s5ylu66QFHWUPhdBqhj1e%2BSmqotQfbZuSSbjpUIEqGO4Cc%2BMpyAL%2FZ%2BVzIbMEkU%3D",

    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",

    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",

}


def get_url_from_qr(filepath):
    if filepath is None:
        return None
    try:
        data = decode(Image.open('test-data/photo_2025-03-08_10-46-15.jpg'))
        return data[0].data.decode("utf-8")
    finally:
        pass
    return None


def get_config_data(url):
    if url is None:
        return None
    r = requests.get(url)
    if r.status_code != 200:
        return None
    print(f"Request {url}\nHeaders:\n{r.request.headers}\n\n")
    data = {}

    matches = re.findall(r"viewModel\.InvoiceNumber\('([^']+)'\);[\s\n\r\t]*viewModel\.Token\('([^']+)'\)", r.text)
    if len(matches) > 0:
        data['invoice'], data['token'] = matches[0]

    matches = re.findall("rootPath = '([^']+)';", r.text)
    if len(matches) > 0:
        data['rootPath'] = matches[0]

    return data


def load_data_from_link(url):
    config = get_config_data(url)
    if config is None:
        return None

    print(f"Config: {config}\n")

    new_url = urllib.parse.urljoin(config['rootPath'], '/specifications')
    new_headers = dict(headers)
    new_headers['referer'] = url
    new_body = f"invoiceNumber={config["invoice"]}&token={config["token"]}"

    r = requests.post(new_url, data=new_body, headers=new_headers)

    data = r.json()
    if data["success"]:
        return data["items"]

    return None


def main():
    print('Hi VSauce! Michael here')

    url = get_url_from_qr('test-data/photo_2025-03-08_10-46-15.jpg')
    items = load_data_from_link(url)
    if items is None:
        print('No data founded')
        return
    for item in items:
        print(item)


if __name__ == "__main__":
    main()
