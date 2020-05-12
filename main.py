import os
import logging
from time import sleep
from flask import Flask, jsonify, request, make_response
from modules.llp8_annual_form import Lllp8Annual
from modules.llp8_interim_form import Lllp8Interim
from modules.chg_pdf_to_json import ChgOneForm
from credentials import creds

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')

file_handler = logging.FileHandler('error.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


app = Flask(__name__)


@app.route('/api/v1/llp8/annual', methods=['GET', 'POST'])
def parse_annual():

    if request.method == 'POST':

        file_name = request.files['file'].filename
        ref_id = request.form['referenceId']

        client_id = request.headers.get('clientId')
        client_secret = request.headers.get('clientSecret')

        if client_id == creds['clientId'] and client_secret == creds['clientSecret']:

            path = "data/" + file_name
            request.files['file'].save(path)
            sleep(1)
            obj = Lllp8Annual(path)
            try:
                result1 = obj.data_parsing()

                # remove the file
                if os.path.exists(path):
                    os.remove(path)

                return make_response(jsonify({
                    "referenceId": ref_id,
                    result1['fileType']: result1
                }), 200)

            except (AttributeError, IndexError) as e:
                logger.exception('error in parsing {} file in llp8 interim '.format(file_name))
                # remove the file
                if os.path.exists(path):
                    os.remove(path)
                return jsonify({"message": "Parsing Error", "code": 200, "error": str(e)})

        else:
            return jsonify({"message": "Invalid clientId or clientSecret", "code": 401})


@app.route('/api/v1/llp8/interim', methods=['GET', 'POST'])
def parse_interim():

    if request.method == 'POST':

        file_name = request.files['file'].filename
        ref_id = request.form['referenceId']

        client_id = request.headers.get('clientId')
        client_secret = request.headers.get('clientSecret')

        if client_id == creds['clientId'] and client_secret == creds['clientSecret']:

            path = "data/" + file_name
            request.files['file'].save(path)
            sleep(1)

            obj = Lllp8Interim(path)
            try:
                result1 = obj.data_parsing()
                # remove the file
                if os.path.exists(path):
                    os.remove(path)

                return make_response(jsonify({
                    "referenceId": ref_id,
                    result1['fileType']: result1
                }), 200)
            except (AttributeError, IndexError) as e:
                logger.exception('error in parsing {} file in llp8 interim '.format(file_name))
                # remove the file
                if os.path.exists(path):
                    os.remove(path)
                return jsonify({"message": "Parsing Error", "code": 200, "error": str(e)})

        else:
            return jsonify({"message": "Invalid clientId or clientSecret", "code": 401})


@app.route('/api/v1/chg-1', methods=['GET', 'POST'])
def parse_chg1():

    if request.method == 'POST':

        file_name = request.files['file'].filename
        ref_id = request.form['referenceId']

        client_id = request.headers.get('clientId')
        client_secret = request.headers.get('clientSecret')

        if client_id == creds['clientId'] and client_secret == creds['clientSecret']:

            path = "data/" + file_name
            request.files['file'].save(path)
            sleep(1)

            obj = ChgOneForm(path)
            try:
                result1 = obj.extract_parse_createjson_frompdf()
                # remove the file
                if os.path.exists(path):
                    os.remove(path)

                return make_response(jsonify({
                    "referenceId": ref_id,
                    result1['fileType']: result1
                }), 200)
            except (AttributeError, IndexError) as e:
                logger.exception('error in parsing {} file in llp8 interim '.format(file_name))
                # remove the file
                if os.path.exists(path):
                    os.remove(path)
                return jsonify({"message": "Parsing Error", "code": 200, "error": str(e)})

        else:
            return jsonify({"message": "Invalid clientId or clientSecret", "code": 401})


if __name__ == '__main__':
    app.run(port=5000)


