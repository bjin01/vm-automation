"""
Written by Bo Jin
Github: https://github.com/jinbo01
Email: bo.jin@suseconsulting.ch

The script makes HTTP POST Request to ansible rule-book
"""
import http.client
import json
from suma_actions import get_suma_config

# This function makes http post request to ansible rule book.
def send_post_request(ip_address):
    suma_config = get_suma_config()
    conn = http.client.HTTPConnection(suma_config["ansible_server"], suma_config["ansible_rulebook_port"])
    headers = {"Content-Type": "application/json"}
    payload = json.dumps({"message": ip_address})

    try:
        conn.request("POST", "/endpoint", body=payload, headers=headers)
        response = conn.getresponse()
        print(f"Response: {response.status}, {response.read().decode()}")
        print("Sent message to trigger ansible-rulebook. Done.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

