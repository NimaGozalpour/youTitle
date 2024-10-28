# Import necessary libraries
from selenium import webdriver  # For browser automation
from selenium.webdriver.remote.webdriver import WebDriver  # For typing hinting of WebDriver
from selenium.webdriver.common.by import By  # To specify methods of locating elements
from bs4 import BeautifulSoup  # For parsing HTML content
from bs4.element import ResultSet, Tag  # For typing hinting with BeautifulSoup
import time  # For adding delays
import pandas as pd  # For data manipulation and saving to Excel

# Function to create and return a new Chrome WebDriver instance
def new_driver():
    driver = webdriver.Chrome()  # Initialize Chrome driver
    return driver

# Function to scroll to the end of the page
def scroll_to_end(driver: WebDriver):
    SCROLL_PAUSE_TIME = 1.5  # Pause time between scrolls
    last_height = driver.execute_script("return document.documentElement.scrollHeight")  # Get initial scroll height
    while True:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")  # Scroll to bottom
        time.sleep(SCROLL_PAUSE_TIME)  # Wait for page to load
        new_height = driver.execute_script("return document.documentElement.scrollHeight")  # Check new scroll height
        if new_height == last_height:  # Break if no new content loaded
            break
        last_height = new_height  # Update last height to continue scrolling

# Function to retrieve video elements from the page and close the driver
def read_page_items(driver: WebDriver):
    page_source = driver.page_source  # Get the HTML source of the page
    driver.close()  # Close the browser window

    # Parse page source with BeautifulSoup
    page_soup = BeautifulSoup(markup=page_source, features="html.parser")

    # Find all video title links on the page
    ytd_items = page_soup.find_all('a', id='video-title-link')

    print("{} videos are found".format(len(ytd_items)))  # Print number of videos found
    if len(ytd_items) == 0:
        print("could not find any video")
        return 0
    else:
        return ytd_items  # Return the list of video items

# Function to extract video information from HTML elements
def extract_info(items: ResultSet):
    info = {'channel_name': [], 'title': [], 'publish_date': [], 'views': [], 'duration': []}  # Info dictionary
    for item in items:
        info['title'].append(item.get('title'))  # Get video title

        # Extract words from aria-label and parse for date, views, and duration
        words = item.get('aria-label')[len(info['title'][-1]):].split()
        index = []
        reversed_words = words[::-1]
        for i, word in enumerate(reversed_words):
            if word in ['ago', 'views', 'by']:
                index.append(i)

        # Extract video details based on parsed words
        info['duration'].append(" ".join(words[-index[0]:]))
        info['publish_date'].append(" ".join(words[-index[1]:-index[0]]))
        info['views'].append(words[-index[1] - 2].replace(',', ''))
        info['channel_name'].append(" ".join(words[1:-index[1] - 2]))

    return info  # Return the dictionary with extracted information

# Function to write video information to an Excel file
def write_info(dict_info: dict):
    save_path = './output/{}.xlsx'.format(dict_info['channel_name'][0])  # File path based on channel name
    print(save_path)
    df = pd.DataFrame.from_dict(dict_info)  # Create a DataFrame from info dictionary
    df.to_excel(save_path)  # Save DataFrame to Excel file

# Function to scrape video information for a given YouTube channel
def get_channel_info(channel: str):
    LOAD_PAGE_PAUSE_TIME = 1.5  # Pause time after page load
    url = "https://www.youtube.com/@{}/videos".format(channel)  # Construct URL to channel's videos

    driver = new_driver()  # Initialize a new Chrome driver
    driver.get(url)  # Open the URL in the browser

    time.sleep(LOAD_PAGE_PAUSE_TIME)  # Wait for page to load

    # Handle potential cookie pop-up
    while url != driver.current_url:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(LOAD_PAGE_PAUSE_TIME)
        button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Reject all']")
        button.click()  # Reject cookies

    scroll_to_end(driver)  # Scroll to the end of the page to load all videos
    time.sleep(LOAD_PAGE_PAUSE_TIME)  # Wait for loading

    items = read_page_items(driver)  # Extract video items from the page

    if not isinstance(items, int):  # If items are found
        dict_info = extract_info(items)  # Extract video information

    write_info(dict_info)  # Write extracted information to an Excel file

# Main function to read channel names and initiate scraping for each channel
def main():
    channels_file_path = './channels.txt'  # File path for channels list
    with open(channels_file_path, "r") as file:  # Open file to read channels
        channels = [line.strip() for line in file]  # Store each line (channel name) in a list

    # Scrape information for each channel
    for channel in channels:
        get_channel_info(channel)

# Execute main function if script is run directly
if __name__ == '__main__':
    main()