from seleniumbase import Driver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
from Config import USER_NAME, PASSWORD,SEARCH_STRING
import json
import pyperclip
import os
import requests


from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

media_directory = "downloaded_media"
os.makedirs(media_directory, exist_ok=True)

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

    def scroll_comments_section(self, post):
        """Helper function to scroll within the comments section of a post."""
        comments_section = post.find_element(By.CLASS_NAME, "comments-comments-list")
        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", comments_section)
        time.sleep(2)  # Adjust sleep as necessary for dynamic loading

    def expand_replies(self, comment):
        """Helper function to expand replies for a given comment."""
        try:
            more_replies_button = comment.find_element(By.CSS_SELECTOR,
                                                       "button.comments-comment-item__show-replies-button")
            self.driver.execute_script("arguments[0].click();", more_replies_button)
            time.sleep(1)  # Adjust as necessary
        except:
            pass  # Ignore if no "show replies" button

    def crawl(self, search_string: str, crawl_replies: bool = False):
        """Crawl LinkedIn posts based on the search string."""
        # Type the search string into the search input field
        search_box = self.driver.find_element(By.CSS_SELECTOR, "input[role='combobox'][placeholder='Search']")
        search_box.send_keys(search_string)
        search_box.send_keys(Keys.RETURN)  # Press Enter to perform the search

        # Wait for posts to load
        self.driver.wait_for_element_visible("div.feed-shared-update-v2")  # Update with actual selector

        while True:
            # Infinite scroll to load all posts on the page
            self.infinite_scroll()  # Ensure this function waits until all posts are loaded

            # Now capture all post elements after scrolling
            post_elements = self.driver.find_elements(By.CSS_SELECTOR,
                                                      "div.feed-shared-update-v2")  # Update with actual selector

            for post in post_elements:
                try:
                    # Extract author name
                    author_name = post.find_element(By.XPATH, ".//span[@aria-hidden='true']").text
                    print(f"Author: {author_name}")

                    # Extract profile URL
                    profile_url_element = post.find_element(By.CSS_SELECTOR,
                                                            "a.app-aware-link.update-components-actor__meta-link")
                    profile_url = profile_url_element.get_attribute("href")
                    print(f"Profile URL: {profile_url}")

                    # Extract likes count
                    try:
                        likes_count_element = post.find_element(By.CSS_SELECTOR,
                                                                "span.social-details-social-counts__reactions-count")
                        likes_count = likes_count_element.text.strip()
                    except:
                        likes_count = 0
                    print(f"Likes Count: {likes_count}")

                    # Extract comments count
                    try:
                        comments_button = post.find_element(By.CSS_SELECTOR,
                                                            "li.social-details-social-counts__comments button")
                        comments_count = comments_button.get_attribute("aria-label").split()[0]
                    except:
                        comments_count = 0
                    print(f"Comments Count: {comments_count}")

                    # Extract shares count
                    try:
                        shares_button = post.find_element(By.XPATH, ".//button[contains(@aria-label, 'reposts')]")
                        shares_count = shares_button.get_attribute("aria-label").split()[0]
                    except:
                        shares_count = 0
                    print(f"Shares Count: {shares_count}")

                    # Initialize media list for each post
                    media = []

                    # Extract images specific to this post
                    try:
                        image_elements = post.find_elements(By.CLASS_NAME, "ivm-view-attr__img--centered")  # Update with actual image selector
                        for image_element in image_elements:
                            image_url = image_element.get_attribute("src")
                            media.append({"type": "image", "url": image_url})
                            print(f"Image URL for Post: {image_url}")
                    except Exception as e:
                        print(f"No images found in post: {e}")

                    # Extract videos specific to this post
                    try:
                        video_elements = post.find_elements(By.CSS_SELECTOR,
                                                            "video.vjs-tech")  # Update with actual video selector
                        for video_element in video_elements:
                            video_url = video_element.get_attribute("src")
                            media.append({"type": "video", "url": video_url})
                            print(f"Video URL for Post: {video_url}")
                    except Exception as e:
                        print(f"No videos found in post: {e}")


                    # Collect data for each post
                    post_data = {
                        'author_name': author_name,
                        'profile_url': profile_url,
                        'likes': likes_count,
                        'shares': shares_count,
                        'media': media,
                        'comments_count': comments_count,
                        #'comments': comments
                    }
                    self.posts.append(post_data)

                except Exception as e:
                    print(f"Error while processing a post: {e}")



            # Click the "Next" button and break the loop if there are no more pages
            if not self.click_next_button():
                break
            #break

# Usage example:

username_input = USER_NAME
password_input = PASSWORD

crawler = LinkedInCrawler()

# Log in to LinkedIn using provided credentials.
crawler.login(username_input, password_input)

search_string=SEARCH_STRING
# Perform crawling operation after logging in.
crawler.crawl(search_string, crawl_replies=True)

print(crawler.posts)
with open('Output.json', 'w') as op:
    json.dump(crawler.posts,op, indent=4 )

# Close the browser manually when all tasks are complete.
#crawler.close_browser()