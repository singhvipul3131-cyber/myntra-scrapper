import pandas as pd
from database_connect import mongo_operation as mongo
import os, sys
from src.constants import *
from src.exception import CustomException
from dotenv import load_dotenv
load_dotenv()



class MongoIO:
    mongo_ins = None

    def __init__(self):
        if MongoIO.mongo_ins is None:
            Mongo_db_url = os.getenv("MONGODB_URL_KEY")
            database_name = os.getenv("MONGODB_DATABASE_NAME")
            
            if Mongo_db_url is None:
                raise Exception(f"Environment key: MONGODB_URL_KEY is not set.")
            if database_name is None:
                raise Exception(f"Environment key: MONGODB_DATABASE_NAME is not set")
            MongoIO.mongo_ins = mongo(
                client_url= Mongo_db_url, database_name = database_name
            )
        self.mongo_ins = MongoIO.mongo_ins

    def store_reviews(self, product_name: str, reviews: pd.DataFrame):
        try:
            Collection_name = product_name.replace(" ", "_")
            self.mongo_ins.bulk_insert(reviews, Collection_name)
            
        except Exception as e:
            print(e)
            raise CustomException(e, sys)
        
    def get_revision(self, product_name: str):
        try:
            data = self.mongo_ins.find(
                collection_name = product_name.replace(" "," - ")
            )
            return data
        except Exception as e:
            raise CustomException(e, sys)