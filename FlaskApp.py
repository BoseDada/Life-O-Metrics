# -*- coding: utf-8 -*-
"""
Created on Thu Jun 22 16:26:57 2023

@author: Ila
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import io
import random
from flask import Response
from flask_mysqldb import MySQL
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import os
import sys
import io
from glob import glob
import json
import matplotlib.pyplot as plt
import seaborn as sns
import base64

import MySQLdb.cursors
import re


app = Flask(__name__)

app.secret_key = 'aumbhola'
 
 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'adyotmysql'
app.config['MYSQL_DB'] = 'lifeometrics'
 
mysql = MySQL(app)   


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM tb_login WHERE username = % s \
            AND password = % s', (username, password, ))
        loginresult = cursor.fetchone()
        if loginresult:
            session['loggedin'] = True  
            session['id'] = loginresult['id']
            session['username'] = loginresult['username']
            session['name'] = loginresult['name']
            msg = session['name']
            return render_template('home.html', msg=msg)
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg=msg)
 

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('name', None)
    return redirect(url_for('login'))
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and \
        'password' in request.form and 'email' in request.form and \
        'name' in request.form:
        username = request.form['username']
        password = request.form['password']        
        email = request.form['email']
        name = request.form['name']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM tb_login WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Username already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'name must contain only characters and numbers !'
        else:
            cursor.execute('INSERT INTO tb_login VALUES \
            (NULL,% s, % s, %s, %s)', (username, password, email, name))
            mysql.connection.commit()
            msg = 'You have successfully registered to Life-o-Metrics!'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html')



@app.route('/home')
def home():  
    #return render_template('home.html')
    if 'loggedin' in session:
        msg = session['name']
        return render_template("home.html", msg=msg)
    return redirect(url_for('login'))
    


@app.route('/about')
def about():
    if 'loggedin' in session:    
        msg = session['name']
        return render_template('about.html', msg=msg)
    return redirect(url_for('login'))

@app.route('/dailysummary', methods=["GET"])
def dailysummary():
    if 'loggedin' in session:    
    
        step_df = fileread()
        fig = MyHealthStats(step_df)
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)    
        # Encode PNG image to base64 string
        pngImageB64String = "data:image/png;base64,"
        pngImageB64String += base64.b64encode(output.getvalue()).decode('utf8')
        msg = session['name']
        return render_template("dailysummary.html", dsum=pngImageB64String, msg=msg)
    return redirect(url_for('login'))

@app.route('/distcal', methods=["GET"])
def distcal():
    if 'loggedin' in session:    
        step_df = fileread()
        fig = DistCal(step_df)    
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
        
        # Encode PNG image to base64 string
        pngImageB64String = "data:image/png;base64,"
        pngImageB64String += base64.b64encode(output.getvalue()).decode('utf8')
        msg = session['name']
        return render_template("distcal.html",  dcscomp=pngImageB64String, msg=msg)
    return redirect(url_for('login'))

@app.route('/weekenday', methods=["GET"])
def weekenday():
    if 'loggedin' in session:    
        step_df = fileread()
        fig = Weekenday(step_df)    
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
        
        # Encode PNG image to base64 string
        pngImageB64String = "data:image/png;base64,"
        pngImageB64String += base64.b64encode(output.getvalue()).decode('utf8')
        msg = session['name']
        return render_template("weekenday.html",  weekenday=pngImageB64String, msg=msg)
    return redirect(url_for('login'))

@app.route('/steptrend', methods=["GET"])
def steptrend():
    if 'loggedin' in session:    
        fig = jsonprocess()    
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
        
        # Encode PNG image to base64 string
        pngImageB64String = "data:image/png;base64,"
        pngImageB64String += base64.b64encode(output.getvalue()).decode('utf8')
        msg = session['name']
        return render_template("steptrend.html",  steptrend=pngImageB64String, msg=msg)
    return redirect(url_for('login'))

@app.route('/calculatebmi', methods=["POST","GET"])
def calculatebmi():
    if 'loggedin' in session:    
        if request.method == 'POST': 
            weight = request.form['txtweight']
            height = request.form['txtheight']
            bmi = calc_bmi(weight, height)
            result = {
                "output": bmi
            }
            result = {str(key): value for key, value in result.items()}
            return jsonify(result=result)
        else:
            msg = session['name']
            return render_template('calculatebmi.html', msg=msg)
    return redirect(url_for('login'))

def calc_bmi(weight, height):
   from decimal import Decimal
   weight = int(weight)
   height = int(height)   
   mheight = Decimal(height/100)
   mheight = mheight * mheight   
   bmi = weight / mheight   
   bmi = format(bmi, ".2f")
   return str(bmi)

def fileread():
    
    from pandas.plotting import register_matplotlib_converters
    register_matplotlib_converters()
    
    working_directory=os.path.dirname(__file__)
    #script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
        
    samsung_base_dir = working_directory 
    #os.path.join('.')    
    #print (samsung_base_dir)
    
    samsung_dump_dirs = glob(os.path.join(samsung_base_dir, '*'))
    samsung_dump_dir = os.path.basename(samsung_dump_dirs[0])
    print(len(samsung_dump_dirs), 'dumps found, taking first:', samsung_dump_dir)
    # print (samsung_dump_dir)
    samsung_json_paths = glob(os.path.join(samsung_base_dir, 'jsons', '*', '*.json'))
    print(len(samsung_json_paths), 'jsons found')
    
    from pandas.plotting import register_matplotlib_converters
    register_matplotlib_converters()    
       
    samsung_csv_paths = glob(os.path.join(samsung_base_dir, '*.csv'))
    print(len(samsung_csv_paths), 'csvs found')
    
    from IPython.display import display
    from IPython.core.interactiveshell import InteractiveShell
    InteractiveShell.ast_node_interactivity = "all"
    
    sam_readcsv = lambda x: pd.read_csv(x, index_col=None, skiprows=0, header=1)
    all_csv_df = {os.path.basename(j).replace('com.samsung.', ''): sam_readcsv(j) for j in samsung_csv_paths}
    for k, v in all_csv_df.items():
        print(k, 'readings:', v.shape[0])
        display(v.sample(2 if v.shape[0]>2 else 1))
    #     display(v.sample())
    # display(all_csv_df)
        
    step_df = pd.concat([v for k,v in all_csv_df.items() if 'step_daily_trend' in k])
    # fix times
    for c_col in ['create_time', 'update_time']:
        step_df[c_col] = pd.to_datetime(step_df[c_col])
    
    step_df = step_df.sort_values('create_time', ascending = True)
    pd.to_datetime(step_df['create_time'])
    
    return step_df
    
        
def MyHealthStats(step_df):    
    
    fig = Figure()
    fig, ax1 = plt.subplots(1, 1, figsize = (10, 5))
    ax1.plot(step_df['create_time'], step_df['count'], '-', label = 'Steps')
    ax1.plot(step_df['create_time'], step_df['distance'], '-', label = 'Meters')
    ax1.plot(step_df['create_time'], step_df['calorie'], '-', label = 'Calories')
    ax1.legend()
    fig.autofmt_xdate(rotation = 45)
    #ax1.set_xticks(ax1.get_xticks()[::15]);

    #output = io.BytesIO()
    #FigureCanvas(fig).print_png(output)
    #return Response(output.getvalue(), mimetype='image/png')
    return fig

def DistCal(step_df):    
    
    fig = Figure()
    sns_plot = sns.pairplot(hue = 'deviceuuid', data = step_df[['count', 'distance', 'calorie', 'speed', 'deviceuuid']])
    sns_plot.savefig("distcal.png")
    fig = sns_plot.fig   
    return fig

def Weekenday(step_df):  
    fig=Figure()
    step_df['day_name'] = step_df['create_time'].dt.day_name()
    step_df['is_weekend'] = step_df['day_name'].map(lambda x: 'Weekend' if x in ['Saturday', 'Sunday'] else 'Weekday')
    sns_plot = sns.pairplot(hue = 'is_weekend', data = step_df[['count', 'distance', 'calorie', 'speed', 'day_name', 'is_weekend']])
    sns_plot.savefig("weekenday.png")
    fig = sns_plot.fig   
    return fig

def jsonprocess():
    
    from pandas.plotting import register_matplotlib_converters
    register_matplotlib_converters()
    
    working_directory=os.path.dirname(__file__)
    #script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
        
    samsung_base_dir = working_directory 
    #os.path.join('.')    
    #print (samsung_base_dir)
    
    samsung_dump_dirs = glob(os.path.join(samsung_base_dir, '*'))
    samsung_dump_dir = os.path.basename(samsung_dump_dirs[0])
    print(len(samsung_dump_dirs), 'dumps found, taking first:', samsung_dump_dir)
    # print (samsung_dump_dir)
    samsung_json_paths = glob(os.path.join(samsung_base_dir, 'jsons', '*', '*.json'))
    print(len(samsung_json_paths), 'jsons found')
    
    from itertools import groupby, chain    
    sam_json_dict = {}
    
    # samsung_json_paths
    for fold_id, files in groupby(samsung_json_paths, lambda x: os.path.basename(os.path.dirname(x)).replace('com.samsung.', '')):
        c_files = list(files)
        
    #     print(samsung_json_paths)
    #     print (fold_id)    
        c_json_data = [json.load(open(c_file, 'r')) for c_file in c_files]
        sam_json_dict[fold_id] = list(chain(*c_json_data)) if isinstance(c_json_data[0], list) else c_json_data    
    
    step_df = pd.DataFrame(sam_json_dict['shealth.step_daily_trend'])
    fig=Figure()
    sns_plot = sns.pairplot(step_df)
    sns_plot.savefig("stepdaily.png")
    fig = sns_plot.fig   
    return fig

if __name__ == '__main__':
    app.run(debug=True, port=9099)
