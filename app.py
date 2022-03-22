
import pandas as pd
import numpy as np
import os
import zipfile
from timeit import default_timer as timer

import json
import requests
import Converter_Camelot
from Converter_Camelot import *
from Converter_Camelot import OUTPUT_DIR, INPUT_DIR
from io import BytesIO
from flask import flash, Flask, request, render_template, send_file, url_for, redirect, send_from_directory, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from wtforms import StringField, SubmitField, DecimalField, BooleanField

from wtforms.validators import DataRequired, URL, NumberRange


from werkzeug.utils import secure_filename
from config import config

ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'pdf'}
ACCURACY_THRESHOLD = 95 # percent
config_name = os.environ.get("APP_MODE") or "production"

app = Flask(__name__)
app.config.from_object(config[config_name])

bootstrap = Bootstrap(app)

logo = './static/resources/MatOLab-Logo.svg'

SWAGGER_URL = "/api/docs"
API_URL = "/static/swagger.json"
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        "app_name": "TablesToCSV"
    }
)



app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

class ExcelForm(FlaskForm):
    data_url = StringField("Excel to csv", validators=[DataRequired(), URL()], description='Paste URL to a excel file containing data-sheets')

class PDF_automatic(FlaskForm):
    data_url = StringField("URL to pdf file", validators=[DataRequired(), URL()],
                           description='Paste URL to a text based pdf file containing tables')
    settings = StringField("URL to .json settings file", validators=[DataRequired(), URL()],
                           description='Paste URL to a settings .json file')
    acc_threshold = DecimalField("Parse accuracy threshold", default=80, validators=[
        NumberRange(min=0, max=100, message="please input a number in range 0-100")],
                                 description="Parse results with an accuracy lower than the given threshold flash a warning message.")
    submit = SubmitField("Start conversion")

class PDF_manual(FlaskForm):
    data_url = StringField("URL to pdf file", validators=[DataRequired(), URL()],
                           description='Paste URL to a text based pdf file containing tables')
    detect_small_lines = DecimalField("Detect small lines", validators=[DataRequired(), NumberRange(min=15, max=100,
                                                                                                    message="please input numbers in range 15-100")],
                                      description="Small lines can be detected by increasing this value: Range 15-100.")
    cut_text = BooleanField("Cut text", default=False, description="cut text along column separators")
    detect_superscripts = BooleanField("Detect Superscripts", default=False,
                                       description="detect super and subscripts in table headers")
    acc_threshold = DecimalField("Parse accuracy threshold", default=80, validators=[
        NumberRange(min=0, max=100, message="please input a number in range 0-100")],
                                 description="Parse results with an accuracy lower than the given threshold flash a warning message.")
    submit = SubmitField("Start Conversion")


def clean_tmp_files():

    # delete local temporary files
    for dirname, subdirs, files in os.walk(OUTPUT_DIR):
        for file in files:
            os.remove(os.path.join(dirname, file))

    for dirname, subdirs, files in os.walk(INPUT_DIR):
        for file in files:
            os.remove(os.path.join(dirname, file))


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html", logo=logo)

@app.route("/excalibur", methods=["GET", "POST"])
def excalibur():
    flash("redirect to excalibur webapp", "info")
    return redirect("https://pypi.org/project/excalibur-py/")

@app.route("/toggle_manual", methods=["GET", "POST"])
def toggle_manual():
    return redirect(url_for("pdf_to_csv", settings_input="manual"))

@app.route("/toggle_automatic", methods=["GET", "POST"])
def toggle_automatic():
    return redirect(url_for("pdf_to_csv", settings_input="automatic"))

@app.route("/send_converted_files", methods=["GET", "POST"])
def send_converted_files():
    """
    This method should only be called after conversion f a pdf file to respective csvs.
    :return: sends the contents of TMP_OUT to the user.
    """

    # check if we have already sent the csvs, in which case, we have already deleted them...
    if os.path.isdir(OUTPUT_DIR):
        if not os.listdir(OUTPUT_DIR):
            flash("App in faulty state, please reload the page and repeat your query.", "info")
            # the output directory is empty, we have already sent and deleted the csvs
            return redirect(url_for("pdf_to_csv", settings_input="automatic"))


    # collect the csvs into a .zip file, then send the zipfile to the user
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for dirname, subdirs, files in os.walk(OUTPUT_DIR):
            zf.write(dirname)
            for filename in files:
                zf.write(os.path.join(dirname, filename))
    memory_file.seek(0)

    return send_file(memory_file, attachment_filename='result.zip', as_attachment=True)


@app.route("/pdf_to_csv/<settings_input>", methods=["GET", "POST"])
def pdf_to_csv(settings_input):
    if settings_input.lower() not in ["manual", "automatic"]:
        return render_template("pdf2csv.html", pdf_form=PDF_automatic(), send_file=False, settings_input=False)

    manual = True if settings_input.lower() == "manual" else False
    pdf_form = PDF_manual() if manual else PDF_automatic()

    if pdf_form.validate_on_submit() and request.method == 'POST':

        # clean out output directory, in case we have old csvs there.
        clean_tmp_files()

        start = timer()
        url = pdf_form.data_url.data

        if "github.com" in url:
            url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

        if manual:
            settings_dict = {
                "split_text": pdf_form.cut_text.data,
                "flag_size": pdf_form.detect_superscripts.data,
                "line_size_scaling": pdf_form.detect_small_lines.data,
                "accuracy_threshold": pdf_form.acc_threshold.data
            }
        else:

            settings = pdf_form.settings.data

            if not url.endswith('.pdf') or not settings.endswith(".json"):
                flash("given urls resolve to files with wrong filetype!", "info")
                return render_template("pdf2csv.html", pdf_form=pdf_form, settings_input=settings_input)

                # we need to access the raw file from github, without html code

            if "github.com" in settings:
                settings = settings.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

            response = requests.get(settings)

            settings_dict = json.load(BytesIO(response.content))
            settings_dict["accuracy_threshold"] = pdf_form.acc_threshold.data

        pdf_filename = secure_filename(url.rsplit("/", maxsplit=1)[1])

        # write the files to local directory, the files are deleted again after conversion
        response = requests.get(url)
        output = open(os.path.join("TMP_PDF", pdf_filename), 'wb')
        output.write(response.content)
        output.close()

        success, parse_report = Converter_Camelot.main(pdf_filename, settings_dict)

        for (key, value) in parse_report:
            flash(f"{key} {value}", "info")

        end = timer()
        flash("Conversion terminated " + ("successfully" if success else "unsuccessfully") + f"in {end - start} seconds.", "info" if success else "warning")


        return render_template("pdf2csv.html", pdf_form=pdf_form, send_file=success, settings_input=settings_input)

    return render_template("pdf2csv.html", pdf_form=pdf_form, settings_input=settings_input)

