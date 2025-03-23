from PIL import Image
from pyzbar.pyzbar import decode
import requests
import re
import urllib.parse

from RreceiptDecoder.AjaxHeaders import headers


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
    print(f"Request {url}\nHeaders:\n{r.request.headers}\n\n")
    data = {
        'url': url
    }

    matches = re.findall(r"viewModel\.InvoiceNumber\('([^']+)'\);[\s\n\r\t]*viewModel\.Token\('([^']+)'\)", r.text)
    if len(matches) > 0:
        data['invoice'], data['token'] = matches[0]

    matches = re.findall("rootPath = '([^']+)';", r.text)
    if len(matches) > 0:
        data['rootPath'] = matches[0]

    return data


def load_data(config):
    new_url = urllib.parse.urljoin(config['rootPath'], '/specifications')
    new_headers = dict(headers)
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
            "items": data["items"],
        }

    return None


def read_receipts(path_to_photo):
    data = []
    urls = get_urls_from_qr(path_to_photo)
    for url in urls:
        config = load_ajax_config(url)
        if config is None:
            return None
        config["file"] = path_to_photo
        data.append(load_data(config))
    return data


def main():
    print('Hi VSauce! Michael here')
    receipts = read_receipts('../test-data/photo_2025-03-08_10-46-15.jpg')
    print(receipts)


if __name__ == "__main__":
    main()
