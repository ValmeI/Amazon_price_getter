import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import pandas as pd
import json

pd.set_option('display.max_colwidth', None)

apotheka_urls = ['https://www.apotheka.ee/catalogsearch/result/?q=nurofen+suukaudne',
                'https://www.apotheka.ee/catalogsearch/result/?q=ibustar+suukaudne']

sudameapteek_urls = ['https://www.sudameapteek.ee/list/filter/index?q=nenurofen%20suukaudne',
                    'https://www.sudameapteek.ee/list/filter/index?q=ibustar%20suukaudne']


fake_user_agent = UserAgent()
user_agent = fake_user_agent.random
headers = {"User-Agent": user_agent}

def apotheka_info(product_urls):
    print('Apotheka info')
    print('======================')
    try:
        for url in product_urls:
            page = requests.get(url, headers=headers)
            soup = BeautifulSoup(page.text, 'html.parser')
            html_result = soup.find(
                'div', {'data-component': 'productCategoryList'})
            json_raw = json.loads(html_result['data-config'])
            df = pd.json_normalize(json_raw['products'])
            # drop columns
            df.drop(['image.image_url', 'image.width', 'image.height', 'image.label', 'image.ratio',
                    'image.custom_attributes', 'image.class', 'image.product_id'], axis=1, inplace=True)
            print(df)
            #print(df.dtypes)
    except Exception as e:
        print(f'URL: {url} error: {e}')


if __name__ == '__main__':
    #apotheka_info(apotheka_urls)

    url2 = 'https://www.sudameapteek.ee/list/filter/index?q=nenurofen%20suukaudne'
    page = requests.get(url2, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    print(soup.prettify())
