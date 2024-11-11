"""Web app."""
import flask
from flask import Flask, render_template, request, redirect, url_for

import pickle
import base64
from training import prediction
import requests
app = flask.Flask(__name__)

data = [{'name':'Delhi', "sel": "selected"}, {'name':'Mumbai', "sel": ""}, {'name':'Kolkata', "sel": ""}, {'name':'Bangalore', "sel": ""}, {'name':'Chennai', "sel": ""}]
# data = [{'name':'India', "sel": ""}]
months = [{"name":"May", "sel": ""}, {"name":"June", "sel": ""}, {"name":"July", "sel": "selected"}]
cities = [{'name':'Delhi', "sel": "selected"}, {'name':'Mumbai', "sel": ""}, {'name':'Kolkata', "sel": ""}, {'name':'Bangalore', "sel": ""}, {'name':'Chennai', "sel": ""}, {'name':'New York', "sel": ""}, {'name':'Los Angeles', "sel": ""}, {'name':'London', "sel": ""}, {'name':'Paris', "sel": ""}, {'name':'Sydney', "sel": ""}, {'name':'Beijing', "sel": ""}]

model = pickle.load(open("model.pickle", 'rb'))

@app.route("/")
@app.route('/index.html')
def index() -> str:
    """Base page."""
    return flask.render_template("index.html")

@app.route('/plots.html')
def plots():
    return render_template('plots.html')

@app.route('/heatmaps.html')
def heatmaps():
    return render_template('heatmaps.html')

@app.route('/satellite.html')
def satellite():
    direc = "processed_satellite_images/Delhi_July.png"
    with open(direc, "rb") as image_file:
        image = base64.b64encode(image_file.read())
    image = image.decode('utf-8')
    return render_template('satellite.html', data=data, image_file=image, months=months, text="Delhi in January 2020")

@app.route('/satellite.html', methods=['GET', 'POST'])
def satelliteimages():
    place = request.form.get('place')
    date = request.form.get('date')
    data = [{'name':'Delhi', "sel": ""}, {'name':'Mumbai', "sel": ""}, {'name':'Kolkata', "sel": ""}, {'name':'Bangalore', "sel": ""}, {'name':'Chennai', "sel": ""}]
    months = [{"name":"May", "sel": ""}, {"name":"June", "sel": ""}, {"name":"July", "sel": ""}]
    for item in data:
        if item["name"] == place:
            item["sel"] = "selected"
    
    for item in months:
        if item["name"] == date:
            item["sel"] = "selected"

    text = place + " in " + date + " 2020"

    direc = "processed_satellite_images/{}_{}.png".format(place, date)
    with open(direc, "rb") as image_file:
        image = base64.b64encode(image_file.read())
    image = image.decode('utf-8')
    return render_template('satellite.html', data=data, image_file=image, months=months, text=text)

@app.route('/predicts.html')
def predicts():
    return render_template('predicts.html', cities=cities, cityname="Information about the city")

@app.route('/predicts.html', methods=["GET", "POST"])
def get_predicts():
    try:
        cityname = request.form["city"]
        cities = [{'name':'Delhi', "sel": ""}, {'name':'Mumbai', "sel": ""}, {'name':'Kolkata', "sel": ""}, 
                  {'name':'Bangalore', "sel": ""}, {'name':'Chennai', "sel": ""}, {'name':'New York', "sel": ""}, 
                  {'name':'Los Angeles', "sel": ""}, {'name':'London', "sel": ""}, {'name':'Paris', "sel": ""}, 
                  {'name':'Sydney', "sel": ""}, {'name':'Beijing', "sel": ""}]
        
        for item in cities:
            if item['name'] == cityname:
                item['sel'] = 'selected'

        # Sending request to the HERE Geocoding API
        URL = "https://geocode.search.hereapi.com/v1/geocode"
        location = cityname
        api_key = 'wBm85BHykSNrgQZBXGiO6JshgNMg6WhbdA6k5unxe7g'  # Ensure this is the correct key
        PARAMS = {'apikey': api_key, 'q': location}

        r = requests.get(url=URL, params=PARAMS)
        r.raise_for_status()  # Raise an error if the response code indicates failure

        # Print the response for debugging
        print(f"API Response: {r.json()}")

        # Check if the 'items' key exists in the response
        data = r.json()
        if not data.get('items'):
            raise ValueError(f"City '{cityname}' not found in geocoding results.")

        # Get latitude and longitude from the correct part of the response
        latitude = data['items'][0]['position']['lat']
        longitude = data['items'][0]['position']['lng']

        final = prediction.get_data(latitude, longitude)
        print(f"Final: {final}")

        # Adjusting data for prediction (e.g., scaling)
        final[4] *= 15

        # Make prediction using the model
        prediction_result = model.predict([final])[0]
        # print(f"Prediction Result: {prediction_result}")
        # print(f"Prediction Result: {type(prediction_result)}")

        if prediction_result == 0:
            pred = "Safe"
        else:
            pred = "Unsafe"

        # Returning the results to be rendered on the page
        return render_template('predicts.html', 
                               cityname=f"Information about {cityname}", 
                               cities=cities, 
                               temp=round((final[0] - 32) * (5 / 9), 2), 
                               maxt=round((final[1] - 32) * (5 / 9), 2), 
                               wspd=round(final[2], 2), 
                               cloudcover=round(final[3], 2), 
                               percip=round(final[4], 2), 
                               humidity=round(final[5], 2), 
                               pred=pred)

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return render_template('predicts.html', cities=cities, cityname="API request failed. Please try again later.")
    except ValueError as e:
        print(f"City data error: {e}")
        return render_template('predicts.html', cities=cities, cityname=f"City '{cityname}' not found.")
    except KeyError as e:
        print(f"Missing data error: {e}")
        return render_template('predicts.html', cities=cities, cityname="Data for the selected city is incomplete.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        return render_template('predicts.html', cities=cities, cityname="Oops, we weren't able to retrieve data for that city.")

if __name__ == "__main__":
    app.run(debug=True)