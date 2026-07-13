import logging
logging.basicConfig(level=logging.DEBUG)

from backend import model_service

import os
if "TESTING" in os.environ:
    del os.environ["TESTING"]

service = model_service.ModelService()
service.initialize()
print(service.health_check())
