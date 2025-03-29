import re
import requests
import urllib.parse
from datetime import datetime
from PIL import Image
from pyzbar.pyzbar import decode
from RreceiptDecoder.AjaxHeaders import ajax_headers


def get_urls_from_qr(filepath):
    if filepath is None:
        return None
    try:
        data = decode(Image.open(filepath))
        return [item.data.decode("utf-8") for item in data]
    finally:
        pass
    return None


def load_ajax_config(url):
    if url is None:
        return None
    r = requests.get(url)
    if r.status_code != 200:
        return None
    data = {
        'url': url
    }

    matches = re.findall(r"viewModel\.InvoiceNumber\('([^']+)'\);[\s\n\r\t]*viewModel\.Token\('([^']+)'\)", r.text)
    if len(matches) > 0:
        data['invoice'], data['token'] = matches[0]

    matches = re.findall("rootPath = '([^']+)';", r.text)
    if len(matches) > 0:
        data['rootPath'] = matches[0]

    # 23.3.2025. 14:46:44
    # 4.3.2025. 19:01:36
    matches = re.findall(r"(\d{1,2}).(\d{1,2}).(\d{1,4})\. (\d{1,2}):(\d{1,2}):(\d{1,2})", r.text)
    if len(matches) > 0:
        day, month, year, hour, minute, second = [int(e) for e in matches[0]]
        data['datetime'] = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)

    return data


def load_data(config):
    new_url = urllib.parse.urljoin(config['rootPath'], '/specifications')
    new_headers = dict(ajax_headers)
    new_headers['referer'] = config['url']
    new_body = f"invoiceNumber={config["invoice"]}&token={config["token"]}"

    r = requests.post(new_url, data=new_body, headers=new_headers)

    data = r.json()
    if data["success"]:
        return {
            "file": config['file'],
            "url": config['url'],
            "invoice": config['invoice'],
            "token": config['token'],
            "datetime": config['datetime'],
            "items": data["items"],
        }

    return None


def read_receipts_from_image(path_to_photo):
    data = []
    urls = get_urls_from_qr(path_to_photo)
    for url in urls:
        if url.startswith("http://") or url.startswith("https://"):
            config = load_ajax_config(url)
            if config is None:
                return None
            config["file"] = path_to_photo
            data.append(load_data(config))
    return data


def read_receipts_from_urls(*urls):
    data = []
    for url in urls:
        if url.startswith("http://suf.purs.gov.rs") or url.startswith("https://suf.purs.gov.rs"):
            config = load_ajax_config(url)
            if config is None:
                return None
            config["file"] = ''
            data.append(load_data(config))
    return data


def main():
    print('Hi VSauce! Michael here')
    receipts = read_receipts_from_image('../test-data/photo_2025-03-08_10-46-15.jpg')
    print(f"Result 1:\n\n{receipts}\n\n\n\n")
    receipts = read_receipts_from_image('../test-data/m50_file_28.jpg')
    print(f"Result 2:\n\n{receipts}\n\n\n\n")
    receipts = read_receipts_from_image('../test-data/m71_file_31.jpg')
    print(f"Result 3:\n\n{receipts}\n\n\n\n")
    receipts = read_receipts_from_image('../test-data/m82_file_35.jpg')
    print(f"Result 4:\n\n{receipts}\n\n\n\n")
    receipts = read_receipts_from_image('../test-data/m150_file_51.jpg')
    print(f"Result 4:\n\n{receipts}\n\n\n\n")


if __name__ == "__main__":
    main()