@app.route("/xls_to_csv", methods=["GET", "POST"])
def xls_to_csv():
    excel_form = ExcelForm()

    if excel_form.validate_on_submit() and request.method == 'POST':

        url = excel_form.data_url.data

        if not url.endswith('.xls') and not url.endswith('.xlsx'):
            flash("cannot convert file with given extension!")
            return redirect(url_for("index"))

        # we need to access the raw file from github, without html code
        if "github.com" in url:
            url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

        filename = secure_filename(url.rsplit("/", maxsplit=1)[1])

        # write the file to local directory, the file is deleted again after conversion
        response = requests.get(url)
        output = open(filename, 'wb')
        output.write(response.content)
        output.close()

        excel_file = pd.ExcelFile(filename)

        memory_file = BytesIO()

        # for each input file, create sheets, for each sheet, try to add csv to zipfile

        with zipfile.ZipFile(memory_file, 'w') as zf:

            prefix = filename.replace(".xls", "").replace(".xlsx", "")

            for sheetname in excel_file.sheet_names:

                try:
                    df = pd.read_excel(excel_file, sheetname)
                    plain_text = df.to_csv(index=False)

                    tmp = secure_filename(prefix + "_" + sheetname + ".csv")
                    zf.writestr(zinfo_or_arcname=tmp, data=plain_text)

                except:
                    # sometimes, excel sheets can't be turned into csv files,e.g. when
                    # the excel sheet contains a diagram. In this case, omit the current sheet
                    continue

        memory_file.seek(0)

        # we're done with conversion, delete the local file.
        excel_file.close()
        os.remove(filename)

        return send_file(memory_file, attachment_filename='result.zip', as_attachment=True)

    return render_template("xls2csv.html", excel_form=excel_form)

@app.route("/api/pdf2csv/<settings_input>", methods=["POST"])
def pdf2csv(settings_input):

    if settings_input.lower() not in ["manual", "automatic"]:
        return jsonify({"parse_report" : ["error, please choose either manual or automatic"]})


    resp = request.get_json()
    settings_dict = {}

    # clean out output directory, in case we have old csvs there.
    clean_tmp_files()

    url = resp["data_url"]

    if "github.com" in url:
        url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

    if settings_input.lower() == "manual":
        settings_dict = {
        "split_text": resp["split_text"],
        "flag_size": resp["flag_size"],
        "line_size_scaling": resp["line_size_scaling"],
        "accuracy_threshold": resp["accuracy_threshold"]}

    else:
        settings = resp["settings"]
        if "github.com" in settings:
            settings = settings.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

        response = requests.get(settings)
        settings_dict = json.load(BytesIO(response.content))
        settings_dict["accuracy_threshold"] = resp["accuracy_threshold"] if resp["accuracy_threshold"] is not None else 80



    pdf_filename = secure_filename(url.rsplit("/", maxsplit=1)[1])

    # write the files to local directory, the files are deleted again after conversion
    response = requests.get(url)
    with open(os.path.join("TMP_PDF", pdf_filename), 'wb') as file:
        file.write(response.content)


    success, parse_report = Converter_Camelot.main(pdf_filename, settings_dict)

    data = {}

    if success:
        for dirname, subdirs, files in os.walk(OUTPUT_DIR):
            for filename in files:
                with open(os.path.join(OUTPUT_DIR, filename), 'r') as file:
                    data[filename.split(".")[0]] = file.read()

    return jsonify({"data": data, "parse_report": parse_report})


@app.route("/api/xls2csv", methods=["POST"])
def xls2csv():
    resp = request.get_json()

    if resp is None or resp["data_url"] is None:
        return None

    url = resp["data_url"]

    if "github.com" in url:
        url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

    filename = secure_filename(url.rsplit("/", maxsplit=1)[1])

    # write the file to local directory, the file is deleted again after conversion
    response = requests.get(url)
    output = open(filename, 'wb')
    output.write(response.content)
    output.close()

    excel_file = pd.ExcelFile(filename)

    ret = {}

    prefix = filename.replace(".xls", "").replace(".xlsx", "")

    for sheetname in excel_file.sheet_names:
        try:
            df = pd.read_excel(excel_file, sheetname)
            plain_text = df.to_csv(index=False)

            key = secure_filename(prefix + "_" + sheetname)
            ret[key] = plain_text

        except:
            # sometimes, excel sheets can't be turned into csv files,e.g. when
            # the excel sheet contains a diagram. In this case, omit the current sheet
            continue

    # we're done with conversion, delete the local file.
    excel_file.close()
    os.remove(filename)

    return jsonify(ret)

@app.route("/redirect_to_api", methods=["GET"])
def redirect_to_api():
    return redirect(SWAGGER_URL)
