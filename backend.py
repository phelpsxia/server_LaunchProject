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

def rendering_box(l, img, timestamp):
    score_list = []
    image = mpimg.imread(img)
    count = 0
    dpi = 100
    
    print(image.shape)
    imageHeight, imageWidth = image.shape[0:2]
    figsize = imageWidth / float(dpi), imageHeight / float(dpi)
    fig = plt.figure(figsize=figsize)
    ax = plt.axes([0,0,1,1])

        # Display the image
    ax.imshow(image)
    ax.set_axis_off()
    
    for item in l:
        rect = patches.Rectangle((float(item['x']),float(item['y'])),float(item['w']),float(item['h']),linewidth=3,edgecolor=color_list[count],facecolor='none')
        
        # Add the patch to the Axes
        ax.add_patch(rect)
        count += 1 
        score = item['score']
        score_list.append(score)
    # This is magic goop that removes whitespace around image plots (sort of)        
    plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
    plt.margins(0,0)
    ax.xaxis.set_major_locator(ticker.NullLocator())
    ax.yaxis.set_major_locator(ticker.NullLocator())
    ax.axis('tight')
    ax.set(xlim=[0,imageWidth],ylim=[imageHeight,0],aspect=1)
    plt.axis('off')                
    outputFileName = "{}.{}".format(timestamp,'jpg')
    # plt.savefig(outputFileName, bbox_inches='tight', pad_inches=0.0, dpi=dpi, transparent=True)
    plt.savefig(outputFileName, dpi=dpi, transparent=True)
    print ('done!')
    return score_list, outputFileName

@app.route('/',methods=["GET", "POST"])
def main():
    return redirect(url_for('login'))
  
@app.route('/signup', methods=["POST"])
def signUp():
    userName = request.form['username']
    password = request.form['password']

    userId = userName + password

    cursor = db.cursor()

    sql = "INSERT INTO USERINFO(USERID, DEVICEID) \
         VALUES ('%s', '%s')" % \
         (userId, deviceId)
    try:
        cursor.execute(sql)
        db.commit()
        db.close()
        return 'signup success!'

    except:
        db.rollback()
        db.close()
        return 'failed!'

@app.route('/login',methods=["GET", "POST"])
def login():
    global logCookie,loginJson,customerId,heart_beat

    if request.method == 'POST':
        
        userName = request.form['username']
        password = request.form['password']

        userId = userName + password
        
        data = {
            "username": userName,
            "password": password
        }
        
        sql = "SELECT USERID FROM USERINFO \
            where USERID = '%S' LIMIT 1" %userId
        
        try:
            # 执行SQL语句
            cursor.execute(sql)
            # 获取所有记录列表
            results = cursor.fetchone()            
            return "LOG_IN_SUCCESS"
        except:
            return "LOG_IN FAILED"

        
        #print content
    else:
        return render_template('load.html')

@app.route('/upload',methods=["GET", "POST"])
def index():
    if request.method == 'POST': 
        if request.content_type == 'image/jpeg':
            r = request
            matchId = r.args.get('TriggerTime')
            h = int(r.args.get('imageHeight'))
            w = int(r.args.get('imageWidth'))
            print (w,h)
            # convert string of image data to uint8
            if type(r.data) == str:
                print('string detected')
                nparr = np.fromstring(r.data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                pil_img = Image.fromarray(nparr)
        
            if type(r.data) == bytes:
                print('bytes detected')
                pil_img = Image.frombytes("RGB",(w, h),r.data)
        
            pil_img.save('temp.jpg', format="JPEG")
            #new_image_string = base64.b64encode(buff.getvalue()).decode("utf-8")
            return matchId
            #socketio.emit('imageConversionByServer', "data:image/jpeg;base64,"+ new_image_string , namespace='/main')
            #print('half way!')
            # build a response dict to send back to client
            #response = {'message': 'image received. size={}x{}'.format(img.shape[1], img.shape[0])}
            # encode response using jsonpickle
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
            
            sql = "INSERT INTO img_info(device_Id, user_Id, user_name, timestamp, confidence_1, species_1, confidence_2, species_2) \
                VALUES ('%s', 'null', 'test', '%s', '%s', 'animal', '0', 'none')" % \
                (deviceId, timestamp, score_l[0])
            
            return Response(response="success", status=200, mimetype="application/json")
        
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
