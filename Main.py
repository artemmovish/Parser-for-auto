import re  # для работы с регулярными выражениями
from itertools import count
import csv
from playwright.sync_api import sync_playwright  # для автоматизации браузера
import json  # для работы с JSON
import time  # для работы с временными задержками

from unicodedata import category

class Attribut():
    def __init__(self, category, name, value):
        self.category = category
        self.name = name
        self.value = value

class Car:
    def __init__(self, main_category="None", category="None", name="None", model="None",
                 price="None", image="None", images=None, attributes=None):
        self._MAIN_CATEGORY_ = main_category
        self._CATEGORY_ = category
        self._NAME_ = name
        self._MODEL_ = model
        self._PRICE_ = price
        self._IMAGE_ = image
        self._IMAGES_ = images if images is not None else []
        self._ATTRIBUTES_ = attributes if attributes is not None else []

    def display_info(self):
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

        # Добавляем изображения
        if not self._IMAGES_:
            info.append("  Нет дополнительных изображений")
        else:
            for i, img in enumerate(self._IMAGES_, 1):
                info.append(f"  Изображение {i}: {img}")

        info.append("\n=== Атрибуты ===")

        # Добавляем атрибуты
        if not self._ATTRIBUTES_:
            info.append("  Нет атрибутов")
        else:
            for attr in self._ATTRIBUTES_:
                info.append(f"  [{attr.category}] {attr.name}: {attr.value}")

        # Выводим всю информацию
        print('\n'.join(info))



class Parser():

    def __init__(self, baseUrl):
        self._BaseUrl = baseUrl
        self.cars = []

    def write_cars_to_csv(cars, filename):
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # Записываем заголовки
            headers = [
                "_MAIN_CATEGORY_",
                "_CATEGORY_",
                "_NAME_",
                "_MODEL_",
                "_PRICE_",
                "_IMAGE_",
                "_IMAGES_",  # Список изображений будет объединён в строку
                "_ATTRIBUTES_"  # Атрибуты будут сериализованы
            ]
            writer.writerow(headers)

            # Записываем каждую машину
            for car in cars:
                # Сериализуем список изображений в строку (например, через разделитель '|')
                images_str = ";".join(car._IMAGES_)

                # Сериализуем атрибуты в строку (например, в формате "категория:название:значение")
                attributes_str = "\n".join(
                    f"{attr.category}|{attr.name}:{attr.value}"
                    for attr in car._ATTRIBUTES_
                )

                # Формируем строку CSV
                row = [
                    car._MAIN_CATEGORY_,
                    car._CATEGORY_,
                    car._NAME_,
                    car._MODEL_,
                    car._PRICE_,
                    car._IMAGE_,
                    images_str,
                    attributes_str,
                ]
                writer.writerow(row)

    def navigate_to_car(self, car_element):
        link = car_element.query_selector("a.text-decoration-none.btn")
        with self.page.expect_navigation():
            href = link.get_attribute("href")
            print(f"Найдена ссылка: {href}")
            link.click()
            self.parse_car()

    def extract_uid(self, url):
        match = re.search(r'uid-(\d+)', url)
        if match:
            return match.group(1)
        return "None"

    def extrat_price(self):
        price_text = self.page.locator('[itemprop="price"]').inner_text()
        clean_price = price_text.replace('&nbsp;', '').replace(' ', '')
        # чуть позже заметил, что id есть и в html, решил пока не изменять
        return clean_price

    def extrat_images(self):
        list_image = self.page.query_selector_all('img.w-100.rounded.img-fluid.swiper-car-view')

        list_src = []
        for img in list_image:
            list_src.append(img.get_attribute('src'))

        return list_src

    def extrar_attributs_tech_spec(self):
        names = self.page.query_selector_all("div.col-6.text-secondary")
        values = self.page.query_selector_all("div.col-6")

        list_Attribut = []
        for name, value in zip(names, values):
            list_Attribut.append(Attribut("Общие", name.text_content(), value.text_content()))

        return list_Attribut[0:(len(list_Attribut) - 2)]

    # def check_option(self, name):
    #     has_close_icon = name.query_selector('i.fa.fa-close').count() > 0
    #     return not has_close_icon
    #
    # def extrar_attributs_Options(self):
    #     names = self.page.query_selector_all("ms-2 text-secondary")
    #
    #     list_Attribut = []
    #     for name in names:
    #         list_Attribut.append(Attribut("Общие", name.text_content(), self.check_option(name)))
    #
    #     return list_Attribut

    def extrar_attributs_Options(self):
        names_true = self.page.query_selector_all("span.ms-2")
        names_false = self.page.query_selector_all("span.ms-2.text-secondary")

        list_Attribut = []
        for name_true in names_true:
            list_Attribut.append(Attribut("Общие", name_true.text_content(), "Есть"))

        for name_false in names_false:
            list_Attribut.append(Attribut("Общие", name_false.text_content(), "Нет"))

        return list_Attribut

    def extrar_attributs(self):
        list_attribut = self.extrar_attributs_tech_spec()
        list_attribut.extend(self.extrar_attributs_Options())

        return  list_attribut

    def parse_car(self):
        category = self.page.query_selector_all("li.breadcrumb-item")[1].query_selector("span").text_content()
        name = self.page.query_selector("h1.mb-0").inner_text()
        model = self.extract_uid(self.page.url)
        price = self.extrat_price()
        images = self.extrat_images()
        atributs = self.extrar_attributs()

        self.cars.append(Car(category, category, name, model, price, images[0], images[1:], atributs))
        self.page.go_back()

    def convertToCar(self):
        ...

    def parse(self):
        # Запускаем Playwright в синхронном режиме
        with sync_playwright() as p:
            # Запускаем браузер Chromium в режиме с отображением (headless=False)
            browser = p.chromium.launch(headless=False)
            self.page = browser.new_page()  # Создаем новую страницу
            self.page.goto(self._BaseUrl)  # Переходим на сайт

            self.page.wait_for_selector("div.row.row-cols-1")

            list_car = self.page.query_selector_all("div.card.car-height")

            for car in list_car:
                self.navigate_to_car(car)
                break

            self.cars[0].display_info()

            time.sleep(10)
            browser.close()  # Закрываем браузер

parser = Parser("https://carskorea.shop/?fbclid=IwY2xjawJQ59xleHRuA2FlbQIxMAABHa-eoVAdnFCp_LmrOG1l_giz9YUibfIygC-VInsGjkgYr83mcEbRBxwHqQ_aem_DqRwVuO5PhySKu4j7WYPUg")

parser.parse()