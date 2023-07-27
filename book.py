import json
from flask import Flask,request,jsonify
from flask import redirect, render_template, url_for
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
from datetime import date
from flask_cors import CORS
from bson import json_util
from pymongo import MongoClient
import openai
import os
import requests

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)
app.config["MONGO_URI"] = "mongodb+srv://aakashgaurav456:Aakash@cluster0.blrrfmi.mongodb.net/proManage?retryWrites=true&w=majority"
db = PyMongo(app).db

client = MongoClient("mongodb+srv://aakashgaurav456:Aakash@cluster0.sztdb1x.mongodb.net/?retryWrites=true&w=majority")
db1 = client['projectManager']
collection = db1['projects']

@app.route("/")
def hello_world():
    return f"<p>Hello, World!</p>"



@app.route("/signup",methods=["POST"])
def signup():
    data = request.get_json()
    image = data["image"]
    name = data["name"]
    bio = data["bio"]
    tech_stack = data["tech_stack"]
    password = data["password"]
    hash_password = bcrypt.generate_password_hash(password).decode('utf-8')
    email = data["email"]

    if image and name and bio and tech_stack and password:
        db.users.insert_one({"image":image,"name":name,"bio":bio,"tech_stack":tech_stack,"password":hash_password,"email":email,"start_date":str(date.today()),"status":"active"})
        return jsonify("data updated")
    else:
        return jsonify("Error Adding Data")


@app.route("/login",methods=["POST"])
def login():
    data = request.get_json()
    email = data["email"]
    password = data["password"]
    if email and password:
       users = db.users.find({"email":email})
       user_list = [user for user in users]
       json_data = json_util.dumps(user_list)
       if len(user_list)>0:
           result = bcrypt.check_password_hash(user_list[0]["password"], password)
           if result:
               return json_data
           else:
               return jsonify("Password Wrong")
       else:
           return jsonify("Email id Not Found")
    else:
        return jsonify("Please Provide all details")
    


@app.route("/manager",methods=["GET"])
def manager():
    if request.method == "GET":
       manager = db.users.find()
       manager_list = [user for user in manager]
       json_data = json_util.dumps(manager_list)
       return json_data





@app.route("/manager/status",methods=["PATCH"])
def manager_status():
    data = request.get_json()
    id = data["name"]
    status = str(data["status"])
    print(id,status)
    db.users.update_one({"name":id},{"$set":{"status":status}})
    return jsonify("Status updated")


@app.route("/manager/<name>",methods=["DELETE"])
def delete_manager(name):
    db.users.delete_one({"name":name})
    return jsonify("Manager Deleted")




@app.route("/project",methods=["GET","POST"])
def project():
    if request.method == "POST":
        data = request.get_json()
        name = data["name"]
        bio = data["bio"]
        start_date = str(date.today())
        assigned_to = data["assigned_to"]
        end_date = ""
        status = ""
        project = {
            "name":name,
            "bio":bio,
            "start_date":start_date
        }
        if name  and bio and assigned_to:
            db.projects.insert_one({"name":name,"bio":bio,"assigned_to":assigned_to,"start_date":start_date,"end_date":"","status":"Not Started","tasks":[],"resources":[]})
            db.users.update_one({"name":assigned_to}, {"$push":{"project":project} } )
            return jsonify("Project Uploaded")
        
    elif request.method == "GET":
        project = db.projects.find()
        project_list  = [user for user in project]
        json_data = json_util.dumps(project_list)
        return json_data
    


@app.route("/project",methods=["PATCH"])
def project_status():
    data = request.get_json()
    if data["status"]!="Completed":
        update_data = {"$set": {"status":data["status"]}} 
    else:
        end_date = str(date.today())
        update_data = {"$set": {"status":data["status"], "end_date":end_date}} 
    
    result = db.projects.update_many({"name":data["name"]}, update_data)
    return jsonify(f"{result.matched_count}")


@app.route("/project",methods=["DELETE"])
def delete_project():
    data = request.get_json()
    print(data)
    results = db.projects.delete_one({"name":data["name"]})
    return jsonify("Project Deleted")

@app.route("/project/<email>")
def independent(email):
     print(email)
     user = db.projects.find({"assigned_to":email})
     user_list = [users for users in user]
     json_data = json_util.dumps(user_list)
     return json_data

@app.route("/task_create",methods=["POST"])
def task_create():
    data = request.get_json()
    project_name = data["project_name"]
    del data["project_name"]
    db.projects.update_one( {"name":project_name}, {"$push":{"tasks":data}})
    return jsonify("Task Added")


@app.route("/resource/<name>",methods=["POST"])
def addResource(name):
    data = request.get_json()
    res = data["resource"]
    db.projects.update_one({"name":name},{"$push":data})
    return jsonify("Resource Added")

def get_current_weather(location, unit="fahrenheit"):
    url =  "https://api.openweathermap.org/data/2.5/weather?q=Ranchi&appid=5bf1532258b851ebe514cc9d06bb7170"
    response = requests.get(url)
    data = response.json()
    weather_info = {
        "location": location,
        "temperature": "90",
        "unit": unit,
        "forecast": ["sunny", "windy"],
    }
    
    return json.dumps(data)



openai.api_key = "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"

@app.route("/openai", methods=("GET", "POST"))
def openai_generate():
    data = request.get_json()
    prompt = data["query"]
    messages = [{"role": "user", "content": prompt}]
    functions = [
        {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        }
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        functions=functions,
        function_call="auto",  # auto is default, but we'll be explicit
    )
    response_message = response["choices"][0]["message"]
    if response_message.get("function_call"):
        available_functions = {
            "get_current_weather": get_current_weather,
        } 
        function_name = response_message["function_call"]["name"]
        fuction_to_call = available_functions[function_name]
        function_args = json.loads(response_message["function_call"]["arguments"])
        function_response = fuction_to_call(
            location=function_args.get("location"),
            unit=function_args.get("unit"),
        )
        messages.append(response_message)  # extend conversation with assistant's reply
        messages.append(
            {
                "role": "function",
                "name": function_name,
                "content": function_response,
            }
        )
        second_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=messages,
        )
        return second_response






if __name__ == "__main__":
    app.run(debug=True)
