from flask import Flask, request, redirect, jsonify
from flasgger import Swagger, swag_from
from dotenv import load_dotenv
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import string
import random
from datetime import datetime

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
app.config["SWAGGER"] = {"title": "My API"}
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
        if not url_entry["isActive"]:
            return jsonify({"error": "URL is not active"}), 400
        collection.update_one({"short_id": id}, {"$inc": {"clicks": 1}})
        return redirect(url_entry["original_url"])
    else:
        return jsonify({"error": "URL not found"}), 404


@app.route("/urls", methods=["GET"])
def get_all_urls():
    urls = collection.find()
    result = []
    for url in urls:
        result.append(
            {
                "original_url": url["original_url"],
                "short_id": url["short_id"],
                "created_at": url["created_at"],
                "isActive": url["isActive"],
                "clicks": url["clicks"],
                "made_by": url["made_by"],
            }
        )
    return jsonify(result)


@app.route("/info/<id>", methods=(["GET"]))
def url_info(id):
    url_entry = collection.find_one({"short_id": id})
    if url_entry:
        return jsonify(
            {
                "original_url": url_entry["original_url"],
                "short_id": url_entry["short_id"],
                "created_at": url_entry["created_at"],
                "isActive": url_entry["isActive"],
                "clicks": url_entry["clicks"],
                "made_by": url_entry["made_by"],
            }
        )
    else:
        return jsonify({"error": "URL not found"}), 404


@app.route("/deactivate/<id>", methods=["POST"])
def deactivate_url(id):
    result = collection.update_one({"short_id": id}, {"$set": {"isActive": False}})
    if result.matched_count > 0:
        return jsonify({"message": "URL deactivated successfully"}), 200
    else:
        return jsonify({"error": "URL not found"}), 404


@app.route("/create", methods=(["POST"]))
def create_url():
    original_url = request.json.get("url")
    custom_id = request.json.get("custom_id")
    is_active = request.json.get("isActive", True)  # Default to True if not provided
    made_by = request.json.get("made_by", "Admin")
    if not original_url:
        return jsonify({"error": "URL is required"}), 400
    if custom_id:
        if collection.find_one({"short_id": custom_id}):
            return jsonify({"error": "Custom ID already exists"}), 400
        short_id = custom_id
    else:
        url_entry = collection.find_one({"original_url": original_url})
        if url_entry:
            short_id = url_entry["short_id"]
        else:
            # Generate a unique short ID
            short_id = generate_short_id()
            while collection.find_one({"short_id": short_id}):
                short_id = generate_short_id()

        # Save to the database
    collection.insert_one(
        {
            "original_url": original_url,
            "short_id": short_id,
            "created_at": datetime.now(),
            "isActive": is_active,
            "clicks": 0,
            "made_by": made_by,
        }
    )

    short_url = request.host_url + short_id
    return jsonify({"short_url": short_url})
