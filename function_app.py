import azure.functions as func
from azure.storage.blob import BlobServiceClient
import logging
import json
import os
import shippo
from shippo.models import components
import random as rand

STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=customerdetailsungku;AccountKey=ZcAIsbgYd9DCysK7O6VnjWbSXZ43xgqzAt+FFLkpAyRNnZ/xTFnLMy9ZouqHfKasH3QdH4DSkh5j+ASt/pDw1w==;EndpointSuffix=core.windows.net"
CONTAINER_NAME = "customerdetails"
shippo_sdk = shippo.Shippo(api_key_header="shippo_test_2ebb7faec745c14f4578a3b32905021023d53ac2")

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="stripe_receive")
def stripe_receive(req: func.HttpRequest) -> func.HttpResponse:
    
    try:
        logging.info(os.environ['SqlConnectionString'])
        logging.info("Received a request")
        req_body = req.get_json()

        id = req_body['id']
        shipping_details = req_body['data']['object']['customer_details']
        name = shipping_details['name']
        address = shipping_details['address']
        formatted_address = {
            "line1": address['line1'],
            "city": address['city'],
            "state": address['state'],
            "postal_code": address['postal_code'],
            "country": address['country']
        }

        customer_data = {
            "name": name,
            "address": formatted_address
        }

        logging.info("Data received")

        try:
            logging.info("Connecting to blob storage")
            blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
            container_client = blob_service_client.get_container_client(CONTAINER_NAME)
            logging.info("Connected to blob storage")

            blob_client = container_client.get_blob_client(f"{id}.json")
            blob_client.upload_blob(json.dumps(customer_data, indent=4))
            logging.info("Data uploaded to blob storage")

        except Exception as e:
            logging.error(f"Error connecting to database: {e}")
            return func.HttpResponse(status_code=500)

        return func.HttpResponse(status_code=200)
    
    except ValueError:
        return func.HttpResponse(
            "Please pass a JSON object in the request body",
            status_code=400
        )

@app.blob_trigger(arg_name="myblob", path="customerdetails", connection="STORAGE_CONNECTION_STRING")
def easypost_send(myblob: func.InputStream):
    logging.info("Blob trigger executed")
    logging.info(f"Blob name: {myblob.name}")

    try:
        blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        file_name = os.path.basename(myblob.name)
        blob_client = container_client.get_blob_client(file_name)
        blob_data = blob_client.download_blob().readall()
        json_data = json.loads(blob_data)

        logging.info("Data retrieved from blob storage")
        logging.info(json.dumps(json_data, indent=4))
    
        logging.info("Creating shipment")
        try:
            address_from = components.AddressCreateRequest(
                name="Ungku",
                street1="123 Fake Street",
                city="Springfield",
                state="IL",
                zip="62701",
                country="US"
            )

            address_to = components.AddressCreateRequest(
                name=json_data['name'],
                street1=json_data['address']['line1'],
                city=json_data['address']['city'],
                state=json_data['address']['state'],
                zip=json_data['address']['postal_code'],
                country=json_data['address']['country']
            )

            parcel = components.ParcelCreateRequest(
                length=rand.randint(1, 10),
                width=rand.randint(1, 10),
                height=rand.randint(1, 10),
                distance_unit="cm",
                weight=rand.randint(1, 10),
                mass_unit="kg"
            )

            shipment = shippo_sdk.shipments.create(
                components.ShipmentCreateRequest(
                    address_from=address_from,
                    address_to=address_to,
                    parcels=[parcel],
                    async_=False
                )
            )

            logging.info("Shipment created")
            logging.info(shipment)

        except Exception as e:
            logging.error(f"Error creating shipment: {e}")
            return func.HttpResponse(status_code=500)

    except Exception as e:
        logging.error(f"Error connecting to blob storage: {e}")
        return func.HttpResponse(status_code=500)

