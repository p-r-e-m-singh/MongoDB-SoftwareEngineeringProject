from __future__ import division, print_function
# coding=utf-8
import sys
import os
import glob
import re
import numpy as np
import tensorflow as tf
import tensorflow as tf
from PIL import Image
from rembg import remove
from pymongo import MongoClient
# Keras
# from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

# Flask utils
from flask import Flask, redirect, url_for, request, render_template
from werkzeug.utils import secure_filename
from datetime import datetime
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask import session
#from gevent.pywsgi import WSGIServer

# Define a flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key'
mongo=MongoClient("mongodb+srv://root:2506@cluster0.3azljoe.mongodb.net/?retryWrites=true&w=majority")
dbb=mongo.get_database("LoginDetails")
user=dbb.get_collection("users")
members=dbb.get_collection("members")
history=dbb.get_collection("history")
app.app_context().push()

db = SQLAlchemy(app)
bcrypt=Bcrypt(app)
uid=None

class Members(db.Model):
    user_id=db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(50), nullable=False)
    username=db.Column(db.String(50), nullable=False)
    password=db.Column(db.String(50), nullable=False)
    date_registered=db.Column(db.DateTime, default=datetime.utcnow)


# db.create_all()

# Model saved with Keras model.save()
MODEL_PATH ='InceptionModel.h5'

# Load your trained model
model = load_model(MODEL_PATH)

def convertToBinaryData(filename):
    
    with open(filename, 'rb') as file:
        blobData = file.read()
    return blobData

def model_predict(img_path, model):
    print(img_path)
    img = image.load_img(img_path, target_size=(224, 224))


    # Preprocessing the image
    x = image.img_to_array(img)
    # x = np.true_divide(x, 255)
    ## Scaling
    x=x/255
    x = np.expand_dims(x, axis=0)
   

    # Be careful how your trained model deals with the input
    # otherwise, it won't make correct prediction!
    # x = preprocess_input(x)
    preds = model.predict(x)
    preds=np.argmax(preds, axis=1)
    if preds==0:
        preds="Tomato Bacterialn Spot"
    elif preds==1:
        preds="Tomato Early Blight"
    elif preds==2:
        preds="Tomato Late Blight"
    elif preds==3:
        preds="Tomato Leaf Mold"
    elif preds==4:
        preds="Tomato Septoria Leaf Spot"
    elif preds==5:
        preds="Tomato Spider mites Two-spotted Spider Mite"
    elif preds==6:
        preds="Tomato Target Spot"
    elif preds==7:
        preds="Tomato Yellow Leaf Curl Virus"
    elif preds==8:
        preds="Tomato Mosaic Virus"
    elif preds==9:
        preds="Healthy"

    # Saving the search history in the database
    # conn=sqlite3.connect('instance/users.db')
    # con=conn.cursor()
    # sqlite_insert_blob_query = " INSERT INTO history (id_user, image_url, disease, date_time) VALUES (?, ?, ?, ?)"

    # empPhoto = convertToBinaryData(img_path)
    # data_tuple = (uid,empPhoto,preds, datetime.now())
    # con.execute(sqlite_insert_blob_query, data_tuple)
    # conn.commit()
    # history.update_one({"_id":uid},{"history":[{"image_url":empPhoto,"disease":preds,"date_time":datetime.now()}]})
    return preds 


