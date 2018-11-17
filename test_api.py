import http.client, urllib.request, urllib.parse, urllib.error, base64,json
from flask import Flask,render_template,request, url_for,redirect
from flask import Response, request

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

app = Flask(__name__)

@app.route('/',methods=["POST"])
def main():
    result = request.get_json()
    print(result)
    uploadData = result
    try:
        conn = http.client.HTTPSConnection('aiforearth.azure-api.net')
        conn.request("POST", "/species-recognition/v0.1/predict?%s" % params, json.dumps(uploadData), headers)
        response = conn.getresponse()
        data = response.read()
        print(data.decode("utf-8"))
        r = json.dumps(data.decode('utf-8'))
        confidence = r['bboxes']['confidence']
        species = r['predictions']['species_common']
        conn.close()
        print(confidence,species)
        return Response(response=json.dumps(r), status=200, mimetype="application/json")
    except Exception as e:
        return("[Errno {0}] {1}".format(e.errno, e.strerror))

if __name__ == '__main__':
    
    app.run(host='0.0.0.0', port=5000,debug=False)