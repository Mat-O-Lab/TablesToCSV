# TablesToCSV
Aims to convert tables in pds or Excel Spreedsheets to a uniform CSV format

# REQUIREMENTS 

Please note that this is a "quick and dirty" type of setup. For a clean setup, install all packages
into a virtual evironment, using venv or anaconda. Alternatively one could use Docker. 
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

5) Use pip, the package manager included in your python download to install all required packages. To
   do this, open up a terminal and type in the command:

```cmd
python -m pip install -r requirements.txt
```

6) To start the local server, simply type the following command:

```cmd
python wsgi.py
```
7) Inside your terminal, some infotext should appear, informing you about the state of startup.
![startup_info](https://user-images.githubusercontent.com/72997461/149931849-f51123d1-2bbb-4f0d-944c-2868c11a3d4b.png)

8) Open a webbrowser, and enter the marked URL into your browsers searchbar.
    A small webapp should appear.
    
# HOW TO USE THE APP

1) The webapp can convert pdf and excel files into a zip folder of csv files. To begin, choose whether to convert pdfs or excel files, by clicking the button.

![choose_conversion](https://user-images.githubusercontent.com/72997461/155974816-b8325d29-dde1-4dfa-a25b-91fd4c7f973a.png)

2) Paste your URLs to the respective fields. Please note that, at the current state, only web-resources are allowed for conversion, pasting the path of a local file
into the url-field will lead to an error message. In this case, simply hit the "back-page" key and try with a different resource.

![pdf_conversion_example](https://user-images.githubusercontent.com/72997461/155974753-6aa44fe1-b4a1-4b63-b982-b1e83b88f3a1.png)

2.1) Alternatively, you can use the "toggle manual" button at the bottom of the page to parse the pdf file without a .json settings file. In this case you will have to provide
additional information required to parse the pdf.

3) When you have filled in all required information, you can proceed, by clicking the "Start Conversion" button. (The parsing may take a few seconds)

![start_conversion](https://user-images.githubusercontent.com/72997461/155975760-d059d2ef-0fad-40e4-8cf5-2fc6b2871a7a.png)

4) You will receive parsing information in case tables in your pdf file couldn't meet the given parsing accuracy threshold. Finally, a "Download" button should
appear. Hit the button to download the zipped csvs.

# DOCKER
Clone the repo with 
```bash
git clone https://github.com/Mat-O-Lab/TablesToCSV.git
```
cd into the cloned folder
```bash
cd TablesToCSV
```
Build and start the container.
```bash
docker-compose build
docker-compose up
```
