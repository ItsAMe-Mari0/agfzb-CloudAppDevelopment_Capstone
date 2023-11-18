import requests
import json
from .models import CarDealer, DealerReview
from requests.auth import HTTPBasicAuth
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, SentimentOptions

with open("/home/project/agfzb-CloudAppDevelopment_Capstone/cloudant/data/dealerships.json", "r") as f:
    dealership_db = json.load(f)['dealerships']
with open("/home/project/agfzb-CloudAppDevelopment_Capstone/cloudant/data/reviews-full.json", "r") as f:
    reviews_db = json.load(f)['reviews']
#print("Dealership_db", dealership_db)
#print('\n\n')
#print("Reviews_db", reviews_db)

# Create a `get_request` to make HTTP GET requests
def get_request(url, api_key=None, **kwargs):
    print(kwargs)
    print("GET from {} ".format(url))
    
    try:
        if api_key:
            response = requests.get(url, headers={'Content-Type': 'application/json'},
                                    params=kwargs, auth=HTTPBasicAuth('apikey', api_key))
        else:
            response = requests.get(url, headers={'Content-Type': 'application/json'},
                                    params=kwargs)
    except:
        # If any error occurs
        print("Network exception occurred")
    
    status_code = response.status_code
    print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    return json_data


# Create a `post_request` to make HTTP POST requests
def post_request(url, json_payload, **kwargs):
    
    print("POST to {} ".format(url))
    
    try:
        response = requests.post(url, params=kwargs, json=json_payload)
        status_code = response.status_code
        print("With status {} ".format(status_code))
        json_data = json.loads(response.text)
        return json_data
    except:
        # If any error occurs
        print("Network exception occurred")
        return None


# Create a get_dealers_from_cf method to get dealers from a cloud function
def get_dealers_from_cf(url, **kwargs):
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url)
    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result
        # For each dealer object
        for dealer in dealers:
            # Get its content in `doc` object
            dealer_doc = dealer
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"], full_name=dealer_doc["full_name"],
                                   id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"],
                                   short_name=dealer_doc["short_name"],
                                   st=dealer_doc["st"], zip=dealer_doc["zip"], _id=dealer_doc["_id"], _rev=dealer_doc["_rev"],
                                   state=dealer_doc["state"])
            results.append(dealer_obj)

    return results

def get_dealers_from_local():
    results = []
    for dealer in dealership_db:
        #print("get_dealer_from_local", dealer)
        results.append(CarDealer(address=dealer["address"], city=dealer["city"], full_name=dealer["full_name"],
                                   id=dealer["id"], lat=dealer["lat"], long=dealer["long"],
                                   short_name=dealer["short_name"],
                                   st=dealer["st"], zip=dealer["zip"], _id=None, _rev=None,
                                   state=dealer["state"]))
    return results

# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
def get_dealer_reviews_from_cf(url, dealer_id, **kwargs):
    results = []
    json_result = get_request(url, id=dealer_id, **kwargs)
    
    if json_result:
        reviews = json_result
        for review in reviews:
            dealer_doc = review
            sentiment = analyze_review_sentiments(dealer_doc["review"])
            review_obj = DealerReview(dealership=dealer_doc["dealership"], name=dealer_doc["name"], purchase=dealer_doc["purchase"],
                                   review=dealer_doc["review"], purchase_date=dealer_doc["purchase_date"], car_make=dealer_doc["car_make"],
                                   car_model=dealer_doc["car_model"], car_year=dealer_doc["car_year"], sentiment=sentiment, id=dealer_doc["id"]
                                )
            results.append(review_obj)

    return results

def get_dealer_reviews_from_local(dealer_id):
    results = []
    for review in reviews_db:
        if review["dealership"] != dealer_id:
            continue
        print("get_dealer_reviews_from_local", dealer_id,review)
        sentiment = analyze_review_sentiments(review["review"])
        results.append(DealerReview(dealership=review["dealership"], name=review["name"], purchase=review["purchase"],
                                   review=review["review"], purchase_date=review["purchase_date"], car_make=review["car_make"],
                                   car_model=review["car_model"], car_year=review["car_year"], sentiment=sentiment, id=review["id"]
                                ))
    return results

def add_dealer_review_from_local(review):
    review['id'] = max([row['id'] for row in reviews_db]) +1
    print("\n\nAdding a review", reviews_db[0], review)
    reviews_db.append(review)
    

# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
def analyze_review_sentiments(dealerreview):
    url = "https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/49539b41-6d73-4689-91a4-8d2eba168cf7"
    api_key = "lzV4_xT-avtO3wzAXOpghf56RMuuBnec1lcFz0lQPI6h"
    authenticator = IAMAuthenticator(api_key)
    natural_language_understanding = NaturalLanguageUnderstandingV1(version='2021-08-01', authenticator=authenticator)
    natural_language_understanding.set_service_url(url)
    
    response = natural_language_understanding.analyze(
        text=dealerreview,
        features=Features(sentiment=SentimentOptions(targets=[dealerreview])),
        language="en"
    ).get_result()
    
    
    label = response['sentiment']['document']['label']

    return label




