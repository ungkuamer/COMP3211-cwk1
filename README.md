# stripe-easypost-integration
- `random_addresses.csv` contains 10,000 randomly generated name and address that could be used for testing the function. The file is also used by the test script `stripe-post-test.jmx` in order to generate the test.

## POST request format
``` json
{
    "id": "${id}",
    "data": {
        "object": {
            "customer_details": {
                "name": "${name}",
                "address": {
                    "line1": "${street}",
                    "city": "${city}",
                    "state": "${state}",
                    "postal_code": "${zip}",
                    "country": "${country}"
                }
            }
        }
    }
}
```
