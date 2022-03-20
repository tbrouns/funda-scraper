import scrapy


class FundaItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    address = scrapy.Field()
    postal_code = scrapy.Field()
    price = scrapy.Field()
    year_built = scrapy.Field()
    living_area = scrapy.Field()
    plot_size = scrapy.Field()
    backyard_area = scrapy.Field()
    rooms = scrapy.Field()
    bedrooms = scrapy.Field()
    bathrooms = scrapy.Field()
    toilets = scrapy.Field()
    property_type = scrapy.Field()
    energy_label = scrapy.Field()
    town = scrapy.Field()
    posting_date = scrapy.Field()
    sale_date = scrapy.Field()
