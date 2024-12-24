import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import json
from notifier import EmailSender, twilio_client

class Flight:
  def __init__(self, date, org, dest, has_business=False):
    self.date = date
    self.org = org
    self.dest = dest
    self.has_business = has_business
    
  def __str__(self):
    if self.has_business:
      return f"Flight(date={self.date}, {self.org} ====> {self.dest}, has_business)"
    else:
      return f"Flight(date={self.date}, {self.org} ====> {self.dest})"    

class Report:
  def __init__(self, title):
    self.depart_flights = []
    self.return_flights = []
    self.title = title
    
  def add_flight(self, flight, is_return=False):
    if flight is None:
      return
    if is_return:
      self.return_flights.append(flight)
    else: 
      self.depart_flights.append(flight)
      
  def __str__(self):
    content = ""
    for flight in self.depart_flights:
      content += f"{flight}\n"
    if len(self.return_flights) > 0:
      content += "=========== returning ===============\n"
    for flight in self.return_flights:
      content += f"{flight}\n"
    return content
  
def has_business(fares):
  for fare in fares:
    if fare.get("fareFamilyType", "") == "AWARD-BUSINESS-FIRST" and fare.get("availability", "") != "SOLD_OUT":
      return True
  return False
      
def post_request(date, dest, org, report=None):
    url = "https://book.virginatlantic.com/flights/search/api/graphql"
    payload= {
      "operationName": "SearchOffers",
      "variables": {
        "request": {
          "pos": None,
          "parties": None,
          "flightSearchRequest": {
            "searchOriginDestinations": [
              {
                "origin": org,
                "destination": dest,
                "departureDate": date
              }
            ],
            "bundleOffer": False,
            "awardSearch": True,
            "calendarSearch": False,
            "flexiDateSearch": False,
            "nonStopOnly": False,
            "currentTripIndexId": "0",
            "checkInBaggageAllowance": False,
            "carryOnBaggageAllowance": False,
            "refundableOnly": False
          },
          "customerDetails": [
            {
              "custId": "ADT_0",
              "ptc": "ADT"
            }
          ]
        }
      },
      "query": "query SearchOffers($request: FlightOfferRequestInput!) {\n  searchOffers(request: $request) {\n    result {\n      slices {\n        current\n        total\n        __typename\n      }\n      criteria {\n        origin {\n          code\n          cityName\n          countryName\n          airportName\n          __typename\n        }\n        destination {\n          code\n          cityName\n          countryName\n          airportName\n          __typename\n        }\n        departing\n        __typename\n      }\n      slice {\n        id\n        fareId\n        flightsAndFares {\n          flight {\n            segments {\n              metal {\n                family\n                name\n                __typename\n              }\n              airline {\n                code\n                name\n                __typename\n              }\n              flightNumber\n              operatingFlightNumber\n              operatingAirline {\n                code\n                name\n                __typename\n              }\n              origin {\n                code\n                cityName\n                countryName\n                airportName\n                __typename\n              }\n              destination {\n                code\n                cityName\n                countryName\n                airportName\n                __typename\n              }\n              duration\n              departure\n              arrival\n              stopCount\n              connection\n              legs {\n                duration\n                departure\n                arrival\n                stopOver\n                isDominantLeg\n                destination {\n                  code\n                  cityName\n                  countryName\n                  airportName\n                  __typename\n                }\n                origin {\n                  code\n                  cityName\n                  countryName\n                  airportName\n                  __typename\n                }\n                __typename\n              }\n              bookingClass\n              fareBasisCode\n              dominantFareProduct\n              __typename\n            }\n            duration\n            origin {\n              code\n              cityName\n              countryName\n              airportName\n              __typename\n            }\n            destination {\n              code\n              cityName\n              countryName\n              airportName\n              __typename\n            }\n            departure\n            arrival\n            __typename\n          }\n          fares {\n            availability\n            id\n            fareId\n            content {\n              cabinName\n              features {\n                type\n                description\n                __typename\n              }\n              __typename\n            }\n            price {\n              awardPoints\n              awardPointsDifference\n              awardPointsDifferenceSign\n              tax\n              amountIncludingTax\n              priceDifference\n              priceDifferenceSign\n              amount\n              currency\n              __typename\n            }\n            fareSegments {\n              cabinName\n              bookingClass\n              isDominantLeg\n              isSaverFare\n              __typename\n            }\n            available\n            fareFamilyType\n            availableSeatCount\n            cabinSelected\n            isSaverFare\n            promoCodeApplied\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      tripSummary {\n        sliceDetails {\n          sliceNumber\n          selectedCabin\n          selectedPrice\n          __typename\n        }\n        currency\n        totalAwardPoints\n        totalPrice\n        __typename\n      }\n      basketId\n      __typename\n    }\n    calendar {\n      fromPrices {\n        fromDate\n        price {\n          amount\n          awardPoints\n          currency\n          minimumPriceInWeek\n          minimumPriceInMonth\n          remaining\n          direct\n          __typename\n        }\n        __typename\n      }\n      from\n      to\n      __typename\n    }\n    priceGrid {\n      criteria {\n        destination {\n          cityName\n          __typename\n        }\n        __typename\n      }\n      returning\n      departures {\n        departing\n        prices {\n          price {\n            amount\n            currency\n            awardPoints\n            __typename\n          }\n          minPrice\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}"
    }
    try:
        # Making the POST request
        response = requests.post(url, json=payload)

        # Raise an exception if the request was unsuccessful
        response.raise_for_status()

        # Print the response (or handle it as needed)
        # print("Response Status Code:", response.status_code)
        res = response.json()
        if 'errors' not in res:
          flight_fares = res.get("data", {}).get("searchOffers", {}).get("result", {}).get("slice", {}).get("flightsAndFares", [])
          fares = []
          for ff in flight_fares:
            fares += ff.get("fares", [])
          flight = Flight(date, org, dest, has_business(fares))
          print(flight)
          return flight
        return None  
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def load_configs(config_path):
    with open(config_path, "r") as file:
        return json.load(file)
      
