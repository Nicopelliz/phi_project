import sys

from flask_restful import Api, Resource
from flask import Flask, request
from flask_cors import CORS
from flask_pymongo import PyMongo
import pandas as pd
from datetime import datetime, timedelta
import pytz
from pytz import timezone


# gestisce la definizione del numero di values
def get_num__hours(date_input, input_tz):
    num_of_values = 24

    # data giorno dopo
    next_day = date_input + timedelta(1)

    # preparo le variabili timezone
    utc = pytz.utc
    input_timezone = timezone(input_tz)

    # creo la data localized
    loc_date = input_timezone.localize(date_input)
    loc_next_date = input_timezone.localize(next_day)

    # trasformo in UTC
    date_utc = loc_date.astimezone(utc)
    next_utc = loc_next_date.astimezone(utc)

    # controllo se ci sono differenze con l'orario del giorno dopo in UTC
    # se ci sono variazioni cambio il numero di ore
    hour_gap = next_utc.hour - date_utc.hour

    if hour_gap != 0:
        num_of_values += hour_gap

    return date_utc, num_of_values


# funzione che gestisce la logica della creazione dei curve values
def get_dates(start_date, end_date, input_tz):

    date_change = start_date

    # loop che genera tutto il range di date
    while date_change < end_date:
        date_utc, num_values = get_num__hours(date_change, input_tz)
        values = {str(i): i for i in range(num_values)}

        yield date_utc, values

        date_change += timedelta(1)


# funzione che cicla i dati creati e li inserisce nel database
def insert_in_DB(data_object):

    # loop che inserisce a db le curve values
    for date, values in data_object:
        print(type(date))
        db.cv_collection.insert_one(
            {
                "date": date,
                "values": values
            }
        )

    # creo un indice sul campo "date" per migliorare future
    # prestazioni di ricerca sul campo stesso
    db.cv_collection.create_index("date")


# funzione che fa l'intersezione tra i documenti richiesti dalla
# GET e quelli presenti nel DB
def retreive_from_DB(data_object):
    for date, values in data_object:
        response = db.cv_collection.find_one({"date": date})
        print(date)

        # per tutte le date non presenti ritorna lo stesso numero
        # di curve values ma con valore NULL
        if response is None:
            values = {str(i): None for i in range(len(values))}

        full_document = {"date": str(date), "values": values}
        yield full_document


# classe che genera l'api
class MyApi(Resource):

    # funzione che raccoglie tutti i values sotto forma di lista
    def get(self):

        try:
            # prendo i dati presenti nel json
            response = request.get_json()
            start_date = response["start_date"]
            end_date = response["end_date"]
            user_timezone = response["timezone"]

            date_start = datetime(start_date['year'], start_date['month'], start_date['day'])
            date_end = datetime(end_date['year'], end_date['month'], end_date['day'])

            date_values_obj = get_dates(date_start, date_end, user_timezone)
            documents_resp = retreive_from_DB(date_values_obj)

            return list(documents_resp)

        except Exception as e:
            return "ERROR: " + str(e), 500

    # funzione che popola il database
    def post(self):

        try:
            response = request.get_json()
            start_date = response["start_date"]
            end_date = response["end_date"]
            user_timezone = response["timezone"]

            date_start = datetime(start_date['year'], start_date['month'], start_date['day'])
            date_end = datetime(end_date['year'], end_date['month'], end_date['day'])

            # escludo tutti i lunedi dalle date
            # datelist = [date for date in datelist if date.weekday() != 0]

            date_values_obj = get_dates(date_start, date_end, user_timezone)

            insert_in_DB(date_values_obj)

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
