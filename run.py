from datetime import datetime
import os
import subprocess

output_dir = "./output"

with open("towns.txt") as f:
    lines = f.readlines()
towns = [line.strip() for line in lines]

os.makedirs(output_dir, exist_ok=True)
for town in towns:
    date = datetime.date(datetime.now())
    town_argument = "town=" + town
    output_file = "{town}_{date}.json".format(town=town, date=date)
    output_path = os.path.join(output_dir, output_file)
    subprocess.run(
        [
            "scrapy",
            "crawl",
            "funda_spider",
            "-a",
            town_argument,
            "-a",
            "range_max=10",
            "-o",
            output_path,
        ]
    )
