# DeBank Scraping
Two scraping scripts using Selenium, that scrape the popular wallet tracking website DeBank.

```
Note: I am aware this project could use considerable refactoring to make it more robust, implement OOP, etc. It is a prototype of a product I would like to eventually build, and only run locally for testing purposes. I am currently focused on exploring new concepts to build more rather than perfecting what currently exists. 
```

## Dependencies

### Selenium / Chrome

This project runs a Chrome browser with Selenium. To execute the script:
* Download an appropriate driver
* Update CHROME_DRIVER_PATH within the file.

Chrome Drivers can be downloaded here: https://chromedriver.chromium.org/downloads


### Pygsheets

Pygsheets is a Google Sheets API wrapper, used to push the scraped data to a spreadsheet. **It is not necessary to use pygsheets.** Once the data is scraped it can be displayed and manipulated using other methods.

In order to run this functionality, follow the authorization instructions here: https://pygsheets.readthedocs.io/en/latest/authorization.html.

The authorization method used in this script is via a Service Account. Once set up it will need to reference a .json file including the auth key, placed in the same directory as the script. A blank example is included in this repo.

Remember to update the filepath variable 'GOOGLE_API_FILE'

