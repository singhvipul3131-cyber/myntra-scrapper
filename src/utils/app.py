import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import streamlit as st
from src.cloud_io import MongoIO
from src.constants import SESSION_PRODUCT_KEY
from src.scrapper.scrape import ScrapeReviews

st.set_page_config("myntra-review-scrapper")
st.title("Myntra Review Scrapper")
st.session_state["data"] = False


def form_input():
    product = st.text_input("Search Products")
    st.session_state[SESSION_PRODUCT_KEY] = product
    no_of_products = st.number_input(
        "No of products to search", step=1, min_value=1
    )

    if st.button("Scrape Reviews"):
        scrapper = ScrapeReviews(
            product_name=product,
            no_of_products=int(no_of_products)
        )
        scrapped_data = scrapper.get_review_data()
       # --- app.py ke andar check lagayein ---
       # --- app.py ke andar check lagayein ---
        if scrapped_data is not None and not scrapped_data.empty:
            # --- YAHAN BADLAV KIYA HAI (MongoIO ke aage () lagaya hai) ---
            mongo_db = MongoIO()
            mongo_db.store_reviews(product_name=product, reviews=scrapped_data)
            
            # YEH LINE BILKUL MONGO_DB KE NICHE EK HI LINE MEIN HONI CHAHIYE
            st.success("Bhai, Data MongoDB mein safely save ho gaya hai! 🔥")
             

if __name__ == "__main__":
    data = form_input()