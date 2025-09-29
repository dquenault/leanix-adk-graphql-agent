import os
import requests
import json
import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent

LEANIX_API_TOKEN = os.getenv('LEANIX_API_TOKEN')
LEANIX_SUBDOMAIN = os.getenv('LEANIX_SUBDOMAIN')
LEANIX_GRAPHQL_URL = f'https://{LEANIX_SUBDOMAIN}.leanix.net/services/pathfinder/v1/graphql'
LEANIX_OAUTH2_URL = f'https://{LEANIX_SUBDOMAIN}.leanix.net/services/mtm/v1/oauth2/token'


def _obtain_access_token() -> str:
    """Obtains a LeanIX Access token using the Technical User generated
    API secret.

    Returns:
        str: The LeanIX Access Token
    """
    if not LEANIX_API_TOKEN:
        raise Exception('A valid token is required')
    response = requests.post(
        LEANIX_OAUTH2_URL,
        auth=("apitoken", LEANIX_API_TOKEN),
        data={"grant_type": "client_credentials"},
    )
    response.raise_for_status()
    return response.json().get('access_token')


def get_fact_sheets(app_name: str) -> dict:
    """Returns the result of a query against the LeanIX GraphQL API
    which holds all of our application data.

    Args:
        app_name (str): The name of the application or substring that we want to find

    Returns:
        dict: status and result or error msg.
    """
    access_token = _obtain_access_token()
    graphql_query = """{
        allFactSheets(
            filter: {facetFilters: {facetKey: "FactSheetTypes", keys: "Application"}, fullTextSearch: "f{app_name}"}  
        ) {
            totalCount
            edges {
                node {
                    id
                    name
                }
            }
        }
    }"""

    data = {'query': graphql_query}
    auth_header = f'Bearer {access_token}'

    response = requests.post(
        url=LEANIX_GRAPHQL_URL,
        headers={'Authorization': auth_header},
        data=json.dumps(data)
    )
    response.raise_for_status()
    print(response.json())
    return {"status": "success", "response": response.json()}



root_agent = Agent(
    name="leanIX_application_query_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to answer questions about the Fletcher Building application landscape."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about what applications we have within our landscape and give details of their relationships to other entities."
    ),
    tools=[get_fact_sheets],
)