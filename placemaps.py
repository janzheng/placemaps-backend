import json
from replit import db


class Event:

  def __init__(self, name, location, date, time, description):
    self.name = name
    self.location = location
    self.date = date
    self.time = time
    self.description = description


class Place:

  def __init__(self,
               name,
               location,
               category,
               description,
               highlights,
               rating,
               external_links=None):
    self.name = name
    self.location = location
    self.category = category
    self.description = description
    self.highlights = highlights
    self.rating = rating
    self.external_links = external_links if external_links else []


class Place:

  def __init__(self,
               name,
               address,
               category,
               description,
               highlights,
               rating,
               external_links=None):
    self.name = name
    self.address = address
    self.category = category
    self.description = description
    self.highlights = highlights
    self.rating = rating
    self.external_links = external_links if external_links else []


def replace_db(json_data):
  # Clear the current database
  for key in db.keys():
    del db[key]

  # Add the new data
  for key, value in json_data:
    print("kv:", key, value, json_data)
    db[key] = json.dumps(value)


def replace_db_list(json_data_list):
  # Clear the current database
  for key in db.keys():
    del db[key]

  # Add the new data
  for json_data in json_data_list:
    db[json_data["key"]] = json.dumps(json_data["data"])


def print_db():
  print("The DB contains:\n", [{
    "key": key,
    "data": json.loads(db[key])
  } for key in db.keys()])


def list_db():
  return [{"key": key, "data": json.loads(db[key])} for key in db.keys()]


def load_json_file(file_path):
  with open(file_path) as json_file:
    data = json.load(json_file)
  print('load_json_file:', data[0])
  return data


def add_example_data():
  # Creating some example events
  event1 = Event("Vivid Sydney", "Sydney", "2023-06-25", "18:00",
                 "Light, Music and Ideas Festival")
  event2 = Event("Sydney Film Festival", "Sydney", "2023-07-05", "19:00",
                 "Film Festival")
  event3 = Event("Sydney Mardi Gras", "Sydney", "2023-02-18", "16:00",
                 "LGBTQ+ Parade and Party")

  # Converting events to JSON and adding them to the database
  db["event-Vivid Sydney"] = json.dumps(event1.__dict__)
  db["event-Sydney Film Festival"] = json.dumps(event2.__dict__)
  db["event-Sydney Mardi Gras"] = json.dumps(event3.__dict__)

  # Creating some example places
  place1 = Place(
    "Port Jackson Bay", "Sydney", "Bay",
    "Highly recommended. A harbour boat trip from Circular Quay is a highlight for any visitor to Sydney and the views of the city are stunning. It is possible to include Manly and Darling Harbour in the trip as well.",
    ["Must go", "Show 2 more"], 4.7,
    ["Wikipedia", "Fort Denison", "Shark Island"])
  place2 = Place(
    "Sydney Harbour Bridge", "Sydney", "Bridge",
    "Highly recommended. An integral part of any visit to Sydney and worth taking a drive over the bridge to the northern parts of Sydney including Manly.",
    ["Must go", "Show 2 more"], 4.8,
    ["Wikipedia", "Bridge Climb", "Pylon Lookout"])
  place3 = Place(
    "Pylon Lookout", "Sydney", "Vista point",
    "One of the ongoing tourist attractions of the bridge has been the south-east pylon, which is accessed via the pedestrian walkway across the bridge, and then a climb to the top of the pylon of about 200 steps.",
    ["Sights & Landmarks", "Show 2 more"], 4.5, ["Wikipedia", "Pylon Lookout"])
  place4 = Place(
    "The Rocks", "Sydney", "Sights & Landmarks",
    "Highly recommended. The area around The Rocks is key to any visit to Sydney with its markets, history, restaurants, shopping and much more. Also a key transport hub within the inner city.",
    ["Must go", "Show 2 more"], 4.6,
    ["Wikipedia", "The Rocks Markets", "Discovery Museum", "Cadman's Cottage"])
  place5 = Place(
    "Museum of Contemporary Art Australia", "Sydney", "Art museum",
    "Located on George Street in Sydney's The Rocks neighbourhood, the museum is solely dedicated to exhibiting, interpreting, and collecting contemporary art, from across Australia and around the world.",
    ["Museums", "Show 4 more"], 4.4, ["Wikipedia", "Official website"])

  # Converting places to JSON and adding them to the database
  db["place-Port Jackson Bay"] = json.dumps(place1.__dict__)
  db["place-Sydney Harbour Bridge"] = json.dumps(place2.__dict__)
  db["place-Pylon Lookout"] = json.dumps(place3.__dict__)
  db["place-The Rocks"] = json.dumps(place4.__dict__)
  db["place-Museum of Contemporary Art Australia"] = json.dumps(
    place5.__dict__)


def get_placemaps(type=None):
  if type is None:
    keys = [
      key for key in db.keys()
      if key.startswith('place-') or key.startswith('event-')
    ]
  else:
    keys = [key for key in db.keys() if key.startswith(f'{type}-')]

  placemaps = [json.loads(db[key]) for key in keys]
  # placemap = {key: json.loads(db[key]) for key in keys}
  print("get_placemaps:::", placemaps)
  return placemaps


def add_placemap(placemap_dict):
  if 'category' in placemap_dict:  # Assuming 'category' is unique to Place
    place = Place(**placemap_dict)
    db[f"place-{place.name}"] = json.dumps(place.__dict__)
  # elif 'date' in placemap_dict:  # Assuming 'date' is unique to Event
  #     event = Event(**placemap_dict)
  #     db[f"event-{event.name}"] = json.dumps(event.__dict__)
  else:
    print("Unable to add item to database. Unknown type.")


# add_example_data()

replace_db_list(load_json_file("./placemaps.json"))
# print_db()
# print(get_placemaps())
