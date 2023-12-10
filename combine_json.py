import json
import glob
import os

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

results = {}
for url_key, entry_dict in result_dict.items():
    if entry_dict["town"] == "Best":
        result = {k: result_dict[url_key][k] for k in ["address", "postal_code", "price", "living_area", "plot_size", "rooms", "posting_date"]}
        if result["plot_size"] != "unknown" and int(result["living_area"]) > 120 and int(result["plot_size"]) > 250:
            result["living_area"] = result["living_area"].zfill(3)
            result["price"] = result["price"].zfill(7)
            results[result["address"]] = result

results = sorted(results.items(), key=lambda x: x[1]['price'], reverse=True)
print(json.dumps(results, sort_keys=True, indent=4))