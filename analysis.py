import json
import glob
import numpy as np
import os
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt


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
            # backyard_area = plot_size - living_area / 2
            backyard_area = entry["plot_size"]
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

    # if (
    #     # entry["town"] != "Helvoirt"
    #     entry["town"] != "Sint-Michielsgestel"
    #     # and entry["town"] != "Boxtel"
    #     # and entry["town"] != "Haaren"
    # ):
    #     continue

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

# print("Aantal huizen:")
# print(np.sum((np.array(features)[:, 1] > 120) * (np.array(features)[:, 2] > 300) * (np.array(house_prices) < 700000)))
# print()

y = np.array(house_prices)
X = np.array(features)

reg = LinearRegression().fit(X, y)
# year_built, living_area, backyard_area (= plot_size), energy_label, rooms
# energy_labels = ["A++++", "A+++", "A++", "A+", "A", "B", "C", "D", "E", "F", "G"]
x = np.array([[1984, 140, 368, 4, 4]])  # Helvoirt
x = np.array([[2012, 160, 320, 4, 3]])  # De Goudplevier 14
x = np.array([[1975, 177, 320, 4, 4]])  # Sint Jorisstraat 29
x = np.array([[1988, 163, 499, 4, 6]])  # Krommeweg 10
# y_pred = reg.predict(np.concatenate((x0, x1)))
y_pred = reg.predict(x)
print(y_pred.astype(int))

# # Creating figure
# fig = plt.figure(figsize=(10, 7))
# ax = plt.axes(projection="3d")
#
# # Creating plot
# ax.scatter3D(X[:, 0], X[:, 1], y, color="green", alpha=0.5, s=2)
# ax.scatter3D(x0[:, 0], x0[:, 1], 595000, color="red")
# ax.scatter3D(x1[:, 0], x1[:, 1], 595000, color="blue")
# ax.set_xlim([1900, 2030])
# ax.set_ylim([0, 500])
# ax.set_zlim([0, 1e6])
# plt.show()
