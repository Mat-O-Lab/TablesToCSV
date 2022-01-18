# TablesToCSV
Aims to convert tables in pds or Excel Spreedsheets to a uniform CSV format

# REQUIREMENTS

1) Download the repository by either cloning the repository with git

```cmd

git clone https://github.com/Mat-O-Lab/TablesToCSV.git
```

or download the repository as .zip file and unpack it to a location of your choice.


2) Install python 3.8 or newer : https://www.python.org/downloads/

3) If not done already, you should add the path to python.exe to your PATH.
   To do so, either tick the box while installing python or adjust the environment variables on your machine.
   
4) Use pip, the package manager included in your python download to install all required packages. To
   do this, open up a terminal and type in the command:

```cmd
pip install -r requirements.txt
```
or

```cmd
python -m pip install -r requirements.txt
```

5) After installing all requiered packages, you are ready to start the server. Navigate to the directory in
which you have unpacked/stored a copy of this repository. Start a terminal in this directory.
To do this in Windows, type "cmd" into the path-bar at the top of your file explorer.
![cmd_in_explorer](https://user-images.githubusercontent.com/72997461/149930925-0a5ff53d-a318-4224-9b78-b14a5b7b90a3.png)

6) A terminal should have opened. To start the local server, simply type the following command:

```cmd
python wsgi.py
```
7) Inside your terminal, some infotext should appear, informing you about the state of startup.
![startup_info](https://user-images.githubusercontent.com/72997461/149931849-f51123d1-2bbb-4f0d-944c-2868c11a3d4b.png)

8) Open a webbrowser, and enter the marked URL into your browsers searchbar.
    A small webapp should appear.
    
# HOW TO USE THE APP

The webapp can convert excel files into a zip folder of csv files. All excel sheets within a given excel file
are converted to csv files (sheets only containing plots are omitted). <br>

To start the conversion, paste the URL of your web-resource into the url-field of the webapp and hit the "Start Conversion" button.

![app_example](https://user-images.githubusercontent.com/72997461/149933370-e6d17ac1-72f6-40d6-bf41-f061eaddd928.png)

Please note that, at the current state, only web-resources are allowed for conversion, pasting the path of a local excel file
into the url-field will lead to an error message. In this case, simply hit the "back-page" key and try with a different resource.
