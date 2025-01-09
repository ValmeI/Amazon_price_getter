'''This script will get the price of a product from amazon 
and send an email if the price is below the target price'''
# from twilio import send_email
import re
import threading

from colored import fg, attr
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def get_product_url(product_code_list: list):
    '''generates a list of amazon urls with the product codes for the different amazon sites'''
    list_of_amazon_urls = ['https://www.amazon.de', 'https://www.amazon.fr',
                           'https://www.amazon.es', 'https://www.amazon.it']
    # cross check the product code with the amazon urls
    product_urls_list = [
        f'{url}/dp/{code}' for url in list_of_amazon_urls for code in product_code_list]
    return product_urls_list


def get_product_price(defined_list: list, input_url: str):
    '''gets the product price from the amazon url'''
    try:
        options = Options()
        options.add_argument("--headless")
        # log_level=0 to disable logging, for example: ====== WebDriver manager ======
        options.add_argument("--log-level=3")  # Adjust the log level
        options.add_experimental_option('excludeSwitches', ['enable-logging'])  # This line disables the DevTools logging
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(input_url)
        wait = WebDriverWait(driver, 10)  # Wait for up to 10 seconds
        product_title_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[id="productTitle"]')))
        product_title = product_title_element.text
        # Wait for the price element and extract the font tag text
        product_price_whole_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'a-price-whole')))
        # Check if the price element is hidden
        if product_price_whole_element.get_attribute('aria-hidden') == 'true':
            print(f'The price for {product_title} is hidden. Skipping this item.')
            return
        try:
            product_price_whole = product_price_whole_element.text
        except: # pylint: disable=bare-except
            product_price_whole = product_price_whole_element.find_element(By.TAG_NAME, 'font').text
        product_price_fraction_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'a-price-fraction')))
        product_price_fraction = product_price_fraction_element.text
        final_product_price = f'{product_price_whole}.{product_price_fraction}'
        get_first_product_title = re.split(r'[-–|:]', product_title)[0].strip()
        product_price_int = float(
            final_product_price.replace('€', '').replace(',', '.'))
        # add the result in the list
        defined_list.append([get_first_product_title, product_price_int, input_url])
    except Exception as exception:  # pylint: disable=broad-except disable=invalid-name
        print(f'URL: {input_url} error: {exception}')


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

    TARGET_PRICE = 240

    #amazon_product_code_list = ['B0BDK2CZ8N', 'B0BDJ3ND5X', 'B0BDJ55SSD']  # Pixel 7 Pro
    # amazon_product_code_list = ['B0BDJG3TWP', 'B0BDK63RF3', 'B0BDJFKY7B'] # Pixel 7
    # amazon_product_code_list = ['B08C7KG5LP', 'B091CQH6VT', 'B08C7KCJF5']  # Sony WH-1000XM4 big ones
    # amazon_product_code_list = ['B095D1HCYG', 'B095DNPH4R'] # Sony WF-1000XM4 Buds
    # amazon_product_code_list = ['B0CNH4Z5DP', 'B0CNH7FRSF', 'B0CNH7J95P', 'B0CNH6RHV6'] # Samsung Galaxy S24 Ultra
    amazon_product_code_list = ['B0CQ4H4H7X', 'B0D1CJWVB8'] # AMD Ryzen 7 5700X3D CPU AM4
    # Create a list to hold the results
    result_list = []
    amazon_final_urls_list = get_product_url(amazon_product_code_list)

    # Create a list to hold the threads we are going to create.
    # Needed for later joining as to wait for all the threads to complete
    threads = []
    for url in amazon_final_urls_list:
        thread = threading.Thread(
            target=get_product_price, args=(result_list, url,))
        thread.start()
        threads.append(thread)
    # Wait for all the threads to complete
    for thread in threads:
        thread.join()
    # sort list by price to list
    sorted_list = sorted(result_list, key=lambda x: x[1])
    print(f"{fg('blue')}{attr('bold')}Sorted Queue contents of all "
          f"the results for price target of {TARGET_PRICE}:{attr('reset')} \n")
    for item in sorted_list:
        product_name = item[0][:20] # cut it smaller
        product_price = round(item[1], 1)
        product_url = item[2]
        print(
            f"{fg('green_1')}The Product Name is:{attr('reset')}{fg('dark_slate_gray_2')} {product_name}{attr('reset')} "  # pylint: disable=line-too-long
            f"{fg('green_1')}The Price is:{attr('reset')}{fg('orange_red_1')} {product_price}{attr('reset')} "  # pylint: disable=line-too-long
            f"{fg('green_1')} URL: {fg('yellow')}{product_url} {attr('reset')} ")

     # create a list with the items that are below the target price and will be sent by email
    send_email_items_list = [item for item in sorted_list if item[1] <= TARGET_PRICE]

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
