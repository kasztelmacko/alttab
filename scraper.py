from firecrawl.firecrawl import FirecrawlApp

from pydantic import BaseModel, Field
from typing import List, Type, Any

import polars as pl

from dotenv import load_dotenv
import os

load_dotenv()


class Item:
    def __init__(self, item_attributes: List[str], data_types: List[Type]):
        if len(item_attributes) != len(data_types):
            raise ValueError("The lengths of item attributes and data types must match.")
        
        self.item_attributes = item_attributes
        self.data_types = data_types
        self.ItemClass = self.create_item_model()
    
    def create_item_model(self):
        annotations = {col: dtype for col, dtype in zip(self.item_attributes, self.data_types)}
        fields = {
            col: Field(description=col)
            for col in self.item_attributes
        }
        Item = type("Item", (BaseModel,), {"__annotations__": annotations, **fields})
        return Item


def main(item_attributes: List[str], data_types: List[Type], max_items: int, url: str):
    app = FirecrawlApp(os.getenv("FIRECRAWL_API_KEY"))

    item_model_instance = Item(item_attributes, data_types)
    ItemClass = item_model_instance.ItemClass
    
    class DynamicItemSchema(BaseModel):
        items: List[ItemClass] = Field(..., max_items=max_items, description="List of products")
    
    data = app.scrape_url(url, {
        'formats': ['extract'],
        'extract': {
            'schema': DynamicItemSchema.model_json_schema()
        }
    })
    
    items = data["extract"]["items"]
    df = pl.DataFrame(items)
    df.write_csv("items.csv")
    print(df)
    return df

if __name__ == "__main__":
    item_attributes = ["item_name", "item_price"]
    data_types = [str, float]
    max_items = 24
    url = "https://sklepbiegacza.pl/menu/meskie/obuwie"

    main(item_attributes, data_types, max_items, url)