@app.route('/predict', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Get the file from post request
        f = request.files['file'] 

        # Save the file to ./uploads
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(
            basepath, 'uploads', secure_filename(f.filename))
        f.save(file_path)
        # removing the background
        inpt=Image.open(file_path)
        if(".jpg" in f.filename):
            temp=f.filename.replace(".jpg",".png")
        elif(".JPG" in f.filename):
            temp=f.filename.replace(".JPG",".png")
        elif(".jpeg" in f.filename):
            temp=f.filename.replace(".jpeg",".png")
        elif(".JPEG" in f.filename):
            temp=f.filename.replace(".JPEG",".png")
        else:
            temp=f.filename
        new_path=os.path.join(basepath,'uploads',secure_filename(temp))
        inpt.save(new_path)
        inpt=Image.open(new_path)
        output=remove(inpt)
        """ fpp=str(file_path)
        if(".jpg" in fpp):
            print(fpp)
            fpp.replace(".jpg",".png") """
        output.save(new_path)
        # Make prediction
        preds = model_predict(new_path, model)
        result=preds
        return result
    return None


def Members_exists(email, username):
    # check if the Members exists in the database
    # return True if the Members exists, False otherwise
    user = Members.query.filter_by(email=email).first(
    ) or Members.query.filter_by(username=username).first()
    return user is not None


def create_Members(email, username, password):
    # create a new Members with the given email, username, and password
    hashed_pas=bcrypt.generate_password_hash(password)
    user = Members(email=email, username=username, password=hashed_pas)
    db.session.add(user)
    db.session.commit()


def check_password(username, password):
    # check if the password is correct for the given username
    # return True if the password is correct, False otherwise
    user = Members.query.filter_by(username=username).first()
    if user is None:
        return False
    conn=sqlite3.connect('instance/users.db')
    con=conn.cursor()
    stat=f"SELECT password FROM members WHERE username='{username}'"
    con.execute(stat)
    if bcrypt.check_password_hash(con.fetchone()[0], password):
        return True
    return False


@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    else:
        return render_template('first.html')


@app.route('/login.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # if check_password(username, password):
        #     session['username'] = username
        #     conn=sqlite3.connect('instance/users.db')
        #     con=conn.cursor()
        #     stat=f"SELECT user_id FROM members WHERE username='{username}'"
        #     con.execute(stat)
        #     global uid
        #     uid=con.fetchone()[0]
        #     print(uid)
        #     return redirect(url_for('home'))
        # else:
        #     return render_template('login.html', err=True)
        loginuser = user.find_one({"username":username})
        passwrd=loginuser['password']
        if bcrypt.check_password_hash(passwrd,password):
            session['username']=username
            global uid
            uid=loginuser['_id']
            return redirect(url_for('home'))
        else:
            return render_template('login.html',err=True)
    else:
        return render_template('login.html')


@app.route('/signup.html', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
    #     if Members_exists(email, username):
    #         return render_template('signup.html', err=True)
    #     else:
    #         create_Members(email, username, password)
    #         session['username'] = username
    #         conn=sqlite3.connect('instance/users.db')
    #         con=conn.cursor()
    #         stat=f"SELECT user_id FROM members WHERE username='{username}'"
    #         global uid
    #         con.execute(stat)
    #         uid=con.fetchone()[0]
    #         return redirect(url_for('home'))
    # else:
    #     return render_template('signup.html')
        exisistinguser=user.find_one({"username":username})
        if exisistinguser is None:
            hash_pass=bcrypt.generate_password_hash(password)
            user.insert_one({"username":username,"email":email,"password":hash_pass})
            loginuser=user.find_one({"username":username})
            global uid
            uid=loginuser['_id']
            members.insert_one({"_id":uid,"full_name":"","mobile_no":"","profession":"","city":"","pre_lang":"","pro_pic":""})
            history.insert_one({"_id":uid,"history":[]})
            session['username']=username
            return redirect(url_for('home'))
        else:
            return render_template('signup.html',err=True)
    else:
        return render_template('signup.html')


@app.route('/profile.html')
def profile():
    # conn=sqlite3.connect('instance/users.db')
    # con=conn.cursor()
    # stat=f"SELECT * FROM members WHERE user_id='{uid}'" 
    # con.execute(stat)
    # m = con.fetchall()
    # stat=f"SELECT * FROM profile WHERE userid='{uid}'"
    # con.execute(stat)
    # p = con.fetchall()
    mm=user.find_one({"_id":uid})
    temp1=(mm["_id"],mm["username"],mm["email"],mm["password"])
    pp=members.find_one({"_id":uid})
    temp2=(pp["_id"],pp["full_name"],pp["mobile_no"],pp["profession"],pp["city"],pp["pre_lang"],pp["pro_pic"])
    m=[temp1]
    p=[temp2]
    return render_template('profile.html', data=zip(m,p))

def writeTofile(data, filename):
    # Convert binary data to proper format and write it on Hard Disk
    with open(filename, 'wb') as file:
        file.write(data)

@app.route('/history.html')
def history():
    conn=sqlite3.connect('instance/users.db')
    con=conn.cursor()
    stat=f"SELECT * FROM history WHERE id_user='{uid}'"
    con.execute(stat)
    data = con.fetchall()
    img=[]
    for i in data:
        n=str(i[0])
        # photoPath = "C:/Users/Sony/Documents/SoftwareEngineeringProject-PlantDiseaseDetection/static/profile_image/" +n + ".jpg" 
        photoPath = "uploads/" +n + ".jpg" 
        writeTofile(i[2], photoPath)
        img+=(photoPath,)
        # img+=(n+".jpg",)
    print(img)
    return render_template('history.html', logs=zip(data, img))

@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/contact.html')
def contact():
    return render_template('contact.html')

@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    if request.method == 'POST':
        data = request.get_json()
        uname = data[0]['name']
        job = data[1]['job']
        city = data[2]['city']
        phone = data[3]['phone']
        print(uname, job, city, phone)
        if(uname==None or job==None or city==None):
            return render_template('profile.html', err=True)
        # conn=sqlite3.connect('instance/users.db')
        # con=conn.cursor()
        # sq=f"DELETE FROM profile WHERE userid={uid}"
        # con.execute(sq)
        # sqlite_insert_blob_query = " INSERT INTO profile (userid, full_name, mobile_no, profession,city,pre_lang,pro_pic) VALUES (?, ?, ?, ?, ?, ?, ?)"
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(
            basepath, 'img',"farmer-image.png")
        empPhoto = convertToBinaryData("/home/pritam/Documents/SoftwareEngineeringProject-PlantDiseaseDetection/img/farmer-image.png")
        print(uid) 
        data_tuple = (uid,uname, phone, job,city,"ENGLISH",empPhoto)
        members.update_one({"_id":uid},{"$set":{"full_name":uname,"mobile_no":phone,"profession":job,"city":city,"pre_lang":"ENGLISH","pro_pic":empPhoto}})
        # members.find_one_and_delete({"_id":uid})
        # members.insert_one({"_id":uid,"full_name":uname,"mobile_no":phone,"profession":job,"city":city,"pre_lang":"ENGLISH","pro_pic":empPhoto})
        # con.execute(sqlite_insert_blob_query, data_tuple)
        # conn.commit()
        # stat=f"SELECT * FROM profile WHERE userid='{uid}'"
        # con.execute(stat)
        # data = con.fetchall()
        finduser=members.find_one({"_id":uid})
        temp=(finduser["_id"],finduser["full_name"],finduser["mobile_no"],finduser["profession"],finduser["city"],finduser["pre_lang"],finduser["pro_pic"])
        data=[temp]
        return render_template('profile.html', data=data)
    else:
        return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template('first.html')

app.run(debug=True)