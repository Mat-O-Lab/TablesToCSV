
import pandas as pd
import numpy as np
import os
import zipfile
from timeit import default_timer as timer

import requests
from pdf import coordinates_copy
from pdf.converter_pdf import *
from pdf.converter_pdf import OUTPUT_DIR
from os import remove
from io import BytesIO
from flask import flash, Flask, request, render_template, send_file, url_for, redirect
from flask_swagger_ui import get_swaggerui_blueprint
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from wtforms import StringField, SubmitField

from wtforms.validators import DataRequired, URL


from werkzeug.utils import secure_filename
from config import config

ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'pdf'}
ACCURACY_THRESHOLD = 95 # percent
config_name = os.environ.get("APP_MODE") or "development"

app = Flask(__name__)
app.config.from_object(config[config_name])

bootstrap = Bootstrap(app)


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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class ExcelForm(FlaskForm):
    data_url = StringField("Excel to csv", validators=[DataRequired(), URL()], description='Paste URL to a excel file containing data-sheets')

class PdfForm(FlaskForm):
    data_url = StringField("Pdf to csv", validators=[DataRequired(), URL()], description='Paste URL to a text based pdf file containing tables')
    settings = StringField("Settings", validators=[DataRequired(), URL()], description='Paste URL to a json settings file, matching the pdf')
    submit = SubmitField("Start Conversion")

@app.route('/', methods=['GET', 'POST'])
def index():
    logo = './static/resources/MatOLab-Logo.svg'
    start_form = ExcelForm()
    pdf_form = PdfForm()
    return render_template("index.html", logo=logo, start_form=start_form, pdf_form=pdf_form)

@app.route("/excalibur", methods=["GET", "POST"])
def excalibur():
    flash("redirect to excalibur webapp", "info")
    return redirect(url_for("index"))

@app.route("/api/pdf_to_csv", methods=["GET", "POST"])
def pdf_to_csv():
    if request.method == 'POST':
        url = request.form.get("data_url")
        settings = request.form.get("settings")

        if not url.endswith('.pdf'):
            flash("cannot convert file with given extension!", "info")
            return redirect(url_for("index"))

        if not settings.endswith('.json'):
            flash("settings file was not given as .json file!", "info")
            return redirect(url_for("index"))

        start = timer()
        # we need to access the raw file from github, without html code
        if "github.com" in url:
            url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

        if "github.com" in settings:
            settings = settings.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

        pdf_filename = secure_filename(url.rsplit("/", maxsplit=1)[1])
        settings_filename = secure_filename(settings.rsplit("/", maxsplit=1)[1])


        # write the files to local directory, the files are deleted again after conversion
        response = requests.get(url)
        output = open(pdf_filename, 'wb')
        output.write(response.content)
        output.close()

        response = requests.get(settings)
        output = open(settings_filename, 'wb')
        output.write(response.content)
        output.close()

        # TODO: incorporate into converter_pdf
        tables = coordinates_copy.main(pdf_filename)
        accuracy_list = []
        table_count = 0
        for page, table_areas, image_size in tables:
            bounding_box = convert_pixel_to_point(table_areas, image_size)
            accuracy_dict = extract_tables(pdf_filename, settings_filename, page, bounding_box, table_count, False)

            for k,v in accuracy_dict.items():
                if v <= ACCURACY_THRESHOLD:
                    flash(f"parsing {k} was unsuccessful with an accuracy of {v}%", "warning")
                    accuracy_list.append(v)

            table_count += 1

        # collect the csvs into a .zip file, then send the zipfile to the user
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for dirname, subdirs, files in os.walk(OUTPUT_DIR):
                zf.write(dirname)
                for filename in files:
                    zf.write(os.path.join(dirname, filename))
        memory_file.seek(0)

        # we're done with conversion, delete the local file.
        remove(pdf_filename)
        remove(settings_filename)

        # remove all csvs in TMP_OUT
        for dirname, subdirs, files in os.walk(OUTPUT_DIR):
            for file in files:
                os.remove(os.path.join(dirname, file))

        # TODO: get accuracy, time out of conversion and flask message
        end = timer()
        mean_accuracy = np.mean(np.array(accuracy_list))
        time_seconds = end - start  #  millis
        flash(f"completed conversion of {filename} in {time_seconds} seconds, \nwith a mean accuracy of {mean_accuracy}%", "info")
        return send_file(memory_file, attachment_filename='result.zip', as_attachment=True)

    return redirect(url_for("index"))


@app.route("/api/xls_to_csv", methods=["GET", "POST"])
def xls_to_csv():
    if request.method == 'POST':

        url = request.form.get("data_url")
        
        if not allowed_file(url):
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

            prefix = filename.replace(".xls", "")
            
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
        remove(filename)

        return send_file(memory_file, attachment_filename='result.zip', as_attachment=True)

    return redirect(url_for("index"))
