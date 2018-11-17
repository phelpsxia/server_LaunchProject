from flask import Flask,render_template,request, url_for,redirect
from flask import Response, request
from flask_bootstrap import Bootstrap
from flask_socketio import SocketIO, emit
import time,json
import os, os.path
import requests
from PIL import Image
import base64
import numpy as np
import cv2
from io import BytesIO
import MySQLdb

# Import smtplib for the actual sending function
import smtplib
import random
# Import the email modules we'll need
from email.mime.text import MIMEText
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.ticker as ticker
 
app = Flask(__name__,static_folder='static')
app.config['SECRET_KEY'] = 'Diversita'

socketio = SocketIO(app)
Bootstrap(app)
color_list = ['k', 'r', 'y', 'g', 'c', 'b', 'm']
db = MySQLdb.connect("localhost", "root", "2018_diversita_2018", "diversita", charset='utf8' )
uploadWebAddr = 'https://aiforearth.azure-api.net/species-recognition/v0.1/predict'

headers = {
    # Request headers
    'Content-Type': 'application/octet-stream',
    'Ocp-Apim-Subscription-Key': '{subscription key}',
}

def rendering_box(l, img):
    image = mpimg.imread(img)
    #count = 0
    dpi = 100
    score_l = []

    print(image.shape)
    imageHeight, imageWidth = image.shape[0:2]
    figsize = imageWidth / float(dpi), imageHeight / float(dpi)
    fig = plt.figure(figsize=figsize)
    ax = plt.axes([0,0,1,1])

        # Display the image
    ax.imshow(image)
    ax.set_axis_off()
    
    
    rect = patches.Rectangle((float(l['x_min']),float(l['y_min'])),float(l['x_max']) - float(l['x_min']),float(item['y_max']) - float(item['y_min']),linewidth=3,edgecolor=color_list[count],facecolor='none')
        # Add the patch to the Axes
    ax.add_patch(rect)

    # This is magic goop that removes whitespace around image plots (sort of)        
    plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
    plt.margins(0,0)
    ax.xaxis.set_major_locator(ticker.NullLocator())
    ax.yaxis.set_major_locator(ticker.NullLocator())
    ax.axis('tight')
    ax.set(xlim=[0,imageWidth],ylim=[imageHeight,0],aspect=1)
    plt.axis('off')                
    
    # plt.savefig(outputFileName, bbox_inches='tight', pad_inches=0.0, dpi=dpi, transparent=True)
    plt.savefig(img, dpi=dpi, transparent=True)
    print ('done!')

@app.route('/',methods=["GET", "POST"])
def main():
    return redirect(url_for('login'))
  
