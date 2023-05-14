
from replit import db
import json
from typing import Union
from models import PlaceModel, EventModel


def add_favorite(username, favorite_data: Union[EventModel, PlaceModel], playlist=None):
    user_key = f"user-{username}-favorites"
    favorites = json.loads(db.get(user_key, "{}"))  # Get current favorites or an empty dict

    # Validate favorite_data against the EventModel or PlaceModel
    if isinstance(favorite_data, EventModel):
        favorite_data = favorite_data.dict()
    elif isinstance(favorite_data, PlaceModel):
        favorite_data = favorite_data.dict()

    print("----> data:", favorite_data)
    favorite_key = favorite_data['name']
    # Add the favorite data to the user's favorites
    favorites[favorite_key] = favorite_data

    # If a playlist is specified, add the favorite to the playlist as well
    if playlist:
        if 'playlists' not in favorites:
            favorites['playlists'] = {}
        if playlist not in favorites['playlists']:
            favorites['playlists'][playlist] = []
        favorites['playlists'][playlist].append(favorite_key)

    # Update the user's favorites in the database
    db[user_key] = json.dumps(favorites)

def remove_favorite(username, favorite_key, playlist=None):
    user_key = f"user-{username}-favorites"
    favorites = json.loads(db.get(user_key, "{}"))

    # Remove the favorite data from the user's favorites
    if favorite_key in favorites:
        del favorites[favorite_key]

    # If a playlist is specified, remove the favorite from the playlist as well
    if playlist and 'playlists' in favorites and playlist in favorites['playlists']:
        favorites['playlists'][playlist].remove(favorite_key)

    # Update the user's favorites in the database
    db[user_key] = json.dumps(favorites)

def list_favorites(username, playlist=None):
    user_key = f"user-{username}-favorites"
    favorites = json.loads(db.get(user_key, "{}"))

    # If a playlist is specified, return only the favorites in that playlist
    if playlist and 'playlists' in favorites and playlist in favorites['playlists']:
        return {key: favorites[key] for key in favorites['playlists'][playlist]}

    # Otherwise, return all favorites
    return favorites

def clear_favorites(username):
    user_key = f"user-{username}-favorites"
    if user_key in db:
        del db[user_key]
