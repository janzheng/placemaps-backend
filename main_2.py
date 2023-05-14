import json
from fastapi import FastAPI
from fastapi import FastAPI, Response, Request, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from models import PlaceModel, EventModel
from placemaps import get_placemaps, list_db, add_placemap

from typing import Union
import os
from dotenv import load_dotenv

load_dotenv('.env')

# app = Quart(__name__)
app = FastAPI()
# List of allowed origins (you can replace these with your own domain names)
# allowed_origins = [
#   "*",
#   "https://chat.openai.com",
#   "https://restfox.dev",  # Testing
#   "http://localhost:3000",  # Local development
#   "http://localhost:5173",
#   "https://example.com",  # Production domain
#   "172.31.128.1",
# ]
# # Add CORS middleware to the FastAPI application
# app.add_middleware(
#   CORSMiddleware,
#   # allow_origins=allowed_origins,
#   allow_origin_regex=".*",
#   allow_credentials=True,
#   allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
#   allow_headers=["*"],  # Allow all headers
# )
origins = ["*"]

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)
#
# SEARCH (temp)
#

from babyagi import babysearch

#
# CHAT (temp)
#
import openai
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

# llm = OpenAI()
chat_model = ChatOpenAI()


async def chat(prompt):
  content = f"""
    {prompt}

    If the question pertains to a asking about an activity, or food options, place, or event:
    - do not answer the question directly
    - do not give a list of answers, like a list of suggestions
    - instead, say something like "Here are the following results" WITHOUT listing the answers! We will return results beyond your training data instead.
    - But make the content of your response fun and courteous and context-specific, like "Sure, I love ramen! Here's what we could find for you" or similar
    - use the following action commands
    - "search" action will search our database for up-to-date events. For these questions, don't answer the question directly. 
    
    Return the results as json as follows. Only return json. Don't explain or add any other code than json. Don't wrap in backticks (don't do ``` anywhere.)
    example json:
    {{
      content: your response to the user's prompt
      action: optional user action
      playlist: optional name of playlist if user requests that in add or list favorites
      query: optional action data or query
    }}

    For actions:
    - If user wants to create, update, edit, or read their favorites or placelist or playlists, use one of these actions: [add_favorite, list_favorites, remove_favorite]
       - for list_favorites, if the user mentions a playlist name, use that for "playlist"
    - If user wants to search for something, like 10 best ramen places, use: [search], and format the query into a string in the query key
    """
  print("llm prompt content:", content)
  aimsg = chat_model.predict_messages([HumanMessage(content=content)])
  print("llm message:", aimsg.content)
  aijson = json.loads(aimsg.content)
  print("llm json:", aijson)

  # perform search
  if "search" in aijson["action"]:
    searches = await babysearch(aijson["query"])
    aijson["results"] = searches

  # list favorites
  if "list_favorites" in aijson["action"]:
    favorites = list_favorites("yawnxyz", aijson["playlist"])
    aijson["results"] = favorites

  return aijson
  # return json.dumps(aijson)


app = FastAPI()


@app.get("/discover")
@app.get("/placemaps")
@app.get("/discover/{type}")
@app.get("/placemaps/{type}")
async def _get_placemaps(type: str = None):
  print("discover!")
  return get_placemaps(type)


async def querysearch(query):
  print("attempting to search against:", query)
  # perform search() w/ babyagi w/o agent
  results = await babysearch(query)
  return results
  # results = json.dumps(search(query))
  # use AGI for a specific query, then save results into json for caching + testing
  # format_search_results(): format output into appropriate models - this should be in the placemaps file
  # return get_placemaps()


@app.get("/search/")
async def _get_search(query: str):
  results = await querysearch(query)
  return results


@app.get("/chat/")
async def _chat(prompt: str, response):
  response["Access-Control-Allow-Origin"] = "*"
  print("chat/prompt:", prompt)
  results = await chat(prompt)
  return results


@app.get("/list_db")
async def list_db_endpoint():
  return list_db()


@app.post("/add_placemap/place")
async def _add_placemap_place(placemap_dict: PlaceModel):
  placemap_dict = placemap_dict.dict()
  add_placemap(placemap_dict)
  return {"status": "Place added"}


@app.post("/add_placemap/event")
async def _add_placemap_event(placemap_dict: EventModel):
  placemap_dict = placemap_dict.dict()
  add_placemap(placemap_dict)
  return {"status": "Event added"}


@app.post("/replace_db")
async def replace_db_endpoint(json_data: dict):
  replace_db(json_data)
  return {"status": "Database replaced"}


from faves import add_favorite, remove_favorite, list_favorites, clear_favorites


# Define models to enforce types and constraints
class FavoriteModel(BaseModel):
  data: Union[EventModel, PlaceModel]
  playlist: str = None


class FavoriteRemovalModel(BaseModel):
  favorite_key: str
  playlist: str = None


@app.post("/favorites/add/{username}")
async def add_favorite_endpoint(username: str, favorite: FavoriteModel):
  add_favorite(username, favorite.data, favorite.playlist)
  return {"status": "Favorite added"}


@app.post("/favorites/remove/{username}")
async def remove_favorite_endpoint(username: str,
                                   favorite: FavoriteRemovalModel):
  remove_favorite(username, favorite.favorite_key, favorite.playlist)
  return {"status": "Favorite removed"}


@app.get("/favorites/list/{username}/{playlist}")
@app.get("/favorites/list/{username}")
async def list_favorites_endpoint(username: str, playlist: str = None):
  return list_favorites(username, playlist)


@app.post("/favorites/clear/{username}")
async def clear_favorites_endpoint(username: str):
  clear_favorites(username)
  return {"status": "Favorites cleared"}


@app.get("/")
async def get_instructions():
  return {
    # "intro:":"Sup y'all. Here are the endpoints:",
    "--- intro ---":
    "Welcome to the Event and Place Manager API. Here are the available endpoints:",
    "[get] /discover":
    "a list of all the places and events",
    "[get] /discover/event or /discover/place":
    "Retrieve a placemap filtered by type ('event' or 'place'). If no type is provided, it returns all places and events.",
    "[get] /chat?prompt=tell me a joke":
    "direct call to the chat API",
    "--- favorites endpoints... (e.g. placelists) ---":
    "",
    "[post] /favorites/add/{username}":
    "Add a favorite to a user's list. Provide a FavoriteModel JSON object in the request body.",
    "[post] /favorites/remove/{username}":
    "Remove a favorite from a user's list. Provide a FavoriteRemovalModel JSON object in the request body.",
    "[get] /favorites/list/{username}":
    "List all of a user's favorites.",
    "[get] /favorites/list/{username}/{playlist}":
    "List a user's favorites, filtered by playlist. If no playlist is provided, it returns all favorites.",
    "[post] /favorites/clear/{username}":
    "Remove all favorites from a user's list.",
    "--- db mgmt endpoints... ---":
    "",
    "[post] /add_placemap/place":
    "Add a new place to the placemap. Provide a PlaceModel JSON object in the request body.",
    "[post] /add_placemap/event":
    "Add a new event to the placemap. Provide an EventModel JSON object in the request body.",
    "[get] /list_db":
    "List all items in the database, including their keys and data.",
    "[post] /replace_db":
    "Replace the entire database with the data provided as JSON in the request body. Use with caution."
  }


if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=5002)