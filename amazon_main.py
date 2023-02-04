import requests
from bs4 import BeautifulSoup
from colored import fg, attr
import threading
import queue
from fake_useragent import UserAgent
from twilio import send_email
import re
import json


def get_product_url(amazon_product_code_list):
    list_of_amazon_urls = ['https://www.amazon.de', 'https://www.amazon.fr', 'https://www.amazon.es', 'https://www.amazon.it']
    # cross check the product code with the amazon urls
    product_urls_list = [f'{url}/dp/{code}' for url in list_of_amazon_urls for code in amazon_product_code_list]
    return product_urls_list


def get_product_price(defined_queue, url):
    fake_user_agent = UserAgent()
    user_agent = fake_user_agent.random
    headers = {"User-Agent": user_agent} 
    page = requests.get(url, headers=headers)
    soup  = BeautifulSoup(page.text, 'html.parser')
    try:
        product_title = soup.find('span', id='productTitle').getText().strip()
        product_price = soup.find('span', class_ = "a-offscreen").getText().strip()
        # to get only Google Pixel 7 Pro for example and not Google Pixel 7 Pro - 128GB and so on
        # split by – or - and get the first element
        get_first_product_title = re.split(r'[-–|:]', product_title)[0].strip()
        product_price_int = float(product_price.replace('€', '').replace(',', '.'))
        # put the result in the queue
        defined_queue.put([get_first_product_title, product_price_int, url])
    except Exception as e:
        print(f'URL: {url} error: {e}')


def email_body_html_formating(input_list_of_items):
    # Create the HTML table
    table = '<table>\n'
    for item in input_list_of_items:
        product_name = item[0]
        product_price = round(item[1], 1)
        product_url = item[2]
        table += f'  <tr><td>{product_name}</td><td>{product_price}</td><td><a href="{product_url}">Link</a></td></tr>\n'
    table += '</table>\n'

    # Create the body of the email using string formatting
    email_body_html = f"""<p>Here is the list you requested:</p>{table}"""
    return email_body_html


if __name__ == '__main__':

    target_price = 800

    #amazon_product_code_list = ['B0BDK2CZ8N', 'B0BDJ3ND5X', 'B0BDJ55SSD'] # Pixel 7 Pro
    #amazon_product_code_list = ['B0BDJG3TWP', 'B0BDK63RF3', 'B0BDJFKY7B'] # Pixel 7
    amazon_product_code_list = ['B08C7KG5LP', 'B091CQH6VT', 'B08C7KCJF5'] # Sony WH-1000XM4
    # Create a queue to hold the results
    result_queue = queue.Queue()
    amazon_final_urls_list = get_product_url(amazon_product_code_list)

    # Create a list to hold the threads we are going to create. Needed for later joining as to wait for all the threads to complete
    threads = []
    for url in amazon_final_urls_list:
        thread = threading.Thread(target=get_product_price, args=(result_queue, url,))
        thread.start()
        threads.append(thread)

    # Wait for all the threads to complete
    for thread in threads:
        thread.join()
    
    # sort queue by price to list
    sorted_queue = sorted(result_queue.queue, key=lambda x: x[1])
    print(f"{fg('blue')}{attr('bold')}Sorted Queue contents of all the results for price target of {target_price}:{attr('reset')} \n")
    for item in sorted_queue:
        product_name = item[0]
        product_price = round(item[1], 1)
        product_url = item[2]
        print(f"{fg('green_1')}The Product Name is:{attr('reset')}{fg('dark_slate_gray_2')} {product_name}{attr('reset')} {fg('green_1')}The Price is:{attr('reset')}{fg('orange_red_1')} {product_price}{attr('reset')} {fg('green_1')} URL: {fg('yellow')}{product_url} {attr('reset')} ")
        
        # create a list with the items that are below the target price and will be sent by email
        send_email_items_list = [item for item in sorted_queue if item[1] <= target_price]

    # make result list to html tables
    email_body_result = email_body_html_formating(send_email_items_list)

    if len(send_email_items_list) > 0:
    # get min price from the list for the email subject
        min_priced_product = min(send_email_items_list, key=lambda x: x[1])
    else:
        min_priced_product = ['No items below target price', 0]

    
    want_email = False

    if want_email and len(send_email_items_list) > 0:
        send_email(sent_from='ignarvalme@gmail.com',
                   sent_to='ignarvalme@gmail.com',
                   sent_subject=f'Amazon Price Alert: {min_priced_product[0]} with price {min_priced_product[1]}',
                   sent_body=email_body_result)

