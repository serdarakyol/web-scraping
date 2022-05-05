from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import time
import json

from bs4 import BeautifulSoup
# https://www.planetahuerto.es/buscador?q=levadura%20nutricional
class Extract:
    def __init__(self) -> None:
        self.product_name:str
        self.base_url:str
        self.website = str
        self.driver_path = Service("/home/ak/Downloads/chromedriver")
        #self.driver = webdriver.Chrome(service=self.driver_path)

    def refactor_product_name(self) -> str:
        product_name = self.product_name.lower()
        product_name = product_name.split(" ")
        if len(product_name) == 1:
            return product_name[0]
        else:
            name:str = ""
            # process for Naturitas
            if self.website == "naturitas":
                for product in product_name:
                    name = name + product + "+"
                return name[:-1]

            # process for Planeto
            else:
                for product in product_name:
                    name = name + product + "%20"
                return name[:-1]
    
    def calculate_price_per_module(self, price:float, weight:float) -> float:
        return round(((price * 1000) / weight), 2)

    def extract_naturitas(self):
        naturitas_url = self.base_url + self.refactor_product_name()
        driver = webdriver.Chrome(service=self.driver_path)
        driver.get(naturitas_url)
        time.sleep(2)
        selenium_data = driver.find_elements(by=By.CSS_SELECTOR, value='#df-results__embedded > form')
        products:object = []
        for datum in selenium_data:
            temp = {
                "price": float,
                "product_name": str,
                "brand": str,
                "ppu": str,
                "weight": str
            }
            # convert selenium object to html for parse in bs4
            elementHTML = datum.get_attribute('outerHTML')
            elementSoup = BeautifulSoup(elementHTML,'html.parser')

            #extract brand
            brand = elementSoup.find("div", {"class": "df-card__brand product-item-brand"})
            temp["brand"] = brand.text

            # extract product name
            product_name = elementSoup.find("div", {"class": "df-card__title product-item-name"})
            temp["product_name"] = product_name.text

            
            
            # extract price
            price = elementSoup.find("span", {"class": "df-card__price"})
            price = price.text.replace("€", "")
            price = price.replace(",", ".")
            price = float(price.strip())
            temp["price"] = price

            # extract weight
            weight_str = elementSoup.find("div", {"class": "df-card__presentation"})
            temp["weight"] = weight_str.text
            weight = float(weight_str.text.split(" ")[0])
            selector = weight_str.text.split(" ")[1]
            if selector == 'gr':
                price = price/1000
            elif selector == 'kg':
                weight = weight * 1000
            temp["ppu"] = self.calculate_price_per_module(price=price, weight=weight)
            
            products.append(temp)
        products = sorted(products, key=lambda x: x['ppu'])
        driver.close()
        return products

    def extract_planeto(self):
        #planeto_url = self.base_url + self.refactor_product_name()
        driver = webdriver.Chrome(service=self.driver_path)
        driver.get(self.base_url)
        time.sleep(2)
        # click cookies disagree button
        disagree_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="didomi-notice-disagree-button"]'))
        )
        disagree_button.click()

        search_box = driver.find_element(by=By.XPATH, value='//*[@id="search"]')
        
        search_box.send_keys("Levadura nutricional")
        time.sleep(2)
        selenium_data = driver.find_elements(by=By.CSS_SELECTOR, value='#df-results__embedded > a')

        products:object = []
        for datum in selenium_data:
            temp = {
                "price": float,
                "product_name": str,
                "price_per_kg": str
            }
            elementHTML = datum.get_attribute('outerHTML')
            elementSoup = BeautifulSoup(elementHTML,'html.parser')
            
            product_name = elementSoup.find("div", {"class": "h-10 overflow-hidden text-base font-bold leading-tight"})
            temp["product_name"] = product_name.text

            price = elementSoup.find("div", {"class": "text-xl font-bold text-black"})
            price = price.text.replace("\u20ac", "").strip()
            temp["price"] = price

            price_per_kg = elementSoup.find("span", {"class": "mt-1 text-xs font-bold text-gray-500"})
            if price_per_kg is not None:
                temp["price_per_kg"] = price_per_kg.text
            else:
                temp["price_per_kg"] = "Unknown"

            products.append(temp)
        products = sorted(products, key=lambda x: x['price'])
        driver.close()
        return products

    def extract(self, product_name:str, base_url:str):
        self.product_name = product_name
        self.base_url = base_url
        self.website = base_url.split(".")[1].lower()

        if self.website == "naturitas":
            results = self.extract_naturitas()
        else:
            results = self.extract_planeto()

        return results
#https://www.naturitas.es/catalogsearch/result/?q=
#https://www.planetahuerto.es/
extractor = Extract()
planeta_list = extractor.extract(product_name="Levadura nutricional", base_url="https://www.planetahuerto.es/")
planeta_list = json.dumps(planeta_list, indent=2, ensure_ascii=False)

naturitas_list = extractor.extract(product_name="Levadura nutricional", base_url="https://www.naturitas.es/catalogsearch/result/?q=")
naturitas_list = json.dumps(naturitas_list, indent=2, ensure_ascii=False)

print(naturitas_list)
