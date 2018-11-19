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

def species_recgonize():
    while True:
        cursor = db.cursor()
        sql = "SELECT * FROM IMGRECEIVED"

        try:
            cursor.execute(sql)
            results = cursor.fetchall()
        except:
            print('failed')
            continue

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
            #print(r)
            d = ast.literal_eval(r)
            #print(d)
            confidence = d['predictions'][0]['confidence']
            species = d['predictions'][0]['species_common']
            conn.close()
            index = row[0].find('_')
            deviceId = row[0][0:index]
            timestamp = row[0][index + 1: -4]
            
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
                sql = "SELECT USERID FROM DEVICEINFO WHERE DEVICEID='%s' " %deviceId

                try:
                    cursor.execute(sql)
                    result = cursor.fetchone()
                    userId = result[0]
                
                except:
                    print('Error: unable to fetch userid')

                sql = "INSERT INTO IMGINFO (IMGNAME, USERID, DEVICEID, TIMESTAMP, JOB, CONFIDENCE) \
                    VALUES ('%s', '%s', '%s', '%s', '%s', '%s')" %(row[0], userId, deviceId, timestamp, species, confidence)
                
                try:
                    cursor.execute(sql)
                    db.commit()
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
        
    else:
        time.sleep(600)

if __name__ == '__main__':
    species_recgonize()
    




