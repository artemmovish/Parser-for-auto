import re
import csv
import time

from playwright.sync_api import sync_playwright  # для автоматизации браузера


class Attribut():
    def __init__(self, category, name, value):
        self.category = category
        self.name = name
        self.value = value

class Car:
    def __init__(self, main_category="None", category="None", name="None", model="None",
                 price=0, image="None", images=None, attributes=None):
        self._MAIN_CATEGORY_ = main_category
        self._CATEGORY_ = category
        self._NAME_ = name
        self._MODEL_ = model
        self._PRICE_ = price
        self._IMAGE_ = image
        self._IMAGES_ = images if images is not None else []
        self._ATTRIBUTES_ = attributes if attributes is not None else []

    def display_info(self):
        """Отображает информацию о машине"""
        info = [
            "=== Информация об автомобиле ===",
            f"Основная категория: {self._MAIN_CATEGORY_}",
            f"Категория: {self._CATEGORY_}",
            f"Марка: {self._NAME_}",
            f"Модель: {self._MODEL_}",
            f"Цена: {self._PRICE_}",
            f"Главное изображение: {self._IMAGE_}",
            "\n=== Дополнительные изображения ==="
        ]

        if not self._IMAGES_:
            info.append("  Нет дополнительных изображений")
        else:
            for i, img in enumerate(self._IMAGES_, 1):
                info.append(f"  Изображение {i}: {img}")

        info.append("\n=== Атрибуты ===")

        if not self._ATTRIBUTES_:
            info.append("  Нет атрибутов")
        else:
            for attr in self._ATTRIBUTES_:
                info.append(f"  [{attr.category}] {attr.name}: {attr.value}")

        print('\n'.join(info))



class Parser():

    def __init__(self, baseUrl):
        self._BaseUrl = baseUrl
        self.cars = []

    def write_cars_to_csv(self, filename):
        """Создание пустой таблицы .csv"""
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=';')

            writer.writerow([
                "_MAIN_CATEGORY_",
                "_CATEGORY_",
                "_NAME_",
                "_MODEL_",
                "_PRICE_",
                "_IMAGE_",
                "_IMAGES_",
                "_ATTRIBUTES_"
            ])

    def append_cars_to_csv(self, filename):
        """Запись автомобилей в .csv"""
        with open(filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=';')

            for car in self.cars:
                attributes_str = "\n".join(
                    f"{attr.category}|{attr.name}|{attr.value}"
                    for attr in car._ATTRIBUTES_
                )
                additional_images = ",".join(car._IMAGES_)

                writer.writerow([
                    car._MAIN_CATEGORY_,
                    car._CATEGORY_,
                    car._NAME_,
                    car._MODEL_,
                    car._PRICE_,
                    car._IMAGE_,
                    additional_images,
                    attributes_str
                ])

    def navigate_to_car(self, car_element):
        """Переходит на страницу автомобиля из элемента списка, открывая её в новой вкладке.
    После загрузки страницы запускает парсинг и закрывает вкладку."""
        link = car_element.query_selector("a.text-decoration-none.btn")
        href = link.get_attribute("href")
        print(f"Найдена ссылка: {href}")

        with self.page.context.expect_page() as new_page_info:
            link.click(button="middle")

        self.car_page = new_page_info.value

        self.car_page.wait_for_load_state()

        self.parse_car()

        self.car_page.close()

    def extract_uid(self):
        """Извлекает id автомобиля с адреса страницы """
        # чуть позже заметил, что id есть и в html, решил пока не изменять
        match = re.search(r'uid-(\d+)', self.car_page.url)
        if match:
            return match.group(1)
        return "None"

    def extract_price(self):
        """Извлекает цену автомобиля со страницы"""
        price_text = self.car_page.locator('[itemprop="price"]').inner_text()
        clean_price = re.sub(r'[^\d,.]', '', price_text)

        return int(clean_price)

    def extract_images(self):
        """Извлекает изображения со страницы"""
        list_image = self.car_page.query_selector_all('img.w-100.rounded.img-fluid.swiper-car-view')

        list_src = []
        for img in list_image:
            list_src.append(img.get_attribute('src'))

        return list_src

    def extract_attributes_tech_spec(self):
        """Извлекает технические характеристики автомобиля со страницы"""
        names = self.car_page.query_selector_all("div.col-6.text-secondary")
        values = self.car_page.query_selector_all("div.col-6:not(.text-secondary)")

        list_attribut = []

        for name, value in zip(names, values):
            name_text = name.text_content().strip()
            value_text = value.text_content().strip()

            if name_text and value_text:
                list_attribut.append(Attribut("Общие", name_text, value_text))

        return list_attribut[:-1] if len(list_attribut) > 2 else list_attribut

    def extract_attributes_options(self):
        """Извлекает опции автомобиля со страницы"""
        all_options = self.car_page.query_selector_all("span.ms-2:not(.fs-6)")

        list_attribut = []

        for option in all_options:
            is_available = "text-secondary" not in option.get_attribute("class")
            option_text = option.text_content().strip()

            if option_text:
                status = "Есть" if is_available else "Нет"
                list_attribut.append(Attribut("Опции", option_text, status))

        return list_attribut

    def extract_attributs(self):
        """Извлекает атрибуты автомобиля со страницы"""
        list_attribut = self.extract_attributes_tech_spec()
        list_attribut.extend(self.extract_attributes_options())

        return  list_attribut

    def parse_car(self):
        """Извлекает данные автомобиля со страницы"""
        category = self.car_page.query_selector_all("li.breadcrumb-item")[1].query_selector("span").text_content()
        name = self.car_page.query_selector("h1.mb-0").inner_text()
        model = self.extract_uid()
        price = self.extract_price()
        images = self.extract_images()
        atributs = self.extract_attributs()

        car = Car(category, category, name, model, price, images[0], images[1:], atributs)
        #car.display_info()

        self.cars.append(car)

    def parse(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            self.page = browser.new_page()
            self.page.goto(self._BaseUrl)

            self.write_cars_to_csv("cars.csv")

            while True:
                self.page.wait_for_selector("div.row.row-cols-1")
                list_car = self.page.query_selector_all("div.card.car-height")

                for i, car in enumerate(list_car, 1):
                    self.navigate_to_car(car)
                    time.sleep(1)

                self.append_cars_to_csv("cars.csv")

                self.cars = []

                try:
                    self.page.click('i.fa-solid.fa-angles-right')
                except:
                    break



            browser.close()

parser = Parser("https://carskorea.shop/")

parser.parse()