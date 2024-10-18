from flask import Flask
from flasgger import Swagger

app = Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'My API',
    'uiversion': 3
}
swagger = Swagger(app)

@app.route('/')
def index():
    """Example Endpoint"""
    return "Hello World!"

@app.route('/<id>')
def url_direct(id):
    return id
    # to implement: search database to see if the ID exists
    # if it exists, get the url from the website and redirect from there
    # if it does not exist, throw a 404 error to the user 

@app.route('/create', methods=('POST'))
def create_url():
    return 42
    # get url from post request 
    # generate shortened link alias
    # put into database 
