'''This script will get the price of a product from amazon 
and send an email if the price is below the target price'''
import queue
# from twilio import send_email
import re
import threading

from colored import fg, attr
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def get_product_url(product_code_list):
    '''generates a list of amazon urls with the product codes for the different amazon sites'''
    list_of_amazon_urls = ['https://www.amazon.de', 'https://www.amazon.fr',
                           'https://www.amazon.es', 'https://www.amazon.it']
    # cross check the product code with the amazon urls
    product_urls_list = [
        f'{url}/dp/{code}' for url in list_of_amazon_urls for code in product_code_list]
    return product_urls_list


def get_product_price(defined_queue, input_url):
    '''gets the product price from the amazon url'''
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # log_level=0 to disable logging, for example: ====== WebDriver manager ======
        driver = webdriver.Chrome(service=Service(
            ChromeDriverManager(log_level=0).install()), options=options)
        driver.get(input_url)
        product_title = driver.find_element(By.ID, 'productTitle').text
        product_price_whole = driver.find_element(
            By.CLASS_NAME, 'a-price-whole').text
        product_price_fraction = driver.find_element(
            By.CLASS_NAME, 'a-price-fraction').text
        final_product_price = f'{product_price_whole}.{product_price_fraction}'
        # price_list = soup.find('div', class_='a-section aok-hidden twister-plus-buying-options-price-data').getText().strip() # pylint: disable=line-too-long
        # product_price  = json.loads(price_list)[0]['priceAmount']
        # split by character - or – or | or : and get the first element to cut product title shorter
        get_first_product_title = re.split(r'[-–|:]', product_title)[0].strip()
        product_price_int = float(
            final_product_price.replace('€', '').replace(',', '.'))
        # put the result in the queue
        defined_queue.put([get_first_product_title, product_price_int, url])
    except Exception as e:  # pylint: disable=broad-except disable=invalid-name
        print(f'URL: {url} error: {e}')


def email_body_html_formating(input_list_of_items):
    '''creates the html table for the email body'''
    table = '<table>\n'
    for input_item in input_list_of_items:
        item_name = input_item[0]
        item_price = round(input_item[1], 1)
        item_url = input_item[2]
        table += f'<tr><td>{item_name}</td><td>{item_price}</td><td>' \
                 f'<a href="{item_url}">Link</a></td></tr>\n'
    table += '</table>\n'

    # Create the body of the email using string formatting
    email_body_html = f"""<p>Here is the list you requested:</p>{table}"""
    return email_body_html


if __name__ == '__main__':

    TARGET_PRICE = 280

    amazon_product_code_list = ['B0BDK2CZ8N', 'B0BDJ3ND5X', 'B0BDJ55SSD']  # Pixel 7 Pro
    # amazon_product_code_list = ['B0BDJG3TWP', 'B0BDK63RF3', 'B0BDJFKY7B'] # Pixel 7
    # amazon_product_code_list = ['B08C7KG5LP', 'B091CQH6VT', 'B08C7KCJF5']  # Sony WH-1000XM4
    # Create a queue to hold the results
    result_queue = queue.Queue()
    amazon_final_urls_list = get_product_url(amazon_product_code_list)

    # Create a list to hold the threads we are going to create.
    # Needed for later joining as to wait for all the threads to complete
    threads = []
    for url in amazon_final_urls_list:
        thread = threading.Thread(
            target=get_product_price, args=(result_queue, url,))
        thread.start()
        threads.append(thread)

    # Wait for all the threads to complete
    for thread in threads:
        thread.join()

    # sort queue by price to list
    sorted_queue = sorted(result_queue.queue, key=lambda x: x[1])
    print(f"{fg('blue')}{attr('bold')}Sorted Queue contents of all "
          f"the results for price target of {TARGET_PRICE}:{attr('reset')} \n")
    for item in sorted_queue:
        product_name = item[0]
        product_price = round(item[1], 1)
        product_url = item[2]
        print(
            f"{fg('green_1')}The Product Name is:{attr('reset')}{fg('dark_slate_gray_2')} {product_name}{attr('reset')} "  # pylint: disable=line-too-long
            f"{fg('green_1')}The Price is:{attr('reset')}{fg('orange_red_1')} {product_price}{attr('reset')} "  # pylint: disable=line-too-long
            f"{fg('green_1')} URL: {fg('yellow')}{product_url} {attr('reset')} ")

        # create a list with the items that are below the target price and will be sent by email
        send_email_items_list = [
            item for item in sorted_queue if item[1] <= TARGET_PRICE]

    # make result list to html tables
    email_body_result = email_body_html_formating(send_email_items_list)

    if len(send_email_items_list) > 0:
        # get min price from the list for the email subject
        min_priced_product = min(send_email_items_list, key=lambda x: x[1])
    else:
        min_priced_product = ['No items below target price', 0]

    WANT_EMAIL = False
#    if WANT_EMAIL and len(send_email_items_list) > 0:
#        send_email(sent_from='ignarvalme@gmail.com',
#                   sent_to='ignarvalme@gmail.com',
#                   sent_subject=f'Amazon Price Alert: {min_priced_product[0]} with price {min_priced_product[1]}',
#                   sent_body=email_body_result)
