import re
import scrapy
from scrapy.linkextractors import LinkExtractor
from funda.items import FundaItem
import logging

class FundaSpider(scrapy.Spider):

    name = "funda_spider"
    allowed_domains = ["funda.nl"]

    def __init__(self, place='amsterdam', range_max=300):
        self.start_urls = ["https://www.funda.nl/koop/%s/p%s/" % (place, page_number) for page_number in range(1, int(range_max))]
        self.base_url = "https://www.funda.nl/koop/%s/" % place
        self.le1 = LinkExtractor(allow=r'%s+(huis|appartement)-\d{8}' % self.base_url)

    def parse(self, response):
        links = self.le1.extract_links(response)
        for link in links:
            if link.url.count('/') == 6 and link.url.endswith('/'):
                item = FundaItem()
                item['url'] = link.url
                if re.search(r'/appartement-',link.url):
                    item['property_type'] = "apartment"
                elif re.search(r'/huis-',link.url):
                    item['property_type'] = "house"
                yield scrapy.Request(link.url, callback=self.parse_dir_contents, meta={'item': item})

    def parse_dir_contents(self, response):
        new_item = response.request.meta['item']
        title = response.xpath('//title/text()').extract()[0]
        postal_code = re.search(r'\d{4} [A-Z]{2}', title).group(0)
        city = re.search(r'\d{4} [A-Z]{2} \w+\s\w*',title).group(0).split()[2:]
        city = " ".join(city)
        address = re.findall(r'te koop: (.*) \d{4}',title)[0]
        price_dd = response.xpath('.//strong[@class="object-header__price"]/text()').extract()[0]
        price = ''.join(re.findall(r'\d+', price_dd)).replace('.','')
        year_built = self.constructionYear(response)
        living_area = self.get_area(response, "Wonen")
        plot_size = self.get_area(response, "Perceel")
        backyard_area = self.get_area(response, "Achtertuin")
        sideyard_area = self.get_area(response, "Zijtuin")
        yard_area = str(float(backyard_area) + float(sideyard_area))
        bedrooms = response.xpath("//span[contains(@title,'slaapkamer')]/following-sibling::span[1]/text()").extract()[0]
        bathrooms, toilets = self.get_bathrooms(response)
        energy_label = self.get_energy_label(response)
        new_item['postal_code'] = postal_code
        new_item['address'] = address
        new_item['price'] = price
        new_item['year_built'] = year_built
        new_item['living_area'] = living_area
        new_item['plot_size'] = plot_size
        new_item['backyard_area'] = yard_area
        new_item['energy_label'] = energy_label
        new_item['bedrooms'] = bedrooms
        new_item['bathrooms'] = bathrooms
        new_item['toilets'] = toilets
        new_item['city'] = city
        yield new_item
    
    def constructionYear(self, response):
        try:
            # Some have a single bouwjaar
            singleYear = response.xpath("//dt[text()='Bouwjaar']/following-sibling::dd/span/text()").extract()
            # Some have a period
            period = response.xpath("//dt[text()='Bouwperiode']/following-sibling::dd/span/text()").extract()
            if len(singleYear) > 0:
                # Some are built before 1906 (earliest date that Funda will let you specify)
                return re.findall(r'\d{4}', singleYear[0])[0]
            elif len(period) > 0:
                return re.findall(r'$\d{4}', period[0])[0]
            else:
                return 'unknown'
        except:
            return "Failed to parse"


    def get_entry(self, response, name):
        xpath = "//dt[text()='" + name + "']/following-sibling::dd[1]/span/text()"
        entry = response.xpath(xpath).extract()
        if len(entry) > 0:
            entry = entry[0]
        return entry

    def get_area(self, response, name):
        area_dd = self.get_entry(response, name)
        if len(area_dd) > 0:
            area = re.findall(r'[\d\.]+', area_dd)[0]
            area = area.replace(".", "")
        else:
            area = 0.0
        return area

    def get_houseType(self, response):
        pass

    def get_bathrooms(self, response):
        bathrooms = self.get_entry(response, name="Aantal badkamers")
        number_of_rooms = re.findall(r'\d+', bathrooms)
        if len(number_of_rooms) == 2:
            bathrooms, toilets = number_of_rooms
        else:
            bathrooms = 1
            toilets = 0
        return bathrooms, toilets

    def get_energy_label(self, response):
        entry = self.get_entry(response, "Energielabel")
        return entry.strip()
