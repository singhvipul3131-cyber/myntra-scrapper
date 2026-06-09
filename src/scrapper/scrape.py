from hashlib import new
from tkinter import SE
from selenium import webdriver
from selenium.webdriver.common.by import By
from src.exception import CustomException
from bs4 import BeautifulSoup as bs
import pandas as pd 
import os, sys
import time
from selenium.webdriver.chrome.options import Options
from urllib.parse import quote, urljoin


class ScrapeReviews:
    def __init__(self, product_name: str, no_of_products: int):
        options = Options()
        
        # SAARE HEADLESS/BACKGROUND OPTIONS HATA DIYE HAIN TAAKI BROWSER SCREEN PAR DIKHE
        options.add_argument("--start-maximized") # Browser poori screen par khulega
        options.add_argument("--disable-blink-features=AutomationControlled") # Myntra ko pata nahi chalega ki yeh automation hai
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=options)
        
        # Script ko bolna ki automation detect na hone de
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        
        self.product_name = product_name
        self.no_of_products = no_of_products
        self.driver_title = "Unknown Product"
        self.product_rating_value = "No Rating"
        self.product_price = "No Price"

    def scrape_products_urls(self, product_name):
        try:
            search_string = product_name.replace(" ", "-")
            encoded_query = quote(search_string)
            url = f"https://www.myntra.com/{search_string}?rawQuery={encoded_query}"
            
            print(f"Opening Search URL: {url}") # <--- Pata chalega browser kahan gaya
            self.driver.get(url)
            
            # Browser ko thoda rokhein taaki page poora load ho jaye
            time.sleep(5) 
            
            myntra_text = self.driver.page_source
            myntra_html = bs(myntra_text, "html.parser")
            
            # Agar purani class 'results-base' kaam nahi kar rahi toh hum seedhe 'a' tags nikalenge
            product_urls = []
            
            # Tarika 1: Pehle product-base dhoodhein
            pyclass = myntra_html.findAll("li", {"class": "product-base"})
            if not pyclass:
                # Tarika 2: Agar nahi mila toh backup ke liye results-base try karein
                pyclass = myntra_html.findAll("ul", {"class": "results-base"})
                
            print(f"Found {len(pyclass)} product elements on page.") # <--- Yeh batayegi element mile ya nahi
            
            for i in pyclass:
                href = i.find_all("a", href=True)
                for product_no in range(len(href)):
                    t = href[product_no]["href"]
                    product_urls.append(t)
            
            print(f"Total Unique URLs found: {len(list(dict.fromkeys(product_urls)))}")
            return product_urls
        except Exception as e:
            raise CustomException(e, sys)
    
    def extract_reviews(self, product_link):
        try:
            product_link = urljoin("https://www.myntra.com", product_link)
            print(f"-> Going to product page: {product_link}")
            self.driver.get(product_link)
            time.sleep(4) # Page load hone ka pura time
            
            prodRes = self.driver.page_source
            prodRes_html = bs(prodRes, "html.parser")
            
            title_h = prodRes_html.findAll("title")
            if title_h:
                self.driver_title = title_h[0].text

            overallRating = prodRes_html.findAll("div", {"class": "index-overallRating"}) or prodRes_html.findAll("div", {"class": "overallRating-base"})
            for i in overallRating:
                try:
                    self.product_rating_value = i.find("div").text
                except:
                    pass

            price = prodRes_html.findAll("span", {"class": "pdp-price"}) or prodRes_html.findAll("strong", {"class": "pdp-price"})
            for i in price:
                self.product_price = i.text

            # --- UPDATED REVIEWS LINK FINDER FOR NEW UI ---
            product_reviews = None
            
            # Tarika 1: Detailed reviews class
            product_reviews = prodRes_html.find("a", {"class": "detailed-reviews-allReviews"})
            
            # Tarika 2: Naya layout rating format class
            if not product_reviews:
                product_reviews = prodRes_html.find("a", {"class": "rating-format-allReviews"})
            
            # Tarika 3: Pure text search
            if not product_reviews:
                product_reviews = prodRes_html.find("a", string=lambda t: t and ("All" in t or "Reviews" in t or "View all" in t))
            
            # Tarika 4: URL fallback check
            if not product_reviews:
                for a_tag in prodRes_html.find_all("a", href=True):
                    if "/reviews/" in a_tag["href"] or "all-reviews" in a_tag["href"]:
                        product_reviews = a_tag
                        break

            if product_reviews:
                print("   [SUCCESS] Found 'All Reviews' link!")
            else:
                print("   [WARNING] Could not find reviews link for this product.")
                
            return product_reviews
        except Exception as e:
            raise CustomException(e, sys)
        
    def scroll_to_load_reviews(self):
        try:
            self.driver.set_window_size(1920, 1080)
            # FIXED BOTH SCROLL PLACES: No 'documents', only 'document'
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(2)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
        except Exception as e:
            print("Scroll ke andar error:", e)

    def extract_products(self, product_reviews, product_url):
        try:
            if not product_reviews or "href" not in product_reviews.attrs:
                return pd.DataFrame()
                
            t2 = product_reviews["href"]
            reviews_link = urljoin("https://www.myntra.com", t2)
            product_link = urljoin("https://www.myntra.com", product_url)
            
            print(f"   -> Opening Review Page: {reviews_link}")
            self.driver.get(reviews_link)
            time.sleep(4)
            
            self.scroll_to_load_reviews()
            
            review_page = self.driver.page_source
            review_html = bs(review_page, "html.parser")
            
            # --- NEW UPDATED SELECTORS FOR MYNTRA REVIEWS ---
            review_containers = (
                review_html.findAll("div", {"class": "user-reviews-userReviewWrapper"}) or 
                review_html.findAll("div", {"class": "detailed-review-userReviewContainer"}) or
                review_html.findAll("div", {"class": "review-summary-container"}) or
                review_html.findAll("div", {"class": "user-review-main"})
            )

            print(f"   -> Found {len(review_containers)} review blocks on review page.")

            review_list = []
            for i in review_containers:
                rating = "No Rating"
                try:
                    rating_span = i.find("span", {"class": "user-reviews-rating"}) or i.find("span")
                    if rating_span:
                        rating = rating_span.get_text().strip()
                except:
                    pass
                    
                comment = "No comment Given"
                try:
                    comment_div = (
                        i.find("div", {"class": "user-review-reviewTextWrapper"}) or 
                        i.find("p", {"class": "user-review-comment"}) or
                        i.find("div", {"class": "review-text"})
                    )
                    if comment_div:
                        comment = comment_div.text.strip()
                except:
                    pass
                    
                name, date = "No name Given", "No date Given"
                try:
                    left_section = i.find("div", {"class": "user-review-left"}) or i.find("div", {"class": "review-user-info"})
                    if left_section:
                        spans = left_section.find_all("span")
                        if len(spans) > 0:
                            name = spans[0].text.strip()
                        if len(spans) > 1:
                            date = spans[1].text.strip()
                except:
                    pass
                
                mydict = {
                    "Product Name": self.driver_title,
                    "Product Link": product_link,
                    "Over_All_Rating": self.product_rating_value,
                    "Price": self.product_price,
                    "Date": date,
                    "Rating": rating,
                    "Name": name,
                    "Comment": comment,
                }
                review_list.append(mydict)

            review_data = pd.DataFrame(review_list)
            return review_data
        except Exception as e:
            raise CustomException(e, sys)
        
    def get_review_data(self):
        try:
            product_urls = self.scrape_products_urls(product_name=self.product_name)
            product_urls = list(dict.fromkeys(product_urls))
            
            product_details = []
            scraped_count = 0
            
            print(f"Loop shuru ho raha hai... Total {len(product_urls)} URLs check karne hain.")
            
            for product_url in product_urls:
                if scraped_count >= self.no_of_products:
                    print(f"Target reached! Scraped {scraped_count} products.")
                    break
                    
                print(f"--- Processing Product {scraped_count + 1}: {product_url} ---")
                review = self.extract_reviews(product_url)
                
                if review:
                    product_detail = self.extract_products(review, product_url)
                    if product_detail is not None and not product_detail.empty:
                        product_details.append(product_detail)
                        scraped_count += 1
                        print(f"   [SUCCESS] Successfully extracted reviews for this product!")
                    else:
                        print("   [INFO] Product detail was empty or None.")
                else:
                    print("   [INFO] Skiping this product because 'All Reviews' link was not found.")

            self.driver.quit()
            
            # AGAR KUCH BHI DATA MILA TOH CSV BANAO
            if product_details:
                print("Creating data.csv with scraped data...")
                data = pd.concat(product_details, axis=0, ignore_index=True)
                data.to_csv("data.csv", index=False)
                print(">>> data.csv successfully created in your folder! <<<")
                return data
            else:
                # AGAR BILKUL DATA NAHI MILA TOH DUMMY FILE BANAO TAAKI STREAMLIT CRASH NA HO
                print("[WARNING] No reviews were found for any product. Creating an empty data.csv.")
                empty_df = pd.DataFrame(columns=["Product Name", "Product Link", "Comment"])
                empty_df.to_csv("data.csv", index=False)
                return empty_df
                
        except Exception as e:
            try:
                self.driver.quit()
            except:
                pass
            print("=========================================")
            print("SCRAPER REAL ERROR:", e)
            print("=========================================")
            raise CustomException(e, sys)