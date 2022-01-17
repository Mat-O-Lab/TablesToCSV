
import pandas as pd
import os
import zipfile

import requests

from os import remove
from io import BytesIO
from flask import flash, Flask, request, render_template, send_file, url_for, redirect
from flask_swagger_ui import get_swaggerui_blueprint
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from wtforms import StringField

from wtforms.validators import DataRequired, URL


from werkzeug.utils import secure_filename
from config import config

ALLOWED_EXTENSIONS = {'xls', 'xlsx'}
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

class StartForm(FlaskForm):
    data_url = StringField('URL to xls file', validators=[DataRequired(), URL()], description='Paste URL to a excel file containing data-sheets')

@app.route('/', methods=['GET', 'POST'])
def index():
    logo = './static/resources/MatOLab-Logo.svg'
    start_form = StartForm()
    return render_template("index.html", logo=logo, start_form=start_form)

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
