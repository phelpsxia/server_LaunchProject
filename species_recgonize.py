import MySQLdb
from pathlib import Path
import http.client, urllib.request, urllib.parse, urllib.error, base64,json
import ast
import os
import glob

db = MySQLdb.connect("localhost", "root", "2018_diversita_2018", "diversita", charset='utf8' )

headers = {
    # Request headers
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': '1169027d1aa2464a8f053245db76a387',
}

params = urllib.parse.urlencode({
    # Request parameters
    'topK': '1',
    'predictMode': 'classifyAndDetect',
})

def rendering_box(l, img):
    image = mpimg.imread(img)
    #count = 0
    dpi = 100

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

def species_recgonize():
    while True:
        cursor = db.cursor()
        sql = "SELECT * FROM IMGRECEIVED"

        try:
            c = cursor.execute(sql)
            results = cursor.fetchall()
        except:
            print('failed')
            continue
        if c > 0:
            for row in results:
                n = 'static/img/' + row[0]
                uploadData = {
                        'url': 'http://40.112.164.41:5000/' + str(n)
                    }
                print(n)
                conn = http.client.HTTPSConnection('aiforearth.azure-api.net')
                conn.request("POST", "/species-recognition/v0.1/predict?%s" % params, json.dumps(uploadData), headers)
                response = conn.getresponse()
                data = response.read()
                #print(data.decode("utf-8"))
                r = data.decode('utf-8')
                print(r)
                d = ast.literal_eval(r)
                #print(d)
                confidence = d['predictions'][0]['confidence']
                species = d['predictions'][0]['species_common']
                conn.close()
                index = row[0].find('_')
                deviceId = row[0][0:index]
                time = row[0][index + 1: -4]
                timestamp = time[0:4] + '-' + time[4:6] + '-' + time[6:8] + ' ' + time[9:11] + ':' + time[11:13] + ':' + time[13:] 
                sql = "SELECT SPECIES FROM JOBLIST WHERE DEVICEID='%s' " %deviceId

                try:
                    cursor.execute(sql)
                    results = cursor.fetchall()
                    s = []

                    for r in results:
                        s.append(r[0])

                except:
                    print('Error: unable to fetch the joblist')
                
                if species in s:
                    if d['bboxes'] != []:
                        rendering_box(d['bboxes'], 'http://40.112.164.41:5000/' + str(n))
                        sql = "SELECT USERID FROM DEVICEINFO WHERE DEVICEID='%s' " %deviceId

                        try:
                            cursor.execute(sql)
                            result = cursor.fetchone()
                            userId = result[0]
                        
                        except:
                            print('Error: unable to fetch userid')

                        sql = "INSERT INTO IMGINFO (IMGNAME, USERID, DEVICEID, TIMESTAMP, JOB, CONFIDENCE) \
                            VALUES ('%s', '%s', '%s', '%s', '%s', '%s')" %(row[0], userId, deviceId, timestamp, species, confidence)
                        
                        cursor.execute(sql)
                        db.commit()
                        try:
                            
                            status = 1
                            
                        except:
                            print('Error: unable to insert data')
                            status = 0
                        
                        if status == 1:
                            sql = "DELETE FROM IMGRECEIVED WHERE IMGNANE = '%s' " %row[0]

                            try:
                                cursor.execute(sql)
                                db.commit()

                            except:
                                print('delete from imgreceived failed')
                
                else:
                    os.remove('./' + n)

                    sql = "DELETE FROM IMGRECEIVED WHERE IMGNANE = '%s' " %row[0]

                    try:
                        cursor.execute(sql)
                        db.commit()

                    except:
                        print('delete from imgreceived failed')
                    
            
        else:
            time.sleep(600)

if __name__ == '__main__':
    species_recgonize()
    




