from mangum import Mangum
from api.server import app

handler = Mangum(app)
