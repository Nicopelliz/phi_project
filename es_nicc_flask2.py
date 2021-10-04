import sys

from flask_restful import Api, Resource
from flask import Flask, request
from flask_cors import CORS
from flask_pymongo import PyMongo
import pandas as pd
from datetime import datetime
import pytz


# funzione che gestisce la logica della creazione dei curve values
def get_dates(dates):

    previous_date = ""

    for date in dates:

        num_values = 24

        next_date = date \
            .replace(tzinfo=pytz.timezone('europe/rome')) \
            .astimezone(pytz.utc).strftime("%Y:%m:%d %H:%M:%S")

        if previous_date and previous_date != next_date:

            if int(next_date[-8:-6]) > int(previous_date[-8:-6]):
                num_values = 25
            elif int(next_date[-8:-6]) < int(previous_date[-8:-6]):
                num_values = 23

            values = {str(i): i for i in range(num_values)}

            yield previous_date, values

        previous_date = next_date


# funzione che cicla i dati creati e li inserisce nel database
def insert_in_DB(data_object):

    for date, values in data_object:
        db.cv_collection.insert_one(
            {
                "date": datetime.strptime(date, "%Y:%m:%d %H:%M:%S"),
                "values": values
            }
        )

    db.cv_collection.create_index("date")


# classe che genera l'api
class MyApi(Resource):

    # funzione che raccoglie tutti i values sotto forma di lista
    def get(self):

        response = request.get_json()
        start_date = response["start_date"]
        end_date = response["end_date"]

        datelist = pd.date_range(
            start=datetime(start_date['year'], start_date['month'], start_date['day']),
            end=datetime(end_date['year'], end_date['month'], end_date['day'])
        )

        values_list = []
        datas = db.cv_collection.find()

        for data in datas:
            values = list(data["values"].values())
            values_list += values
        print(datelist)

        return values_list

    # funzione che popola il database
    def post(self):

        try:
            response = request.get_json()
            start_date = response["start_date"]
            end_date = response["end_date"]

            datelist = pd.date_range(
                start=datetime(start_date['year'], start_date['month'], start_date['day']),
                end=datetime(end_date['year'], end_date['month'], end_date['day'])
            )

            # escludo tutti i lunedi dalle date
            datelist = [date for date in datelist if date.weekday() != 0]

            date_values = get_dates(datelist)

            insert_in_DB(date_values)

            return "Dati inseriti", 201

        except Exception as e:
            return "ERROR: " + str(e), 500


# istanzio l'app di flask
app = Flask('phinergy_app')

# collega l'app database di MongoDB
app.config["MONGO_URI"] = "mongodb://localhost:27017/phi_db"
db = PyMongo(app).db

# abilita le CORS restringendo l'accesso solo ad un indirizzo
CORS(app, resources={'/*': {'origins': "http://localhost:4200"}})
api = Api(app)

# aggiunge le funzionalità per l'API
api.add_resource(MyApi, '/')

if __name__ == "__main__":

    try:
        app.run(debug=True, port=8000)

    except OSError as e:
        print("OSerror on APP LEVEL: " + str(e))

    except Exception as e:
        print("GENERIC ERROR on APP LEVEL: " + str(e))
