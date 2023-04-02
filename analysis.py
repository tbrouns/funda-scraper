import json
import glob
import numpy as np
import os
from sklearn.linear_model import LinearRegression

json_dir = "./output"
json_path_list = sorted(glob.glob(os.path.join(json_dir, "*.json")))
result_dict = {}

for json_path in json_path_list:

    try:
        with open(json_path) as file:
            json_dict = json.load(file)
        for entry in json_dict:
            result_dict[entry["url"]] = entry
    except:
        print(f"Probably empty: {json_path}")


def convert_to_float(value):
    if value is not None and isinstance(value, str) and value.isdigit():
        value = float(value)
    elif isinstance(value, int):
        value = float(value)
    else:
        value = None
    return value


def convert_field_to_float(entry, field):
    value = convert_to_float(entry[field])
    return value


def get_backyard_area(entry):
    backyard_area = entry.get("backyard_area")
    if backyard_area is None or backyard_area == "unknown":
        living_area = entry.get("living_area")
        plot_size = entry.get("plot_size")
        living_area = convert_to_float(living_area)
        plot_size = convert_to_float(plot_size)
        if living_area is not None and plot_size is not None:
            backyard_area = plot_size - living_area
        elif backyard_area == "unknown":
            backyard_area = 0.0
    backyard_area = convert_to_float(backyard_area)
    return backyard_area


def convert_energy_label(entry):
    energy_label = entry.get("energy_label")
    energy_labels = ["A++++", "A+++", "A++", "A+", "A", "B", "C", "D", "E", "F", "G"]
    index = np.nonzero(energy_label == np.array(energy_labels))[0]
    if len(index) > 0:
        energy_label = float(index[0])
    else:
        if energy_label is not None and energy_label != "unknown":
            print(f"Unknown label: {energy_label}")
        energy_label = None
    return energy_label


house_prices = []
features = []

for key in result_dict.keys():

    entry = result_dict[key]

    price = convert_field_to_float(entry, "price")
    year_built = convert_field_to_float(entry, "year_built")
    living_area = convert_field_to_float(entry, "living_area")
    energy_label = convert_energy_label(entry)
    backyard_area = get_backyard_area(entry)
    rooms = convert_field_to_float(entry, "rooms")

    if (
        price is not None
        and year_built is not None
        and living_area is not None
        and backyard_area is not None
        and energy_label is not None
        and rooms is not None
    ):
        features.append([year_built, living_area, backyard_area, energy_label, rooms])
        house_prices.append(price)

y = np.array(house_prices)
X = np.array(features)

reg = LinearRegression().fit(X, y)
reg.predict(np.array([[2004, 90, 0, 3]]))
