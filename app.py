from flask import Flask, request, redirect, jsonify
from flasgger import Swagger, swag_from
from dotenv import load_dotenv
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import string
import random


load_dotenv()

database_url = os.getenv("MONGO_URL")

client = MongoClient(database_url, server_api=ServerApi("1"))

db = client["url_shortener"]
collection = db["urls"]


try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


app = Flask(__name__)
app.config["SWAGGER"] = {"title": "My API", "uiversion": 3}
swagger = Swagger(app)


def generate_short_id(length=6):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


@app.route("/")
def index():
    """Example Endpoint"""
    # return "Hello World!"


@app.route("/<id>")
def url_direct(id):
    url_entry = collection.find_one({"short_id": id})
    if url_entry:
        return redirect(url_entry["original_url"])
    else:
        return jsonify({"error": "URL not found"}), 404


@app.route("/create", methods=(["POST"]))
@swag_from("./doc/flasgger/create.yml")
def create_url():
    original_url = request.json.get("url")
    if not original_url:
        return jsonify({"error": "URL is required"}), 400
    url_entry = collection.find_one({"original_url": original_url})
    if url_entry:
        short_id = url_entry["short_id"]
    else:
        # Generate a unique short ID
        short_id = generate_short_id()
        while collection.find_one({"short_id": short_id}):
            short_id = generate_short_id()

        # Save to the database
        collection.insert_one({"original_url": original_url, "short_id": short_id})

    short_url = request.host_url + short_id
    return jsonify({"short_url": short_url})
    # get url from post request
    # generate shortened link alias
    # put into database
