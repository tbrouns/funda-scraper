from datetime import datetime, timedelta
import numpy as np
import re
import scrapy
from scrapy.linkextractors import LinkExtractor
from funda.items import FundaItem
import logging


class FundaSpider(scrapy.Spider):

    name = "funda_spider"
    allowed_domains = ["funda.nl"]

    def __init__(self, town="amsterdam", range_max=300):
        self.start_urls = [
            "https://www.funda.nl/koop/%s/p%s/" % (town, page_number)
            for page_number in range(1, int(range_max))
        ]
        self.base_url = "https://www.funda.nl/koop/%s/" % town
        self.le1 = LinkExtractor(allow=r"%s+(huis|appartement)-\d{8}" % self.base_url)
        self.current_date = datetime.today()

    def parse(self, response):
        links = self.le1.extract_links(response)
        for link in links:
            if link.url.count("/") == 6 and link.url.endswith("/"):
                item = FundaItem()
                item["url"] = link.url
                if re.search(r"/appartement-", link.url):
                    item["property_type"] = "apartment"
                elif re.search(r"/huis-", link.url):
                    item["property_type"] = "house"
                yield scrapy.Request(
                    link.url, callback=self.parse_dir_contents, meta={"item": item}
                )

    def parse_dir_contents(self, response):
        new_item = response.request.meta["item"]
        title = response.xpath("//title/text()").extract()[0]
        print("========== title ===========")
        print(title)
        postal_code = self.get_postal_code(title)
        town = self.get_town(title)
        address = re.findall(r"te koop: (.*) \d{4}", title)[0]
        price = self.get_price(response)
        year_built = self.constructionYear(response)
        living_area = self.get_area(response, "Wonen")
        plot_size = self.get_area(response, "Perceel")
        if living_area == "unknown":  # Different formatting
            living_area, plot_size = self.get_area_2(response)
        backyard_area = self.get_area(response, "Achtertuin")
        sideyard_area = self.get_area(response, "Zijtuin")
        if backyard_area != "unknown" and sideyard_area != "unknown":
            yard_area = str(float(backyard_area) + float(sideyard_area))
        elif backyard_area == "unknown" and sideyard_area != "unknown":
            yard_area = sideyard_area
        elif backyard_area != "unknown" and sideyard_area == "unknown":
            yard_area = backyard_area
        else:
            yard_area = "unknown"
        rooms, bedrooms = self.get_rooms(response)
        bathrooms, toilets = self.get_bathrooms(response)
        energy_label = self.get_energy_label(response)
        posting_date = self.get_posting_date(response)

        new_item["postal_code"] = postal_code
        new_item["address"] = address
        new_item["price"] = price
        new_item["year_built"] = year_built
        new_item["living_area"] = living_area
        new_item["plot_size"] = plot_size
        new_item["backyard_area"] = yard_area
        new_item["energy_label"] = energy_label
        new_item["rooms"] = rooms
        new_item["bedrooms"] = bedrooms
        new_item["bathrooms"] = bathrooms
        new_item["toilets"] = toilets
        new_item["town"] = town
        new_item["posting_date"] = posting_date
        yield new_item

    def get_price(self, response):
        price_dd = response.xpath(
            './/strong[@class="object-header__price"]/text()'
        ).extract()[0]
        if len(price_dd) > 0:
            price = "".join(re.findall(r"\d+", price_dd)).replace(".", "")
        else:
            price = "unknown"
        return price

    def get_postal_code(self, title):
        postal_code = re.search(r"\d{4} [A-Z]{2}", title)
        if postal_code is not None:
            postal_code = postal_code.group(0)
        else:
            postal_code = "unknown"
        return postal_code

    def get_town(self, title):
        town = re.search(r"\d{4} [A-Z]{2} \w+[\s-]\w*", title)
        if town is not None:
            town = town.group(0).split()[2:]
            town = " ".join(town)
        else:
            town = "unknown"
        return town

    def get_entry_list(self, response, name):
        xpath = "//dt[text()='" + name + "']/following-sibling::dd[1]/span/text()"
        entry = response.xpath(xpath).extract()
        return entry

    def get_entry(self, response, name):
        entry = []
        entry_list = self.get_entry_list(response, name)
        if len(entry_list) > 0:
            entry = entry_list[0]
        return entry

    def get_posting_date(self, response):
        date = "unknown"
        entry = self.get_entry(response, "Aangeboden sinds")
        result = re.findall(r"\d+ [a-z]+ \d{4}", entry)
        if len(result) > 0:
            maanden = [
                "januari",
                "februari",
                "maart",
                "april",
                "mei",
                "juni",
                "juli",
                "augustus",
                "september",
                "oktober",
                "november",
                "december",
            ]
            result = result[0].split()
            if len(result) == 3:
                day, month, year = result
                index = np.nonzero(np.array(maanden) == month)[0]
                if len(index) > 0:
                    month = index[0] + 1
                    date = datetime(int(year), month, int(day))
        else:
            days_to_subtract = None
            result = re.findall(r".+?(?= weken)", entry)
            if len(result) == 1:
                days_to_subtract = 7 * int(result[0])
            else:
                result = re.findall(r".+?(?= maanden)", entry)
                if len(result) == 1:
                    result = result[0]
                    result = re.findall(r"\d", result)[0]
                    days_to_subtract = 30 * int(result)
                else:
                    result = re.findall(r"Vandaag", entry)
                    if len(result) == 1:
                        date = self.current_date
            if days_to_subtract is not None:
                date = self.current_date - timedelta(days=days_to_subtract)
        return date

    def get_year(self, string):
        return re.findall(r"\d{4}", string[0])

    def constructionYear(self, response):
        construction_year = "unknown"
        singleYear = self.get_entry_list(response, "Bouwjaar")
        period = self.get_entry_list(response, "Bouwperiode")
        if len(singleYear) > 0:
            year = self.get_year(singleYear)
            if len(year) == 1:
                construction_year = year[0]
        elif len(period) > 0:
            period = self.get_year(period)
            if len(period) == 2:
                period = [int(year) for year in period]
                construction_year = int(np.mean(period))
        return construction_year

    def get_area(self, response, name):
        area_dd = self.get_entry(response, name)
        if len(area_dd) > 0:
            area = re.findall(r"[\d\.]+", area_dd)[0]
            area = area.replace(".", "")
        else:
            area = "unknown"
        return area

    def get_area_2(self, response):
        area_dd = self.get_entry(response, "Oppervlakte")
        if len(area_dd) > 0:
            area = re.findall(r"[\d\.]+", area_dd)
            if len(area) == 2:
                living_area, plot_size = area
                plot_size = plot_size.replace(".", "")
            else:
                living_area = area[0]
                plot_size = "unknown"
            living_area = living_area.replace(".", "")
        else:
            living_area = "unknown"
            plot_size = "unknown"
        return living_area, plot_size

    def get_rooms(self, response):
        rooms = self.get_entry(response, name="Aantal kamers")
        bedrooms = "unknown"
        if len(rooms) > 0:
            number_of_rooms = re.findall(r"\d+", rooms)
            if len(number_of_rooms) == 2:
                rooms, bedrooms = number_of_rooms
            else:
                rooms = number_of_rooms
        else:
            rooms = "unknown"
        return rooms, bedrooms

    def get_bathrooms(self, response):
        bathrooms = self.get_entry(response, name="Aantal badkamers")
        if len(bathrooms) > 0:
            number_of_rooms = re.findall(r"\d+", bathrooms)
            if len(number_of_rooms) == 2:
                bathrooms, toilets = number_of_rooms
            else:
                bathrooms = "1"
                toilets = "0"
        else:
            bathrooms = "unknown"
            toilets = "unknown"
        return bathrooms, toilets

    def get_energy_label(self, response):
        energy_label = self.get_entry(response, "Energielabel")
        if len(energy_label) > 0:
            energy_label = energy_label.strip()
        else:
            energy_label = "unknown"
        return energy_label.strip()
