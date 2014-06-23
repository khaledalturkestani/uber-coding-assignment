from flask import Flask, request, make_response, render_template, json #redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
#from sqlalchemy.orm import validates
import requests
import re
import mandrill
from sent_emails_db import db_session, init_db
from models import SentEmail
#from wtforms import Form, TextField, validators

# TODO:
# - automated tests
# - better UI
# - DB
# - jQuery Form validation
# - Save UNSENT emails
# - Delayed emails

# NOTES:
# do browser validation, application level validation, and DB level validation

# TEST CASES:
# - send empty fields
# - send invalid emails
# - send json missing some fields
# - 

app = Flask(__name__)
#db = SQLAlchemy(app)

# Mailgun variabls:
mailgun_key = "key-9rgronlrp86yfoak85gg0obzqavpzcs4"
mailgun_server = "https://api.mailgun.net/v2/sandboxbc03a6f4ca24417cb61b282883b83697.mailgun.org/messages"

# Mandrill variables:
mandrill_key = "qgGuBRiAtGhrL-vvzjTOmg"


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route("/")
def display_form():
    return render_template("form.html")
   
@app.route("/email", methods=["POST"])
def send_email():
    email_fields = json.loads(request.data)
    errors = []
    fields_validated = validate_email_fields(email_fields, errors)

    # Return 400 status if fields are not valid
#    if not fields_validated:
#    	return make_response(json.dumps(errors), "400", {})

    # Send via Mailgun first:
#    mailgun_response = send_via_mailgun(email_fields)
#    if mailgun_response == 200:
#	email_fields["service"] = "mailgun"
#	email_fields["service_response"] = json.dumps(mailgun_response.json())
#	save_to_db(email_fields)
#    	return make_response()
    
    # Mailgun failed -- Send via Mailgun:
    mandrill_response = send_via_mandrill(email_fields)
    print "-------------------- Mandrill:"
    print mandrill_response
    if mandrill_response[0]["status"] == "sent":
	email_fields["service"] = "mandrill"
	email_fields["service_response"] = json.dumps(mandrill_response[0])
	save_to_db(email_fields)
    	return make_response()

    return make_response("Both email services failed", "400", {})
 
def send_via_mailgun(fields):
    return requests.post(
        mailgun_server,
        auth=("api", mailgun_key),
        data={"from": fields["from_name"] + " <" + fields["from_email"] + ">",
        #data={"from": "someone ",
              "to": fields["to_name"] + " <" + fields["to_email"] + ">",
              "subject": fields["subject"],
              "html": fields["body"]})

def send_via_mandrill(fields):
    try:
    	mandrill_client = mandrill.Mandrill(mandrill_key)
    	message = {
	  "from_email": fields["from_email"],
   	  "from_name": fields["from_name"],
          "to": [{"email": fields["to_email"],
                 "name": fields["to_name"]}],
	  "subject": fields["subject"],
   	  "html": fields["body"]}
   	result = mandrill_client.messages.send(message=message, async=False, ip_pool="Main Pool")
	return result

    except mandrill.Error, e:
    	# Mandrill errors are thrown as exceptions
    	print "A mandrill error occurred: %s - %s" % (e.__class__, e)
    	# A mandrill error occurred: <class "mandrill.UnknownSubaccountError"> - No subaccount exists with the id "customer-123"    
    	raise
       
def save_to_db(f):
    email_model = SentEmail(f["to_name"], f["to_email"], f["from_name"], f["from_email"], f["subject"], f["body"], f["service"], f["service_response"])
    db_session.add(email_model)
    db_session.commit()

def validate_email_fields(f,errors):
    try:
	ret_val = True

	if len(f["to_name"]) == 0 or len(f["to_email"]) == 0 or len(f["from_name"]) == 0 or len(f["from_name"]) == 0 or len(f["subject"]) == 0 or len(f["body"]) == 0:
	    errors.append("Error: Email fields cannot be empty.")
	    ret_val = False

	if not is_valid_email(f["to_email"]) or not is_valid_email(f["from_email"]):
	    errors.append("Error: invalid to/from email address")
	    ret_val = False
	return ret_val

    except KeyError:
	errors.append("Error: Missing some email fields.")
	print "----------------------------------------------- KeyError"
	return False

def is_valid_email(email):
	if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
	    return False
	return True

#class SentEmail(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    to_name = db.Column(db.String(50), nullable=False)
#    to_email = db.Column(db.String(50), nullable=False)
#    from_name = db.Column(db.String(50), nullable=False)
#    from_email = db.Column(db.String(50), nullable=False)
#    subject = db.Column(db.String(100), nullable=False)
#    body = db.Column(db.Text, nullable=False)
#    service = db.Column(db.String(50), nullable=False)
#    service_response = db.Column(db.Text, nullable=False)

    # Simple validation. Checks that theres only one @ followed by a .
    # TODO: check regex
#    @validates("to_email", "from_email")
#    def validate_email(self, key, address):
#	if not re.match(r"[^@]+@[^@]+\.[^@]+", address):
#	    return False
#	return True

#    def __init__(self, to_name, to_email, from_name, from_email, subject, body, service, service_response):
#	self.to_name = to_name
#	self.to_email = to_email
#	self.from_name = from_name
#	self.from_email = from_email
#	self.subject = subject
#	self.body = body
#	self.service = service
#	self.service_response = service_response

if __name__ == "__main__":
    app.debug = True # or: app.run(debug=True).
    init_db()
    app.run()
    #app.run(host="0.0.0.0")