def run_for_config(dests, origins, depart_dates, return_dates):
    report = Report(f"Search for {origins}[{depart_dates[0]} ~ {depart_dates[-1]}] <> {dests}[{return_dates[0]} ~ {return_dates[-1]}]")
    with ThreadPoolExecutor(max_workers=5) as executor:
      for city_2 in origins:
        for city in dests:
          for date in depart_dates:
              future = executor.submit(post_request, date, city, city_2, report)
              future.add_done_callback(lambda f: report.add_flight(f.result()))

    print("=========== returning ===============")
    with ThreadPoolExecutor(max_workers=5) as executor:
      for city_2 in origins:
        for city in dests:
          for date in return_dates:
              future = executor.submit(post_request, date, city_2, city)
              future.add_done_callback(lambda f: report.add_flight(f.result(), True))
    return report

def iterate_dates(start_date, end_date):
    current_date = start_date
    dates = []
    while current_date <= end_date:
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    return dates
      
def get_dates(start_str, end_str):
    start_date = datetime.strptime(start_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_str, "%Y-%m-%d")
    return iterate_dates(start_date, end_date)

if __name__ == "__main__":
    configs = load_configs("./configs.json")
    sender = None
    try:
      sender = EmailSender()
    except Exception as e:
      print(f"Error initializing email sender: {e}")
    for config in configs:
      origins = config["origins"] 
      destinations = config["destinations"]
      d_dates = get_dates(config["depart_start"], config["depart_end"])
      r_dates = get_dates(config["return_start"], config["return_end"])
      report = run_for_config(destinations, origins, d_dates, r_dates)
      if sender:
        sender.send_email(str(report), config["report_emails"], report.title)