@app.route('/login',methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        page_status = request.form['status']

        if page_status == 'signup':
            userName = request.form['username']
            email = request.form['email']
            password = request.form['password']
            uid_token = request.form['uuid']
            notification_token = request.form['token']

            cursor = db.cursor()
            sql = "SELECT USERID FROM USERINFO"
            
            try:
                cursor.execute(sql)
                results = cursor.fetchall()
                for row in results: 
                    if row[0] == userName:
                        return 'username exist'
                
                cursor = db.cursor()
                sql = "INSERT INTO USERINFO(USERID, PASSWORD, EMAIL) \
                    VALUES ('%s', '%s', '%s')" % \
                    (userName, password, email)

                try:
                    cursor.execute(sql)
                    db.commit()
                    s = 1

                except:
                    db.rollback()
                    s = 0
                
                if s == 1:
                    cursor = db.cursor()
                    sql = "INSERT INTO TOKENLIST \
                        VALUES ('%s', '%s', '%s')" % \
                        (userName, uid_token, notification_token)
                
                    try:
                        cursor.execute(sql)
                        db.commit()
                        return render_template('main.html') 
                    
                    except:
                        db.rollback()
                        return 'retry_die at insert into tokenlist'
                
                else:
                    return 'retry_die at insert into userinfo'
            
            except:
                return 'retry_die at fetching user date'

        if page_status == 'login':
            userName = request.form['username']
            password = request.form['ID']
            
            cursor = db.cursor()

            sql = "SELECT USERID FROM USERINFO \
                where USERID = '%s' AND PASSWORD = '%s'" %(userName, password)
            
            try:
                # 执行SQL语句
                cursor.execute(sql)
                # 获取所有记录列表
                result = cursor.fetchone()
                if result[0] == userId:            
                    return render_template('main.html') 
                else:
                    return "LOG_IN FAILED"
            except:
                return 'retry'
        
        if page_status == 'email':
            email = request.form['email']

            cursor = db.cursor()
            sql = "SELECT EMAIL FROM USERINFO \
                where EMAIL = '%s' " %email
            
            try:
                cursor.execute(sql)
                result = db.fetchone()
                if result[0] == email:
                    #TODO send email to the email address
                    valid_code = random.randint(0,1001)
                    with open(textfile) as fp:
                        # Create a text/plain message
                        msg = MIMEText(fp.read())

                    # me == the sender's email address
                    # you == the recipient's email address
                    msg['Subject'] = 'Reset Password for Diversita' 
                    msg['From'] = 'clytze20@uw.edu'
                    msg['To'] = email

                    # Send the message via our own SMTP server.
                    s = smtplib.SMTP('localhost')
                    s.send_message(msg)
                    s.quit()

                else:
                    return 'email not exist'
            
            except:
                return 'retry'

        if page_status == 'validation':
            valid_c = request.form['valid']
            if valid_c == valid_code:
                return 'verified'
            
            else:
                return 'failed'
        
        if page_status == 'reset':
            password = request.form['reset']
            sql = "UPDATE USERINFO SET PASSWORD='%s' \
                WHERE EMAIL='%s' " %s(password, email)
            
            try:
                db.execute(sql)
                db.commit()
                return 'reset success!'

            except:
                db.rollback()
                return 'failed'
        
    else:
        return render_template('login.html') 

@app.route('/m',methods=["GET", "POST"])
def run():
    if request.method == 'POST':
        page_status = request.form['status']
        uuid = request.form['uuid']
        namespace = '/' + uuid
        #print(uuid)
        cursor = db.cursor()
        sql = "SELECT USERID FROM TOKENLIST \
                WHERE UUIDTOKEN = '%s'" %uuid
            
        try:
            cursor.execute(sql)
            result = cursor.fetchone()
            userId = result[0]
            print(userId)
        except:
            return "Error: unable to find the user"

        if page_status == 'dashboard':
            cursor = db.cursor()
            sql = "SELECT DEVICENAME FROM DEVICEINFO \
                WHERE USERID = '%s' " %userId
            
            try:
                count = cursor.execute(sql)
                if count > 0:
                    results = cursor.fetchall()
                    deviceName = []
                    for row in results:
                        deviceName.append(row[0])
                    #socketio.emit('device', {'status': 1, 'devices': deviceName})
                else:
                    return "no device" 
            except:
                return "Error: unable to fecth device list"

            cursor = db.cursor()
            sql = "SELECT DEVICENAME FROM DEVICEINFO \
                    WHERE NEW = 1 AND USERID = '%s' " %userId 
                        
            try:
                c = cursor.execute(sql)
                if c > 0:
                    results = cursor.fetchall()
                    newDevice = []
                    for row in results:
                        newDevice.append(row[0])
                    
                        sql = "UPDATE DEVICEINFO SET NEW = 0 \
                            WHERE DEVICENAME='%s' " %row[0]

                        try:
                            cursor.execute(sql, newDevice)
                            db.commit()
                        
                        except:
                            db.rollback()
                        
                    oldDevice = deviceName - newDevice
                    r = {
                        'oldDevice': oldDevice,
                        'newDevice': newDevice
                        }
                    return Response(json.dumps(r), mimetype='application/json')

                else:
                    r = {'oldDevice': deviceName}
                    return Response(json.dumps(r), mimetype='application/json')

            except:
                return "Error: unable to fecth new device"  
                           
        if page_status == 'device':
            deviceName = request.form['deviceName']
            cursor = db.cursor()
            sql = "SELECT DEVICEID, REGISTERDATE, LOCATION FROM DEVICEINFO \
                        WHERE DEVICENAME = '%s' AND USERID = '%s'" %(deviceName, userId)
            
            try:
                cursor.execute(sql)
                result = cursor.fetchone()
                deviceId = result[0]
                registerDate = result[1]
                location = result[2]
            
            except:
                return 'Error: unable to fetch device info'

            cursor = db.cursor()
            sql = "SELECT SPECIES FROM JOBLIST \
                    WHERE DEVICEID = '%s' AND ACTIVE = 1" %deviceId

            try:
                c = cursor.execute(sql)
                species = []
                if c > 0:
                    results = cursor.fetchall()                 
                    for row in results:
                        species.append(row[0])

            except:
                r = {
                    'deviceId': deviceId,
                    'registerDate': str(registerDate),
                    'location': location,
                    'species': 'unknown',
                    'count': 'unknown',
                    'latest': 'unknown'
                    }
                return Response(json.dumps(r), mimetype='application/json')
            
            cursor = db.cursor()
            sql = "SELECT TIMESTAMP FROM IMGINFO \
                WHERE DEVICEID = '%s'" %deviceId

            try:
                count = cursor.execute(sql)

            except:
                r = {
                    'deviceId': deviceId,
                    'registerDate': str(registerDate),
                    'location': location,
                    'species': species,
                    'count': 'unknown',
                    'latest': 'unknown'
                    }
                return Response(json.dumps(r), mimetype='application/json')

            if count > 0:
                cursor = db.cursor()
                sql = "SELECT MAX(TIMESTAMP) FROM IMGINFO \
                    WHERE DEVICEID = '%s'" %deviceId

                try:
                    cursor.execute(sql)
                    result = cursor.fetchone()
                    lateset = result[0]

                    r = {
                        'deviceId': deviceId,
                        'registerDate': str(registerDate),
                        'location': location,
                        'species': species,
                        'count': count,
                        'latest': lateset
                    }
                    return Response(json.dumps(r), mimetype='application/json')
                        
                except: 
                    r = {
                        'deviceId': deviceId,
                        'registerDate': str(registerDate),
                        'location': location,
                        'species': species,
                        'count': count,
                        'latest': 'unknown'
                    }
                    return Response(json.dumps(r), mimetype='application/json')
            
            else:
                r = {
                    'deviceId': deviceId,
                    'registerDate': str(registerDate),
                    'location': location,
                    'species': species,
                    'count': count,
                    'latest': 'unknown'
                    }
                return Response(json.dumps(r), mimetype='application/json')
                    
        if page_status == 'notification':
            cursor = db.cursor()
            sql = "SELECT DEVICEID, TIMESTAMP, JOB, UNREAD FROM IMGINFO \
                WHERE USERID = '%s' " %userId 
            
            try:
                count = cursor.execute(sql)
                results = cursor.fetchall()
                imgInfo = []

            except:
                return 'Error: unable to fetch img info'
            if count > 0:
                for row in results:
                    cursor = db.cursor()
                    sql = "SELECT DEVICENAME FROM DEVICEINFO \
                        WHERE DEVICEID = '%s' " %row[0]
                    
                    try:
                        cursor.execute(sql)
                        result = cursor.fetchone()

                        detail = {
                            'deviceName': result[0],
                            'timestamp': row[1],
                            'job': row[2],
                            'new': row[3]
                        }

                    except:
                        detail ={
                            'deviceName': 'unknown',
                            'timestamp': row[1],
                            'job': row[2],
                            'new': row[3]
                        }
                    
                    imgInfo.append(detail)

                cursor = db.cursor()
                sql = "UPDATE IMGINFO SET \
                    UNREAD = 0 WHERE USERID = '%s' AND UNREAD = 1" %userId

                try:
                    db.execute(sql)
                    db.commit()
                
                except:
                    db.rollback()

            r = {
                    'count': count,
                    'imgInfo': imgInfo 
                }

            return Response(json.dumps(r), mimetype='application/json')
 
        if page_status == 'img_detail':
            deviceName = request.form['deviceName']
            timestamp = request.form['timestamp']

            cursor = db.cursor()
            sql = "SELECT DEVICEID FROM DEVICEINFO \
                WHERE DEVICENAME = '%s' " \
                %deviceName

            try:
                cursor.execute(sql)
                result = cursor.fetchone() 
                deviceId = result[0]

            except:
                return "Error: unable to fetch the device"  

            cursor = db.cursor()
            sql = "SELECT IMGNAME, CONFIDENCE FROM IMGINFO \
                WHERE DEVICENAME = '%s' AND TIMESTAMP = '%s'" \
                %(deviceId, timestamp) 
            
            try:
                cursor.execute(sql)
                result = cursor.fetchone() 
                imgName = result[0]
                confidence = result[1]

                r = {
                    'imgName': imgName,
                    'confidence': confidence
                }
                return Response(json.dumps(r), mimetype='application/json')

            except:
                return 'display image failed'
            
        if page_status == 'device_edit':
            deviceName = request.form['deviceName']
            deviceId = request.form['deviceId']
            cursor = db.cursor()
            sql = "UPDATE DEVICEINFO SET \
                DEVICENAME='%s' WHERE DEVICEID='%s' AND USERID='%s' " \
                %(deviceName, deviceId, userId)
            
            try:
                cursor.execute(sql)
                db.commit()
                return 'success'
            
            except:
                db.rollback()
                return 'fail'
        
        if page_status == 'job':
            deviceId = request.form['deviceId']
            cursor = db.cursor()
            sql = "SELECT SPECIES, ACTION, JOBNAME FROM JOBLIST \
                    WHERE DEVICEID = '%s' AND ACTIVE = 1" %deviceId
                
            try:
                count = cursor.execute(sql)
                results = cursor.fetchall()
                jobInfo = []
                for row in results:
                    detail = {
                        'species': row[0],
                        'action': row[1],
                        'jobname': row[2]
                    }
                    jobInfo.append(detail)
                
                r = {
                    'count': count,
                    'jobInfo': jobInfo
                }
                
                return Response(json.dumps(r), mimetype='application/json')
            
            except:
                return 'Error: cannot get the job info'

        if page_status == 'jobinfo':
            deviceId = request.form['deviceId']
            jobName = request.form['jobName']

            cursor = db.cursor()
            sql = "SELECT SPECIES FROM JOBLIST \
                WHERE JOBNAME = '%s' AND DEVICEID = '%s'" %(jobName, deviceId)
            
            try:
                cursor.execute(sql)
                result = cursor.fetchone()
                species = result[0]

            except:
                return "Error: unable to find the job" 

            cursor = db.cursor()
            sql = "SELECT IMGNAME, TIMESTAMP FROM IMGINFO \
                WHERE JOB = '%s' AND DEVICEID = '%s'" \
                %(species, deviceId)
                
            try:
                count = cursor.execute(sql)
                results = cursor.fetchall()
                img_info = []
                for row in results:
                    detail = {
                        'imgName': row[0], #URL
                        'timestamp': row[1]
                    }
                    img_info.append(detail)
                
                r = {
                    'imgInfo': img_info,
                    'count': count
                } 
                return Response(json.dumps(r), mimetype='application/json')
                
            except:
                return 'Error: unable to fetch img info'

        if page_status == 'jobedit': #debug
            deviceId = request.form['deviceId']
            jobName = request.form['jobName']
            try:
                if request.form['active'] == 0:
                    cursor = db.cursor()
                    
                    sql = "UPDATE JOBLIST SET \
                        ACTIVE=0 WHERE DEVICEID='%s' AND JOBNAME='%s'" \
                        %(deviceId, jobName)

            except:
                species = request.form['species']
                action = request.form['action']

                cursor = db.cursor()
                sql = "UPDATE JOBLIST SET \
                    SPECIES='%s', ACTION='%s' WHERE DEVICEID='%s' AND JOBNAME='%s'" \
                    %(species, action, deviceId, jobName)

            finally:    
                try:
                    print(sql)
                    cursor.execute(sql)
                    db.commit()
                    return 'success'

                except:
                    db.rollback()
                    return 'failed'

        if page_status == 'captured':
            deviceId = request.form['deviceId']

            cursor = db.cursor()
            sql = "SELECT TIMESTAMP, IMGNAME, JOB FROM IMGINFO \
                WHERE DEVICEID='%s' " %deviceId
            
            try:
                count = cursor.execute(sql)
                results = db.fetchall()
                img_info = []
                for row in result:
                    detail = {
                        'timestamp': row[0],
                        'imgName': row[1],
                        'jobName': row[2]
                    }
                    img_info.append(detail)

                r = {
                    'count': count,
                    'imgInfo': detail
                }

                return Response(json.dumps(r), mimetype='application/json')
            
            except:
                return 'Error: unable to fetch the photos'

        if page_status == 'add_device':
            deviceId = request.form['deviceId']
            deviceName = request.form['deviceName']
            registerDate = time.strftime("%Y-%m-%d", time.localtime()) 
        
            cursor = db.cursor()
            sql = "SELECT DEVICENAME FROM DEVICEINFO \
                where USERID = '%s'" %userId

            try:
                cursor.execute(sql)
                results = cursor.fetchall()
                for row in results:
                    if row[0] == deviceName:
                        return 'devicename exist'

            except:
                print('no device for the user')

            cursor = db.cursor()
            try:
                location = request.form['location']
            
                sql = "INSERT INTO DEVICEINFO(USERID, DEVICEID, DEVICENAME, REGISTERDATE, LOCATION) \
                    VALUES ('%s', '%s', '%s', '%s', '%s')" % \
                    (userId, deviceId, deviceName, registerDate, location)
            
            except:
                sql = "INSERT INTO DEVICEINFO(USERID, DEVICEID, DEVICENAME, REGISTERDATE) \
                    VALUES ('%s', '%s', '%s', '%s')" % \
                    (userId, deviceId, deviceName, registerDate)

            try:
                cursor.execute(sql)
                db.commit()
                return 'add device success'

            except:
                db.rollback()
                return 'unable to add the device'
        
        if page_status == 'addjob':
            jobName = request.form['jobName']
            species = request.form['species']
            action = request.form['action']
            deviceId = request.form['deviceId']

            cursor = db.cursor()
            sql = "INSERT INTO JOBLIST (JOBNAME,SPECIES,ACTION,DEVICEID) \
                VALUES ('%s','%s','%s','%s')" %(jobName, species, action, deviceId)
            
            try:
                cursor.execute(sql)
                db.commit()
                return 'success'
            
            except:
                db.rollback()
                return 'failed'

    else:
        return render_template('login.html') 
        
@app.route('/upload',methods=["GET", "POST"])
def index():
    if request.method == 'POST': 
        if request.content_type == 'image/jpeg':
            r = request
            h = int(r.args.get('imageHeight'))
            w = int(r.args.get('imageWidth'))
            deviceId = r.args.get('serial')
            timestamp = r.args.get('timestamp')

            print (w,h)
            # convert string of image data to uint8
            if type(r.data) == str:
                print('string detected')
                nparr = np.fromstring(r.data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                pil_img = Image.fromarray(nparr)
        
            if type(r.data) == bytes:
                print('bytes detected')
                pil_img = Image.open(BytesIO(r.data))
                #pil_img = Image.frombytes("RGB",(w, h),r.data)

            p = Path('./static/img/', deviceId+'_'+timestamp+'.jpg')
            print('path:', p)
            pil_img.save(p, format="JPEG")

            uploadData = {
                'url': 'http://40.112.164.41:5000/' + p
            }

            r = requests.post(uploadWebAddr, data=json.dumps(uploadData), headers=headers)            
            result = json.loads(r)

            confidence = result['bboxes']['confidence']
            species = result['predictions']['species_common']

            cursor = db.cursor()
            sql = "SELECT SPECIES FROM JOBLIST \
                WHERE DEVICEID='%s' " %deviceId 
            
            try:
                count = cursor.execute(sql)
                if count > 0:
                    results = cursor.fetchall()
                    for row in results:
                        if species == row[0]:
                            rendering_box(result['bboxes'], p)
                
                else:
                    rendering_box(result['bboxes'], p)
            
            except:
                print('Error: unable to fetch jobs for the device') 

            cursor = db.cursor()
            sql = "SELECT USERID, LOCATION FROM DEVICEINFO WHERE DEVICEID='%s' " %deviceId

            try:
                cursor.execute(sql)
                result = cursor.fecthone()
                userId = result[0]
                location = result[1]

            except:
                return 'Error: unable to find the device in the db'

            cursor = db.cursor()        
            sql = "INSERT INTO IMGINFO(DEVICEID, USERID, TIMESTAMP, IMGNAME, LOCATION, JOB, CONFIDENCE) \
                VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%f')" % \
                (deviceId, userId, timestamp, deviceId + "_" + timestamp, location, species, confidence)

            try:
                cursor.execute(sql)
                db.commit()
                return 'insert success'
                        
            except:
                db.rollback()
                return 'insert failed'
                        
                        
        elif request.content_type == 'application/json':
            resJson = request.get_json()
            #print(resJson)
            res = resJson
            print(type(resJson))
            deviceId = res['serial']
            timestamp = res['timestamp']
            l = res['boxes']
            score_l, imgName = rendering_box(l, 'temp.jpg', timestamp)
                #TODO API communication
            img_d = Image.open(imgName)
            buff = BytesIO()
            img_d.save(buff, format="JPEG")
            new_image_string = base64.b64encode(buff.getvalue()).decode("utf-8")
            socketio.emit('imageConversionByServer', "data:image/jpeg;base64,"+ new_image_string , namespace='/main')
            socketio.emit('/data', {'status': 0 , 'score':score_l, 'timestamp': timestamp}, namespace='/main')
            
            #device_Id VARCHAR(30) NOT NULL, user_Id VARCHAR(255) NOT NULL, user_name VARCHAR(255) NOT NULL, timestamp DATETIME NOT NULL, confidence_1 FLOAT NOT NULL, species_1 VARCHAR(30) NOT NULL, confidence_2 FLOAT NOT NULL, species_2 VARCHAR(30) NOT NULL, confidence_3 FLOAT, species_3 VARCHAR(30), PRIMARY KEY(user_Id) );
            #TODO more info needed from uploaded data 
            return Response(response="success", status=200, mimetype="application/json")
        
        else:
            return 'wrong content_type'
    else:
        return render_template('main.html')

@app.route('/imageUpload',methods=["GET", "POST"])
def test():
    if request.method == 'POST': 
        if request.content_type == 'image/jpeg':
            r = request
            matchId = r.args.get('TriggerTime') + r.args.get('serial')
            c = r.args.get('count')
            h = int(r.args.get('imageHeight'))
            w = int(r.args.get('imageWidth'))
            print (w,h)
            # convert string of image data to uint8
            headers = {
            # Request headers
                'Content-Type': 'application/octet-stream',
                'Ocp-Apim-Subscription-Key': '1169027d1aa2464a8f053245db76a387',
            }

            try:
                res = requests.post('https://aiforearth.azure-api.net/species-recognition/v0.1/predict?'+ c, data=r.data, headers=headers)
                result = json.loads(res)
                if result['bboxes']['confidence'] >= 90:
                    l = result['bboxes']
                    pil_img = Image.frombytes("RGB", (w, h),r.data)
                    pil_img.save('temp.jpg', format="JPEG")
                    imgName = rendering_box(l, 'temp.jpg', matchId)

                    deviceId = r.args.get('serial')
                    confidence_1 = result['predictions'][0]['confidence']
                    confidence_2 = result['predictions'][1]['confidence']
            #device_Id VARCHAR(30) NOT NULL, user_Id VARCHAR(255) NOT NULL, user_name VARCHAR(255) NOT NULL, timestamp DATETIME NOT NULL, confidence_1 FLOAT NOT NULL, species_1 VARCHAR(30) NOT NULL, confidence_2 FLOAT NOT NULL, species_2 VARCHAR(30) NOT NULL, confidence_3 FLOAT, species_3 VARCHAR(30), PRIMARY KEY(user_Id) );
            #TODO more info needed from uploaded data
                    cursor = db.cursor()

                    sql = "INSERT INTO img_info(device_Id, user_Id, user_name, timestamp, confidence_1, species_1, confidence_2, species_2) \
                        VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
                        (deviceId, logCookie, imgName, timestamp)
            
                    return Response(response="success", status=200, mimetype="application/json")
            except:
                return 'Error: unable to send data to the server'
        else:
            return 'wrong content_type'
    else:
        return render_template('main.html')

@app.route('/config',methods=["GET", "POST"])
def config():
    initThreads()

    if request.method == 'POST':
        need = request.form['detect']
        if need == "yes":
            if os.path.exists('config.json'):
                os.remove('config.json')
                #TODO
            return "DETECTING"

    else: 
        return render_template('config.html')  

@socketio.on('connect', namespace='/test')
def test_connect():
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            data = json.load(f)
            print(data)
            #TODO
    else:
        socketio.emit('my_detect',{'state': "off"},namespace='/test')
                             
@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

@socketio.on('imageConversionByServer')
def handle_message(message):
    nparr = np.fromstring(message, np.uint8)
    # decode image
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # do some fancy processing here....
            #dataStr = json.dumps(r.data)
    pil_img = Image.fromarray(img)
    buff = BytesIO()
    pil_img.save(buff, format="JPEG")

if __name__ == '__main__':
    #upload the ip

    # ipAddress = getIpAddress()
    # while ipAddress == None:
    #     time.sleep(0.5)
    #     ipAddress = getIpAddress()

    # print(getMacAddress())
    # print(getIpAddress())

    # r = requests.get('http://39.104.94.28:5000/device/' + getMacAddress() + '/' + getIpAddress())
    # print(r.text)
    socketio.run(app,  host='0.0.0.0', port=5000,debug=False)
