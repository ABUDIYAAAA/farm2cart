from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from serpapi import GoogleSearch
import json
import re


# Create your views here.
def index(request):
    return render(request, "main/home.html")


@csrf_exempt
def get_prices(request):
    if request.method == "POST":
        try:
            # Parse JSON payload from request body
            data = json.loads(request.body)
            location = data.get("location")
            vegetable = data.get("vegetable")

            if not location or not vegetable:
                return JsonResponse(
                    {"error": "Location and vegetable are required"},
                    status=400,
                )

            # Split location into city, state, and country
            location_parts = location.split(", ")
            if len(location_parts) != 3:
                return JsonResponse(
                    {"error": "Location must include city, state, and country"},
                    status=400,
                )
            city, state, country = location_parts

            # SerpAPI integration
            api_key = "0d2c785facf9f139965c344b902f186aee5896f701cff7c7a7033a8c4ade1775"

            try:
                # Set up SerpAPI search parameters
                params = {
                    "api_key": api_key,
                    "engine": "google_shopping",
                    "google_domain": "google.co.in",
                    "q": f"{vegetable} price",
                    "hl": "en",  # Language set to English
                    "gl": "in",  # Country set to India
                    "location": location,  # Using location from frontend
                }

                search = GoogleSearch(params)
                results = search.get_dict()
                # Parse shopping results from the API response
                stores = {}

                if "shopping_results" in results:
                    for item in results["shopping_results"]:
                        store_name = item.get("source", "Unknown Store")
                        price_str = item.get("price", "₹0")

                        # Extract numeric price value
                        price_value = (
                            float(re.sub(r"[^\d.]", "", price_str)) if price_str else 0
                        )

                        # Get product link
                        link = item.get("product_link", item.get("link", "#"))

                        # Extract distance if available in extensions
                        distance = "Unknown"
                        if "extensions" in item:
                            for ext in item["extensions"]:
                                if "mi" in ext or "km" in ext:
                                    distance = ext
                                    break

                        # Only keep the cheapest price for each store
                        if (
                            store_name not in stores
                            or price_value < stores[store_name]["price"]
                        ):
                            stores[store_name] = {
                                "store": store_name,
                                "price": price_value,
                                "distance": distance,
                                "link": link,
                            }

                # If no results found
                if not stores:
                    return JsonResponse(
                        {"error": "No results found for this search"}, status=404
                    )

                # Convert stores dictionary to a list and sort by price
                sorted_stores = sorted(stores.values(), key=lambda x: x["price"])
                return JsonResponse({"results": sorted_stores})

            except Exception as api_error:
                print(f"SerpAPI Error: {api_error}")
                return JsonResponse(
                    {"error": f"API Error: {str(api_error)}"}, status=500
                )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)
