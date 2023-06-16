import csv
import json

def convert_to_json_instances(input):
    with open(input, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        instances = []
        for row in reader:
            instance = {
                'region': row[0],
                'origin_lat': row[1].split("T ")[1].split("(")[1].split(")")[0].split(" ")[0],
                'origin_lon': row[1].split("T ")[1].split("(")[1].split(")")[0].split(" ")[1],
                'destination_lat': row[2].split("T ")[1].split("(")[1].split(")")[0].split(" ")[0],
                'destination_lon': row[2].split("T ")[1].split("(")[1].split(")")[0].split(" ")[1],
                'datetime': row[3],
                'datasource': row[4]
            }
            instances.append(instance)
        
    
    with open('instances.json', 'w') as f:
        json.dump(instances, f, indent=4)

convert_to_json_instances('trips.csv')