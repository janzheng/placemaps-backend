from typing import Dict, List
from collections import deque
import openai
import pinecone
import aiohttp
import json
from serpapi import GoogleSearch

import os
from dotenv import load_dotenv

load_dotenv('.env')

# Set API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_TABLE_NAME = os.getenv("PINECONE_TABLE_NAME")
SERP_API_KEY = os.getenv("SERP_API_KEY")
GOOGLE_API_KEY = ""
CUSTOM_SEARCH_ENGINE_ID = ""


class BabyAGI:

  def __init__(self,
               openai_api_key,
               pinecone_api_key,
               google_api_key,
               serp_api_key,
               custom_search_engine_id,
               pinecone_environment=PINECONE_ENV,
               table_name=PINECONE_TABLE_NAME,
               first_task="Develop a task list"):
    self.openai_api_key = openai_api_key
    self.pinecone_api_key = pinecone_api_key
    self.google_api_key = google_api_key
    self.serp_api_key = serp_api_key
    self.custom_search_engine_id = custom_search_engine_id
    self.pinecone_environment = pinecone_environment
    self.task_list = deque([])
    self.objective = ""
    self.table_name = table_name
    self.first_task = first_task

    openai.api_key = self.openai_api_key
    pinecone.init(api_key=self.pinecone_api_key,
                  environment=self.pinecone_environment)

  def set_objective(self, objective):
    self.objective = objective

  def add_task(self, task: Dict):
    if not self.task_list:
      task_id = 1
    else:
      task_id = self.task_list[-1]["task_id"] + 1
    task.update({"task_id": task_id})
    self.task_list.append(task)

  def get_ada_embedding(self, text):
    text = text.replace("\n", " ")
    return openai.Embedding.create(
      input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]

  def task_creation_agent(self, objective: str, result: str,
                          task_description: str, task_list: List[str]):
    prompt = f"You are an task creation AI that uses the result of an execution agent to create new tasks with the following objective: {objective}, The last completed task has the result: {result}. This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join(task_list)}. Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks. Return the tasks as an array."

    response = openai.Completion.create(engine="text-davinci-003",
                                        prompt=prompt,
                                        temperature=0.5,
                                        max_tokens=100,
                                        top_p=1,
                                        frequency_penalty=0,
                                        presence_penalty=0)
    new_tasks = response.choices[0].text.strip().split('\n')
    return [{"task_name": task_name} for task_name in new_tasks]

  async def execution_agent(self, objective: str, task: str) -> str:
    context = await self.context_agent(index=PINECONE_TABLE_NAME,
                                       query=objective,
                                       n=5)
    context_str = '\n'.join(context)

    response = openai.Completion.create(
      engine="text-davinci-003",
      prompt=
      f"You are an AI who performs one task based on the following objective: {objective}. Your task: {task}\n\nContext:\n{context_str}\n\nResponse:",
      temperature=0.7,
      max_tokens=2000,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0)
    return response.choices[0].text.strip()

  async def context_agent(self, query: str, index: str, n: int):
    # Get search results
    # search_results = await self.search_internet(query, self.google_api_key, self.custom_search_engine_id)
    print("[context_agent] query:", query)

    # if query is a dict with query['objective'], set query as query['objective']
    if isinstance(query, dict):
      query = query["objective"]

    query_embedding = self.get_ada_embedding(query)
    search_results = await self.serp_internet(query, self.serp_api_key)

    # serp results
    print('pizza things', search_results["organic_results"])
    search_snippets = [
      json.dumps({
        "snippet": item.get("snippet", ""),
        "title": item.get("title", ""),
        "link": item.get("link", "")
      }) for item in search_results["organic_results"] if item is not None
    ]

    # search_snippets = [
    #   item["snippet"] for item in search_results.get("items", [])
    # ]
    print("SERP SNIPPETS:", search_snippets)

    index = pinecone.Index(index_name=index)
    results = index.query(query_embedding, top_k=n, include_metadata=True)
    sorted_results = sorted(results.matches,
                            key=lambda x: x.score,
                            reverse=True)
    return search_snippets + [(str(item.metadata['task']))
                              for item in sorted_results]

  async def search_internet(self, query, api_key, custom_search_engine_id):
    print("search_internet called with query:", query)
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": api_key, "cx": custom_search_engine_id, "q": query}
    async with aiohttp.ClientSession() as session:
      async with session.get(base_url, params=params) as response:
        result = await response.json()
        print("Search results:", result)
        return result

  async def serp_internet(self, query, api_key):
    params = {
      "api_key": api_key,
      "engine": "google",
      "q": query,
      # "location": "Austin, Texas, United States",
      "google_domain": "google.com",
      # "gl": "us",
      # "hl": "en"
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    print("SERP Results:", results)
    return results

  def clear_task_list(self):
    self.task_list.clear()
    self.task_id_counter = 0


baby_agi = BabyAGI(OPENAI_API_KEY,
                   PINECONE_API_KEY,
                   GOOGLE_API_KEY,
                   SERP_API_KEY,
                   CUSTOM_SEARCH_ENGINE_ID,
                   table_name=PINECONE_API_KEY,
                   pinecone_environment=PINECONE_ENV,
                   first_task="Develop a task list")


def load_json_file(file_path):
  with open(file_path) as json_file:
    data = json.load(json_file)
  return data


async def babysearch(query):
  global baby_agi
  print("[SEARCH]", query)
  # search_results = await baby_agi.search_internet(query, baby_agi.google_api_key, baby_agi.custom_search_engine_id)

  # save some API calls for dev - top 10 ramen
  # return load_json_file("./serp.json")
  search_results = await baby_agi.serp_internet(query, baby_agi.serp_api_key)
  print("[SEARCH] Results:", search_results)
  # return search_results
  return search_results


# ## BabyAGI Endpoints

# # Todo
# # [@] Add single-task endpoint, where one single task is requested and run

# # @app.get("/joke")
# # async def joke():
# #   print("[JOKE!!]")
# #   # return {"punchline": "banana!"}
# #   return Response(
# #     content="Why did the banana cross the road?! Because ban ana!",
# #     media_type="text")
# #   return "Why did the banana cross the road?!"

# # @app.post("/set_objective")
# # async def set_objective(objective: dict):
# #   global baby_agi
# #   print("[SETTING OBJECTIVE]", objective)
# #   baby_agi.clear_task_list(
# #   )  # Clear the task list and reset the task ID counter
# #   baby_agi.set_objective(objective)
# #   return {"status": "Objective set", "objective": objective}

# # @app.get("/set_objective")
# # async def set_get_objective(objective: str):
# #   global baby_agi
# #   print("[SETTING OBJECTIVE]", objective)
# #   baby_agi.clear_task_list(
# #   )  # Clear the task list and reset the task ID counter
# #   baby_agi.set_objective(objective)
# #   return {"status": "Objective set", "objective": objective}

# # @app.post("/add_task")
# # async def add_task(task_name: dict):
# #   global baby_agi
# #   print("[ADDING TASK]", task_name)
# #   task = {"task_name": task_name}
# #   baby_agi.add_task(task)
# #   return {"status": "Task added"}

# # @app.get("/add_task")
# # async def get_task(task: str):
# #   global baby_agi
# #   print("[ADDING TASK]", task)
# #   taskdict = {"task_name": task}
# #   baby_agi.add_task(taskdict)
# #   return {"status": "Task added", "task": task}

# # @app.get("/execute_next_task")
# # @app.post("/execute_next_task")
# # async def execute_next_task():
# #   global baby_agi
# #   print("[EXECUTING NEXT TASK]")

# #   if not baby_agi.task_list:
# #     return {"status": "No tasks in the list"}

# #   task = baby_agi.task_list.popleft()
# #   print("[EXECUTING NEXT TASK] task:", task, " (objective): ",
# #         baby_agi.objective)

# #   result = await baby_agi.execution_agent(baby_agi.objective,
# #                                           task["task_name"])
# #   print("[EXECUTING NEXT TASK] result:", result)

# #   new_tasks = baby_agi.task_creation_agent(
# #     baby_agi.objective, result, task["task_name"],
# #     [t["task_name"] for t in baby_agi.task_list])
# #   print("[EXECUTING NEXT TASK] adding new tasks:", new_tasks)
# #   for new_task in new_tasks:
# #     baby_agi.add_task(new_task)

# #   response = {
# #     "task_id": task["task_id"],
# #     "task_name": task["task_name"],
# #     "result": result,
# #     "new_tasks": new_tasks,
# #   }

# #   return response

# # @app.get("/get_task_list")
# # async def get_task_list():
# #   global baby_agi
# #   task_list = [task["task_name"] for task in baby_agi.task_list]
# #   print("[GET TASK LIST]", task_list)
# #   return {"task_list": task_list}

# # @app.get("/search")
# async def babysearch(query):
#   # global baby_agi
#   print("[SEARCH]", query)
#   # search_results = await baby_agi.search_internet(query, baby_agi.google_api_key, baby_agi.custom_search_engine_id)
#   # search_results = await baby_agi.serp_internet(query, baby_agi.serp_api_key)
#   # print("[SEARCH] Results:", search_results)
#   # return search_results
#   return "some search result"

# # async def get_search(request: Request):
# #   global baby_agi
# #   query = request.query_params.get("query", "test")
# #   print("[SEARCH]", query)
# #   # search_results = await baby_agi.search_internet(query, baby_agi.google_api_key, baby_agi.custom_search_engine_id)
# #   search_results = await baby_agi.serp_internet(query, baby_agi.serp_api_key)
# #   return search_results

# # ## Plugin Support Code
# # # @app.get("/favicon.ico")
# # # async def get_logo():
# # #     return FileResponse("favicon.ico", media_type="image/ico")

# # @app.get("/logo.png")
# # async def plugin_logo():
# #   return FileResponse('logo.png')

# # @app.get("/.well-known/ai-plugin.json")
# # async def plugin_manifest(request: Request):
# #   host = request.headers['host']
# #   with open("ai-plugin.json") as f:
# #     text = f.read().replace("PLUGIN_HOSTNAME", f"https://{host}")
# #   return JSONResponse(content=json.loads(text))

# # @app.get("/openapi.yaml")
# # async def load_openapi(request: Request):
# #   host = request.headers["host"]
# #   try:
# #     with open("openapi.yaml") as file:
# #       text = file.read()
# #   except FileNotFoundError:
# #     return Response(status_code=404, content="Not found")
# #   # text = text.replace("PLUGIN_HOSTNAME", f"http://{host}")
# #   return Response(content=text, media_type="text/yaml")

# # if __name__ == "__main__":
# #   import uvicorn
# #   uvicorn.run(app, host="0.0.0.0", port=5002)
