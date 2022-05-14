import pygsheets
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import time

wallet_to_scan = '<< wallet address here, including "0x" prefix >>'

# set up driver
CHROME_DRIVER_PATH = '<< Filepath to your chrome driver file >>'
s = Service(executable_path=CHROME_DRIVER_PATH)
driver = webdriver.Chrome(service=s)

GOOGLE_API_FILE = '<< Filepath to your .json file >>'

URL = f'https://debank.com/profile/{wallet_to_scan}/history'

driver.get(url=URL)

all_txns = []

try:

    # watch for update
    time.sleep(1)  # avoids a false trip of data_update on pageload
    data_update = WebDriverWait(driver, 30).until(EC.text_to_be_present_in_element(
        (By.CLASS_NAME, "UpdateButton_refresh__1tR6K"), text_="Data updated"))
    print(data_update)

    # find load more button
    load_more_btn = driver.find_element(
        By.CLASS_NAME, "History_loadMore__1DkZs")

    # open full history
    try:
        for i in range(0, 100):
            load_more_btn.click()
            time.sleep(1)
            print('opening history...')

    except StaleElementReferenceException:  # escapes loop once 'load more' button disappears
        pass

    # find txn table
    txn_table = driver.find_element(By.CLASS_NAME, "History_table__9zhFG")

    # find txn rows
    rows = txn_table.find_elements(By.CLASS_NAME, "History_tableLine__3dtlF")

    # initialize loop
    row_num = 0
    failed_rows = []

    # scrape txn row
    for i in range(0, len(rows)):
        row_num += 1
        try:
            txn_date = rows[i].find_element(
                By.CLASS_NAME, "History_sinceTime__3JN2E").text
            txn_chain = rows[i].find_element(
                By.CLASS_NAME, "History_rowChain__eo4NT").get_attribute('alt')
            txn_link = rows[i].find_element(
                By.TAG_NAME, "a").get_attribute('href')
            txn_title = rows[i].find_element(
                By.CLASS_NAME, "History_ellipsis__rfBNq").text
            txn_interacted_with = rows[i].find_element(
                By.CLASS_NAME, "History_greyText__KIi2L").get_attribute('href')
            assets_traded = rows[i].find_elements(
                By.CLASS_NAME, "History_tokenChangeItem__3NN7B")
        except:
            failed_rows.append(txn_link)

        # build a row/dataframe entry for every asset moved in the txn

        for asset in assets_traded:
            # determine if asset inbound or outbound
            direction = asset.find_element(By.TAG_NAME, "span").text
            if direction == '+':
                asset_direction = 'in'
            else:
                asset_direction = 'out'

            # determine asset title and amount traded
            asset_title = asset.get_attribute('title')
            txn_text = asset.find_element(
                By.CLASS_NAME, "db-autoTooltip").text.split()
            try:
                asset_float = float(txn_text[0].replace(',', ''))
            except:
                pass

            # find gas fee where available
            try:
                gas_fee = rows[i].find_element(
                    By.CLASS_NAME, "History_txExplain__-I6jt").text.split()[-1]
            except:
                gas_fee = None

            # assemble dataset and save
            txn_data = {
                "Date": txn_date,
                "Chain": txn_chain,
                "Link": txn_link,
                "Action": txn_title,
                "Interacted With": txn_interacted_with,
                "In/Out": asset_direction,
                "Balance Traded": asset_float,
                "Asset Traded": asset_title,
                "Gas Fee": gas_fee,
            }

            all_txns.append(txn_data)

except Exception as e:
    print(repr(e))
    print(txn_date)
    print(txn_chain)
    print(txn_link)
    print(txn_title)
    print(txn_interacted_with)
    print(txn_text)
    failed_rows.append(txn_link)


finally:
    print('closed')
    driver.quit()
    print('failed rows:', '\n', failed_rows)


############ Print DF to gSheets ############

gc = pygsheets.authorize(
    service_file=GOOGLE_API_FILE)

sheet = gc.open('DeBank Scrape')
worksheet = sheet[1]
worksheet.clear()

df = pd.DataFrame(all_txns)
print(df)

worksheet.set_dataframe(df, (2, 2))
