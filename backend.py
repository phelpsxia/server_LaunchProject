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

 
app = Flask(__name__,static_folder='static')
app.config['SECRET_KEY'] = 'Diversita'

socketio = SocketIO(app)
Bootstrap(app)

@app.route('/',methods=["GET", "POST"])
def main():
    return redirect(url_for('login'))  

@app.route('/login',methods=["GET", "POST"])
def login():
    global logCookie,loginJson,customerId,heart_beat

    if request.method == 'POST':
        
        userName = request.form['username']
        password = request.form['password']
        
        data = {
            "username": userName,
            "password": password
        }
        
        try:
            res = requests.post(loginWebAddr, data=json.dumps(data), headers=headers)
            print(res.text)
            jsonStr = res.text
            logCookie = res.cookies
            loginJson = json.loads(jsonStr)
            if loginJson['status'] == 0:
                resultJson = loginJson['result']
                companyName = resultJson['companyName']
                customerId = resultJson['id']

                if heart_beat != None:
                    heart_beat.stop()
                    heart_beat = None

                heart_beat = HeartBeatThread(logCookie)
                heart_beat.start()


                return "LOG_IN_SUCCESS"
            else:
                return "LOG_IN_FAILED"
        except requests.exceptions.ConnectionError:
            return "INTERNET_CONNECT_ERROR"
        except:
            return "UNKNOWN_ERROR"
        
        #print content
    else:
        return render_template('load.html')

@app.route('/upload',methods=["GET", "POST"])
def index():
    if request.method == 'POST':
        #jsonStr = json.dumps(request.files) 
        # print jsonStr
        print (request.content_type) 
        if request.content_type == 'image/jpeg':
            r = request
    # convert string of image data to uint8
            nparr = np.fromstring(r.data, np.uint8)
    # decode image
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # do some fancy processing here....
            #dataStr = json.dumps(r.data)
            pil_img = Image.fromarray(img)
            buff = BytesIO()
            pil_img.save(buff, format="JPEG")
            new_image_string = base64.b64encode(buff.getvalue()).decode("utf-8")
            #base64EncodedStr = base64.b64encode(nparr)
            #s = base64.decodestring(base64EncodedStr)
            print(type(new_image_string))
            socketio.emit('imageConversionByServer', "data:image/png;base64,"+ new_image_string , namespace='/main')
            print('half way!')
    # build a response dict to send back to client
            response = {'message': 'image received. size={}x{}'.format(img.shape[1], img.shape[0])}
    # encode response using jsonpickle

            return Response(response=response, status=200, mimetype="application/json")
            #test.save('lion.jpg')
            #socketio.emit('img', test)
            
            
        
        else:
            resJson = json.loads(request.data)
            
            if 'score' in request.form:
                precision = resJson['score']
                timestamp = resJson['timestamp']
                #TODO API communication
                
                socketio.emit('data',{ 'precision':precision,
                                    'timestamp':timestamp})
            
                #send to the DB
                uploadData = {
                    #'deviceId':getMacAddress(),
                    #'genre':genre,
                    'precision':precision,
                    'timestamp':timestamp, 
                    'image':test
                    }

    if request.method == 'GET':
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