from flask import jsonify, abort, Flask
from mylocalpackages.functions import ask_questions
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# We set the limit:
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["500 per minute", "100 per second"],)

# We set the limit again:
@app.route("/")
@limiter.limit("500 per minute", "100 per second")

def create_python_queries(request, decoded_token=None):

    data = request.json.get("data")
    name = data["name"]


    # We create the questions:
    questions = {"": ""}
    try:
        list_args = name.split(";")
        storageId = list_args[0]
        pags = args_list[1]
        delete_pages = args_list[2]
        pdf_url = list_args[3]

        if(pdf_url.startswith("https://firebasestorage.googleapis.com/v0/b/fastest-e5579.appspot.com")):
            questions = ask_questions(
                storageId, pags, delete_pages, pdf_url)
    except Exception as error:
        print("error: "+str(error))
        questions = {"": ""}

    return jsonify({
        "data": {
            "name": questions
        }
    })
