from dotenv import load_dotenv              # pip install python-dotenv
from geopy import distance
from googleplaces import GooglePlaces, types, lang
import json
import os
import pgeocode
import requests as req

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
google_places = GooglePlaces(GOOGLE_API_KEY)


def Closest_Hospitals(Latitude, Longitude, Nearby_Hospital_Results):
    def Take_Second(elem):
        return elem[1]

    User_Coords = (Latitude, Longitude)
    Nearby_Hospital_Result_w_Distance = [['$' for x in range(2)] for y in range(len(Nearby_Hospital_Results)-1)]
    for x in range(len(Nearby_Hospital_Results)-1):
        current = Nearby_Hospital_Results[x].split(' ')
        Hospital_Coords = (current[1], current[2])
        Nearby_Hospital_Result_w_Distance[x][0] = distance.distance(Hospital_Coords, User_Coords).km
        Nearby_Hospital_Result_w_Distance[x][1] = str(Nearby_Hospital_Results[x])

    Nearby_Hospital_Result_w_Distance.sort()
    Three_Closest_Hospitals = []
    for x in range(3):
        Three_Closest_Hospitals.append(str(Nearby_Hospital_Result_w_Distance[x][0]) + ' ' + Nearby_Hospital_Result_w_Distance[x][1])
    return Three_Closest_Hospitals
    


def Nearby_Hospitals(Latitude, Longitude, Radius):  # Returns an array of all health center/hospitals within a certain radius
    Nearby_Hospital_Results = []
    print("Lat: " + str(Latitude) + " Lng: " + str(Longitude) + " Radius: " + str(Radius))
    query_result = google_places.nearby_search(lat_lng={'lat': Latitude, 'lng': Longitude}, radius = Radius, types = [types.TYPE_HOSPITAL])
    if query_result.has_attributions:
        print (query_result.html_attributions)
    for place in query_result.places:
        if ("Health Centre" in place.name) or ("Hospital" in place.name):
            name = str(place.name).replace(' ', '_')
            Nearby_Hospital_Results.append(name + ' ' + str(place.geo_location['lat']) + ' ' + str(place.geo_location['lng']))

    return Closest_Hospitals(Latitude, Longitude, Nearby_Hospital_Results)


def Area_Code_to_Coordinates(area_code):
    nomi = pgeocode.Nominatim('ca')
    area_code_data = nomi.query_postal_code(area_code.lower())
    Latitude = area_code_data.get('latitude')
    Longitude = area_code_data.get('longitude')

    print("Lat: " + str(Latitude) + " Long: " + str(Longitude) + "\n")
    Three_Closest_Hospitals = Nearby_Hospitals(float(Latitude), float(Longitude), 20000)
    return Three_Closest_Hospitals