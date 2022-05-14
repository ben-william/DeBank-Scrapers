import pygsheets
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# set up driver
chrome_driver_path = '<< Filepath to your chrome driver file >>'
s = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=s)

GOOGLE_API_FILE = '<< Filepath to your .json file >>'

# initialize
final_list = []


wallets_to_scan = ['walletaddress1',
                   'walletaddress2']


for n in range(0, len(wallets_to_scan)):
    URL = f'https://debank.com/profile/{wallets_to_scan[n]}'

    driver.get(url=URL)
    time.sleep(1)  # avoids a false trip of data_update on pageload

    try:

        ########## WALLET SCRAPING ###############

        # wait for data to load fully
        data_update = WebDriverWait(driver, 30).until(EC.text_to_be_present_in_element(
            (By.CLASS_NAME, "UpdateButton_refresh__1tR6K"), text_='Data updated'))

        wallet_div = driver.find_element(
            By.CLASS_NAME, "Wallet_container__3JSJH")

        wallet_rows = wallet_div.find_elements(
            By.CLASS_NAME, "db-table-row")

        wallet_assets = []
        # get values from each row, save

        for i in wallet_rows:
            columns = i.find_elements(By.CLASS_NAME, "db-table-cell")
            chain_img_url = columns[0].find_element(
                By.CSS_SELECTOR, "img").get_attribute("src")
            chain = chain_img_url.url.split('/')[-1].split('.')[0]
            wallet_assets.append(
                {
                    "asset": columns[0].text,
                    "chain": chain,
                    "price": columns[1].text,
                    "balance": columns[2].text,
                    "value": columns[3].text,
                }
            )

        ########## PROTOCOL SCRAPING ###############

        protocol_assets = []

        protocol_divs = driver.find_elements(
            By.CLASS_NAME, "Project_portfolioProject__2f0GB")

        for protocol_div in protocol_divs:

            # get protocol name
            protocol_name = protocol_div.find_element(
                By.CLASS_NAME, "ProjectTitle_name__331gA").text

            # get protocol chain
            try:
                chain_link = protocol_div.find_element(
                    By.CSS_SELECTOR, "img[class='ProjectTitle_projectChain__2PfPP'").get_attribute("src")
                protocol_chain = chain_link.split('/')[-1].split('.')[0]
            except:
                protocol_chain = 'eth'

            # get protocol balance (if < 10$, skip)
            protocol_balance = int(protocol_div.find_element(
                By.CLASS_NAME, "ProjectTitle_number__IrHQU").text.split('$')[1].replace(',', ''))
            if protocol_balance < 10:
                continue

            # loop through cards
            protocol_cards = protocol_div.find_elements(
                By.CLASS_NAME, "card_card__i5VM9")

            for card in protocol_cards:
                # get label/function
                protocol_tag = card.find_element(
                    By.CLASS_NAME, "BookMark_container__3AoLL").text
                # check if 'lending', get health score if so
                if protocol_tag == "Lending":
                    health_score = card.find_element(
                        By.CSS_SELECTOR, "div[class='flex_flexRow__2Uu_s More_line__28qwV']").text.split('\n')[1]
                else:
                    health_score = None

                # get rows
                card_rows = card.find_elements(
                    By.CSS_SELECTOR, "div[class='EmbededTable_contentRow__3NvJL flex_flexRow__2Uu_s ']")

                # find columns
                for row in card_rows:
                    columns = row.find_elements(By.CSS_SELECTOR, "span")

                    protocol_pool = columns[0].text

                    # check for 3rd column presence, skip if so
                    if len(columns) == 3:
                        total_value = int(columns[2].text.split('$')[
                            1].replace(',', ''))
                    else:
                        total_value = int(columns[3].text.split('$')[
                            1].replace(',', ''))
                    # skip loop if value < 5$
                    if total_value < 5:
                        continue

                    # need to loop if balance has multiple assets
                    assets_in_balance = columns[1].find_elements(
                        By.CSS_SELECTOR, "div")

                    for asset in assets_in_balance:
                        balance = float(asset.text.split(' ')
                                        [0].replace(',', ''))
                        value = total_value/len(assets_in_balance)
                        protocol_assets.append({
                            "protocol": protocol_name,
                            "tag": protocol_tag,
                            "chain": protocol_chain,
                            "pool": protocol_pool,
                            "asset": asset.text.split(' ')[1],
                            "price": value/balance,
                            "balance": balance,
                            "value": value,
                            "healthscore": health_score,
                        })

        final_list.append({
            "wallet_id": wallets_to_scan[n],
            "wallet": wallet_assets,
            "protocols": protocol_assets,
        })

    finally:
        print('done')

driver.quit()

############ Print DF to gSheets ############

gc = pygsheets.authorize(
    service_file=GOOGLE_API_FILE)

sheet = gc.open('DeBank Scrape')
worksheet = sheet[0]

# Clear wallet and protocol columns in sheet
pygsheets.datarange.DataRange(start='A1', end='F', worksheet=worksheet).clear()
pygsheets.datarange.DataRange(start='H1', end='P', worksheet=worksheet).clear()

print_offset = 0
for entry in final_list:
    wallet_df = pd.DataFrame(entry['wallet'])
    protocol_df = pd.DataFrame(entry['protocols'])

    worksheet.update_value((1+print_offset, 1), entry['wallet_id'], parse=None)
    worksheet.update_value((2+print_offset, 1), "Wallet: ", parse=None)
    worksheet.update_value((2+print_offset, 8), "Protocols: ", parse=None)

    worksheet.set_dataframe(wallet_df, (2+print_offset, 2))  # (row, column)
    worksheet.set_dataframe(protocol_df, (2+print_offset, 8))

    # space out wallets by 50 rows to avoid over-writing
    print_offset += 50
