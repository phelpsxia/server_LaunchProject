import http.client, urllib.request, urllib.parse, urllib.error, base64,json

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

def main(uploadData):
    try:
        conn = http.client.HTTPSConnection('aiforearth.azure-api.net')
        conn.request("POST", "/species-recognition/v0.1/predict?%s" % params, json.dumps(uploadData), headers)
        response = conn.getresponse()
        data = response.read()
        #print(data.decode("utf-8"))
        r = data.decode('utf-8')
        print(r)
        result = json.load(r)
        print(result)
        confidence = result['bboxes'][0]['confidence']
        species = result['predictions'][0]['species_common']
        conn.close()
        print(confidence,species)
        return confidence, species
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

if __name__ == '__main__':
    main({
	"url" : "http://40.112.164.41:5000/static/img/abc1234_1223455677.jpg"
})
    
