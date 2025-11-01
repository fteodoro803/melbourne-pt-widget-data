from flask import Request
from main import cloud_update_gtfs  # replace with actual module name

# Simple mock request
class MockRequest:
    def __init__(self, args=None, json=None):
        self.args = args or {}
        self.json = json or {}

# Call the function with a mock request
if __name__ == "__main__":
    request = MockRequest()
    response, status = cloud_update_gtfs(request)
    print(f"Status: {status}")
    print(f"Response: {response}")
