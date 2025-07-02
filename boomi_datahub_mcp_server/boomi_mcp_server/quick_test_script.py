# Quick test script
from boomi_datahub_client import BoomiDataHubClient

client = BoomiDataHubClient()
result = client.query_records_by_parameters(
    universe_id="02367877-e560-4d82-b640-6a9f7ab96afa",
    repository_id="43212d46-1832-4ab1-820d-c0334d619f6f",
    fields=["AD_ID", "ADVERTISER", "PRODUCT"],
    filters=[{"fieldId": "ADVERTISER", "operator": "EQUALS", "value": "Sony"}],
    limit=5
)
print(f"Status: {result.get('status')}")
if result.get('status') == 'success':
    print(f"Records: {len(result.get('data', {}).get('records', []))}")