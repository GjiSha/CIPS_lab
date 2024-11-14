from seleniumbase import Driver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
from Config import USER_NAME, PASSWORD
import json
import os
import requests

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Base class for crawling posts on social media platforms
class PostCrawler:
    def __init__(self):
        self.driver = Driver()  # Initialize SeleniumBase Driver instance
        self.posts = []  # List to store crawled posts

    def login(self, username: str, password: str):
        """Login method to be implemented by child classes."""
        raise NotImplementedError("Subclasses should implement this method.")

    def crawl(self, search_string: str, crawl_replies: bool = False):
        """Crawl method to be implemented by child classes."""
        raise NotImplementedError("Subclasses should implement this method.")


    def close_browser(self):
        """Close the browser session."""
        self.driver.quit()  # Manually close the session when done


# Child class for crawling LinkedIn posts
class LinkedInCrawler(PostCrawler):
    def login(self, username: str, password: str):
        """Log in to LinkedIn using provided credentials."""
        self.driver.open("https://www.linkedin.com/login")

        time.sleep(2) # incase verification is required

        # Input username and password
        self.driver.type("input#username", username)  # Update selector if needed
        self.driver.type("input#password", password)  # Update selector if needed

        # Press Enter to submit the login form
        self.driver.find_element("input#password").send_keys(Keys.RETURN)

        time.sleep(15)  # incase verification is required

        # Optionally, wait for successful login (e.g., wait for search bar to appear)
        self.driver.wait_for_element_visible("input[placeholder='Search']")

    def infinite_scroll(self):
        """Scroll down the page to load more content."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to the bottom of the page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait for new content to load
            time.sleep(2)  # Adjust sleep time as per your internet speed

            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                break  # If no new content is loaded, exit the loop

            last_height = new_height

    def click_next_button(self):
        """Click the 'Next' button if it exists."""
        try:
            next_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Next']")
            # Check if the button is disabled
            if 'disabled' in next_button.get_attribute("class") or not next_button.is_enabled():
                print("Next button is disabled or not clickable.")
                return False
            next_button.click()
            time.sleep(2)  # Wait for new content to load after clicking 'Next'
            return True  # Return True if 'Next' button was found and clicked
        except Exception as e:
            print(f"No more 'Next' button found or error occurred: {e}")
            return False  # Return False if 'Next' button was not found




    def crawl(self, search_string: str, crawl_replies: bool = False):
        """Crawl LinkedIn posts based on the search string."""
        # Type the search string into the search input field
        search_box = self.driver.find_element("input[role='combobox'][placeholder='Search']")
        search_box.send_keys(search_string)

        # Press Enter to perform the search
        search_box.send_keys(Keys.RETURN)

        # Wait for posts to load (update with actual selector for posts)
        self.driver.wait_for_element_visible("div.feed-shared-update-v2")  # Update with actual selector

        while True:

            # Crawl posts and media based on search results
            post_elements = self.driver.find_elements("div.feed-shared-update-v2")  # Update with actual selector for posts
            self.infinite_scroll()
            for post in post_elements:
                try:
                    author_name = post.find_element(By.XPATH, ".//span[@aria-hidden='true']").text
                    print(author_name)
                    profile_url_element = post.find_element(By.CSS_SELECTOR,
                                                              "a.app-aware-link.update-components-actor__meta-link")

                    # Extract the href attribute (URL of the profile)
                    profile_url = profile_url_element.get_attribute("href")
                    print(profile_url)



                    try:
                        likes_count_element = post.find_element(By.CSS_SELECTOR,
                                                                "span.social-details-social-counts__reactions-count")
                        likes_count = likes_count_element.text.strip()

                    except:
                        likes_count=0



                    # Extract the text content (number of likes) and strip any extra spaces

                    print(f"likes count: {likes_count}")

                    # Extract Comments Count

                    
                    try:
                        comments_button = post.find_element(By.CSS_SELECTOR,
                                                            "li.social-details-social-counts__comments button")
                        comments_count = comments_button.get_attribute("aria-label").split()[0]
                    except:
                        comments_count=0

                    print(f"Comments Count: {comments_count}")

                    # Extract Shares Count


                    try:
                        shares_button = post.find_element(By.XPATH,
                                                          ".//button[contains(@aria-label, 'reposts')]")
                        shares_count = shares_button.get_attribute("aria-label").split()[0]
                    except:
                        shares_count = 0

                    print(f"shares Count: {shares_count}")

                    post_data = {
                        'author_name': author_name,
                        'profile_url': profile_url,

                        'likes': likes_count,
                        'shares': shares_count,
                        #'media': media,
                        'comments': comments_count,
                        #'replies': []
                    }
                    self.posts.append(post_data)



                except Exception as e:
                    print(f"Error while processing a post: {e}")

            if not self.click_next_button():
               break

# Usage example:

username_input = USER_NAME
password_input = PASSWORD

crawler = LinkedInCrawler()

# Log in to LinkedIn using provided credentials.
crawler.login(username_input, password_input)

# Perform crawling operation after logging in.
crawler.crawl('"black lives matter" OR "all lives matter"', crawl_replies=True)

print(crawler.posts)
with open('Output.json', 'w') as op:
    json.dump(crawler.posts,op, indent=4 )

# Close the browser manually when all tasks are complete.
crawler.close_browser()