"""AWS Lambda entry point: the FastAPI app behind a Function URL.

Mangum translates the Function URL event (payload format 2.0) into ASGI and
back, so `sdoc.api:app` runs unchanged. Lifespan events are off because the
app has none and Lambda has no long-lived process to run them in.

Lambda handler setting: `sdoc.lambda_handler.handler`
"""
from mangum import Mangum

from .api import app

handler = Mangum(app, lifespan="off")
