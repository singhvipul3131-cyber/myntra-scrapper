import os
import sys
import pandas as pd
import streamlit as st

# Path theek karne ke liye taaki cloud_io aur src automatic mil jayein
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_io import MongoIO
from src.constants import SESSION_PRODUCT_KEY
from src.data_report.generate_data_report import DashboardGenerator

# MongoDB connection
mongo_con = MongoIO()


def create_analysis_page(review_data: pd.DataFrame):
    if review_data is not None and not review_data.empty:
        st.dataframe(review_data)
        if st.button("Generate Analysis"):
            dashboard = DashboardGenerator(review_data)
            dashboard.display_general_info()
            dashboard.display_product_sections()
    else:
        st.warning("Bhai, is product ka koi data nahi mila database mein.")


st.title("Generate Analysis Dashboard 📊")

# Try-Except block jahan spacing ki dikkat thi
try:
    if (
        SESSION_PRODUCT_KEY in st.session_state
        and st.session_state[SESSION_PRODUCT_KEY]
    ):
        product = st.session_state[SESSION_PRODUCT_KEY]
        data = mongo_con.get_reviews(product_name=product)
        create_analysis_page(data)
    else:
        st.info(
            "⚠️ Bhai, pehle main 'app' page par jaakar koi product search aur scrape karo!"
        )
except Exception as e:
    st.error(f"Kuch gadbad hui bhai: {e}")