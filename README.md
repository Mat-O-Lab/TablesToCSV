# TablesToCSV
Aims to convert tables in PDFs or Excel Spreadsheets to a uniform CSV format

# CONTENTS OF THIS README
1) REQUIREMENTS: Things you need to get done, before you can use this web app.
2) HOW TO USE THE APP: Simple instructions on how to navigate and use the app.
3) EXAMPLE INPUT/OUTPUT: We give an example of a PDF file conversion into CSVs
4) DOCKER: How to start the app with Docker


# REQUIREMENTS 

Please note that this is a "quick and dirty" type of setup. For a clean setup, install all packages
into a virtual environment, using venv or anaconda. Alternatively, one could use Docker. 
<br>

1) Download the repository by either cloning the repository with git

```cmd

git clone https://github.com/Mat-O-Lab/TablesToCSV.git
```

or download the repository as .zip file and unpack it to a location of your choice.


2) Install python 3.8 or newer : https://www.python.org/downloads/

3) If not done already, you should add the path to python.exe to your PATH.
   To do so, either tick the box while installing python or adjust the environment variables on your machine.
   
4) Navigate to the directory in which you have unpacked/stored a copy of this repository. Start a terminal in this directory.
To do this in Windows, type "cmd" into the path-bar at the top of your file explorer and hit the Enter key.
![cmd_in_explorer](https://user-images.githubusercontent.com/72997461/149930925-0a5ff53d-a318-4224-9b78-b14a5b7b90a3.png)

5) Use pip, the package manager included in your python download, to install all required packages. To
   do this, open up a terminal and type in the command:

```cmd
python -m pip install -r requirements.txt
```

6) To start the local server, simply type the following command:

```cmd
python wsgi.py
```
7) Inside your terminal, some info text should appear, informing you about the state of startup.
![startup_info](https://user-images.githubusercontent.com/72997461/149931849-f51123d1-2bbb-4f0d-944c-2868c11a3d4b.png)

8) Open a web browser, and enter the marked URL into your browsers search bar.
    A small web app should appear.
    
# HOW TO USE THE APP

1) The web app can convert PDF and Excel files into a zip folder of CSV files. To begin, choose whether to convert PDFs or Excel files, by clicking the button.

![choose_conversion](https://user-images.githubusercontent.com/72997461/155974816-b8325d29-dde1-4dfa-a25b-91fd4c7f973a.png)

2) Paste your URLs to the respective fields. Please note that, at the current state, only web-resources are allowed for conversion, pasting the path of a local file
into the url-field will lead to an error message. In this case, simply hit the "back-page" key and try with a different resource.

![pdf_conversion_example](https://user-images.githubusercontent.com/72997461/155974753-6aa44fe1-b4a1-4b63-b982-b1e83b88f3a1.png)

2.1) Alternatively, you can use the "toggle manual" button at the bottom of the page to parse the PDF file without a .json settings file. In this case, you will have to provide
additional information required to parse the PDF.

3) When you have filled in all required information, you can proceed, by clicking the "Start Conversion" button. (The parsing may take a few seconds)

![start_conversion](https://user-images.githubusercontent.com/72997461/155975760-d059d2ef-0fad-40e4-8cf5-2fc6b2871a7a.png)

4) You will receive parsing information in case tables in your PDF file couldn't meet the given parsing accuracy threshold. Finally, a "Download" button should
appear. Hit the button to download the zipped CSVs.

# EXAMPLE INPUT/OUTPUT

Here, we will give a brief example of an input with the corresponding output. We will be converting a PDF file
to a number of CSV files with the help of a JSON settings file. Alternatively, we could use the manual settings, in case
we do not have a settings.json file at our disposal. (click on the links to view the files)

1) An example of a PDF file can be seen under this URL:
https://github.com/Mat-O-Lab/TablesToCSV/blob/PDF-to-CSV/PDFtoCSV/PDFs/C85C_1.pdf

2) An example of a settings file can be seen here:
https://github.com/Mat-O-Lab/TablesToCSV/blob/PDF-to-CSV/PDFtoCSV/settings/C85C_1.json

3) We provide these URLs to the web app and hit the "Start conversion" Button.
![example](https://user-images.githubusercontent.com/72997461/156362496-86da985b-8bd4-4ae1-97d6-052ac01ffe7d.png)

4) By hitting the "Download" Button, we can download a .zip file to our local machine.

5) Use your zip-tool of choice (in case you don't have one: https://www.7-zip.de/) to extract the CSVs. Open the unzipped folder.
You should find a number of CSV files inside. Use a text editor or excel to open the files.

A resulting CSV file should have the following form
```text
"","Datum","Uhrzeit","E<s>t</s>MPa","<s>M</s>MPa","<s>M</s>%","b  mm","h   mm","A<s>0</s>  mm²","Angaben zum Bruch"
"Probe 1","17.09.2020","13:22:49","532.89","33.54","135.56","9.97","4.02","40.05","Bruch Mitte"
"Probe 2","17.09.2020","13:44:11","517.66","33.04","135.75","9.97","4.02","40.08","Bruch Mitte"
"Probe 3","17.09.2020","14:07:31","400.12","32.47","132.86","9.96","4.02","40.05","Bruch Mitte"
"Probe 4","18.09.2020","08:38:29","480.07","33.46","143.23","9.99","4.01","40.08","Bruch Mitte"
"Probe 5","18.09.2020","09:00:54","344.63","34.82","147.06","9.99","4.02","40.18","Bruch Mitte"
"Probe 6","18.09.2020","09:23:25","403.46","32.13","130.45","9.99","4.01","40.08","Bruch Mitte"
"Probe 7","18.09.2020","09:42:21","394.21","31.95","132.92","9.98","4.04","40.35","Bruch Mitte"
"Probe 8","18.09.2020","10:02:36","497.21","34.95","158.92","9.97","4.01","40.00","Bruch Mitte"
"Probe 9","18.09.2020","10:26:30","367.99","30.87","123.88","9.97","4.02","40.08","Bruch Mitte"
"Probe 10","18.09.2020","10:45:35","636.65","34.49","154.33","9.98","4.03","40.20","Bruch Mitte"
```

6) You are done! Happy converting!

# DOCKER
Clone the repo with 
```bash
git clone https://github.com/Mat-O-Lab/TablesToCSV.git
```
Change to the cloned directory
```bash
cd TablesToCSV
```
Build and start the container.
```bash
docker-compose build
```
```bash
docker-compose up
```
