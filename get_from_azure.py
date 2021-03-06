import urllib2
# If you are using Python 3+, import urllib instead of urllib2
from pprint import pprint
import json 
from ast import literal_eval

def get_from_azure(userid):
    data = {
            "Inputs": {
                    "input1":
                    {
                        "ColumnNames": ["User"],
                        "Values": [ [ "%s" % userid ] ]
                    },
            },
        }

    body = str.encode(json.dumps(data))

    url = 'https://ussouthcentral.services.azureml.net/workspaces/c5592c8a66474ff5adaba6942e9c5e30/services/2a908e9427c14b71a849234277cf1464/execute?api-version=2.0&details=true'
    api_key = 'vH1Iha3eLLQwCSS15lLQoWKQQr0ufynE4igs2ubOkX6V5EQ35YVHvgLXDlw6AFbi8HDLpbBZb4BUZrrZJ9tHdA==' # Replace this with the API key for the web service
    headers = {'Content-Type':'application/json', 'Authorization':('Bearer '+ api_key)}

    req = urllib2.Request(url, body, headers)

    try:
        response = urllib2.urlopen(req)

        # If you are using Python 3+, replace urllib2 with urllib.request in the above code:
        # req = urllib.request.Request(url, body, headers)
        # response = urllib.request.urlopen(req)

        result = json.load(response)
        return result['Results']['output1']['value']['Values'][0][1:]
    except urllib2.HTTPError, error:
        # print("The request failed with status code: " + str(error.code))
        pass
        # Print the headers - they include the request ID and the timestamp, which are useful for debugging the failure
        # print(error.info())
        # print(json.loads(error.read()))