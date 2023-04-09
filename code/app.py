from flask.globals import request
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import engine
from sqlalchemy.orm import sessionmaker
from project_orm import User
from utils import *
from flask import Flask, render_template,send_from_directory,url_for, flash, session, redirect,abort
from flask_uploads import UploadSet, IMAGES, configure_uploads
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired , FileAllowed 
from wtforms import SubmitField
import tensorflow as tf
import numpy as np
from PIL import Image
from werkzeug.utils import secure_filename 

app = Flask(__name__)
app.secret_key = "the basics of life with python"
app.config['UPLOADED_PHOTOS_DEST'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 10 # 2MB
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.bmp']
app.config['UPLOAD_PATH'] = 'uploads'


photos = UploadSet ('photos',   IMAGES)
configure_uploads(app, photos)


def predict_image_class(image_path, model_path):
    # Load the model
    model = tf.keras.models.load_model(model_path)
    # Get the image and resize it
    img = Image.open(image_path)
    img = img.resize((224, 224))
    # Convert the image to a numpy array
    img_array = np.array(img)
    # Add an extra dimension to the array to match the model's input shape
    img_array = np.expand_dims(img_array, axis=0)
    # Normalize the pixel values
    img_array = img_array / 255.0
    # Make the prediction
    prediction = model.predict(img_array)
    # Get the predicted class label
    class_label = np.argmax(prediction)
    return class_label

class UploadForm(FlaskForm):
            photo= FileField(
                validators=[
                FileAllowed(photos,'Only images are allowed'),
                FileRequired('File field should not be empty')]
            )
            submit = SubmitField('Upload')

def open_db():
    engine = create_engine('sqlite:///database.db')
    Session = sessionmaker(bind=engine)
    return Session()

@app.route('/',methods=['GET','POST'])
def index():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email and validate_email(email):
            if password and len(password)>=6:
                try:
                    sess = open_db()
                    user = sess.query(User).filter_by(email=email,password=password).first()
                    if user:
                        session['isauth'] = True
                        session['email'] = user.email
                        session['id'] = user.id
                        session['name'] = user.name
                        del sess
                        flash('login successfull','success')
                        return redirect('/home')
                    else:
                        flash('email or password is wrong','danger')
                except Exception as e:
                    flash(e,'danger')
    return render_template('index.html',title='login')

@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        cpassword = request.form.get('cpassword')
        if name and len(name) >= 3:
            if email and  validate_email(email):
                if password and len(password)>=6:
                    if cpassword and cpassword == password:
                        try:
                            newuser = User(name=name,email=email,password=password)
                            sess = open_db()
                            sess.add(newuser)
                            sess.commit()
                            sess.close()
                            del sess
                            flash('registration successful','success')
                            return redirect('/')
                        except:
                            flash('email account already exists','danger')
                    else:
                        flash('confirm password does not match','danger')
                else:
                    flash('password must be of 6 or more characters','danger')
            else:
                flash('invalid email','danger')
        else:
            flash('invalid name, must be 3 or more characters','danger')
    return render_template('signup.html',title='register')

@app.route('/forgot',methods=['GET','POST'])
def forgot():
    return render_template('forgot.html',title='forgot password')

@app.route('/home',methods=['GET','POST'])
def uploader():
    if session.get('isauth'):
        form = UploadForm()
        if form.validate_on_submit():
            filename = photos.save(form.photo.data)           
            # request.files[form.photo.name].save(app.config['UPLOAD_PATH']+filename)
            session['luf'] = filename
            file_url = url_for('get_file',filename=filename)
            print(f'filename  = {filename}')
            save_file(request)
        else:
            file_url= None
        return render_template('home.html', form=form, file_url=file_url) 
    else:
        flash('login to continue','djanger')
        return redirect('/')
    
def save_file(request):
    import os
    print(request.files)

    # filename = secure_filename(photo.name)              # clean the filename n store it in variable
    # if filename != '':                                              # if the filename is not empty then
    #     file_ext = os.path.splitext(filename)[1]                    # get the extension from filename abc.png ['abc','.png']
    #     if file_ext not in app.config['UPLOAD_EXTENSIONS']:         # if extension is not valid
    #         abort(400)                                              # then stop execution else
    #     path = os.path.join(app.config['UPLOAD_PATH'],filename)     # make os compatible path string
    #     photo.save(path)                                    # then save the file with original name 

@app.route('/predict')
def prediction():
    if 'luf' in session:
        file_url = url_for('get_file'   ,filename=session['luf'])
        model_path = "models/model.h5"
        result = predict_image_class('uploads/'+session['luf'], model_path)
        return render_template('predict.html', result=result)
    else:
        return redirect('/home')

@app.route('/uploads/<filename>')
def get_file(filename):
    return send_from_directory(app.config['UPLOADED_PHOTOS_DEST'],filename)

@app.route('/about')
def about():
    return render_template('about.html',title='About Us')

@app.route('/logout')
def logout():
    if session.get('isauth'):
        session.clear()
        flash('you have been logged out','warning')
        
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True,threaded=True)
