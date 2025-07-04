from flask import Flask, render_template, request, redirect, url_for
import json, requests

app = Flask(__name__)

@app.route('/')
def masukkeindeks():
    alamatserver_ms1_dba = "http://localhost:5051/cars"
    datas_dba = requests.get(alamatserver_ms1_dba)
    rows_dba = json.loads(datas_dba.text)
    alamatserver_ms3_dbb = "http://localhost:5053/cars"
    datas_dbb = requests.get(alamatserver_ms3_dbb)
    rows_dbb = json.loads(datas_dbb.text)

    return render_template('index.html', rows_dba=rows_dba,  rows_dbb=rows_dbb)

@app.route('/ms1')
def ms1():
    servermana='MS1'
    alamatserver = "http://localhost:5051/cars"
    datas = requests.get(alamatserver)
    rows = json.loads(datas.text)
    return render_template('indexms.html', rows=rows,  servermana=servermana, DB='DB-A')

@app.route('/ms2')
def ms2():
    servermana='MS2'
    alamatserver = "http://localhost:5052/cars"
    datas = requests.get(alamatserver)
    rows = json.loads(datas.text)
    return render_template('indexms.html', rows=rows,  servermana=servermana, DB='DB-A')
    

@app.route('/ms3')
def ms3():
    servermana='MS3'
    alamatserver = "http://localhost:5053/cars"
    datas = requests.get(alamatserver)
    rows = json.loads(datas.text)
    return render_template('indexms.html',  rows=rows,servermana=servermana, DB='DB-B')

@app.route('/createcar/<ms>')
def createcar(ms):
    try:
        return render_template('createcar.html', servermana=ms)
    except:
        ms = 'MS1'
        return render_template('createcar.html', servermana=ms)
@app.route('/createcarsave_ms1', methods=['GET','POST'])
def createcarsave_ms1():
    fName = request.form['carName']
    fBrand = request.form['carBrand']
    fModel = request.form['carModel']
    fPrice = request.form['carPrice']
    fdesc = request.form['carDesc']

    datacar = {
        "carname" : fName,
        "carbrand" : fBrand, 
        "carmodel" : fModel,
        "carprice" : fPrice,
        "description":fdesc
    }

    alamatserver = "http://localhost:5051/cars"
    headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
    try:
        kirimdata = requests.post(alamatserver, json=datacar, headers=headers)
        kirimdata.raise_for_status()
    except Exception as e:
        return f"Gagal menambah data ke MS1: {e}", 500
    return redirect(url_for('ms1'))

@app.route('/createcarsave_ms2', methods=['GET','POST'])
def createcarsave_ms2():
    fName = request.form['carName']
    fBrand = request.form['carBrand']
    fModel = request.form['carModel']
    fPrice = request.form['carPrice']
    fdesc = request.form['carDesc']

    datacar = {
        "carname" : fName,
        "carbrand" : fBrand, 
        "carmodel" : fModel,
        "carprice" : fPrice,
        "description":fdesc
    }

    alamatserver = "http://localhost:5052/cars"
    headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
    try:
        kirimdata = requests.post(alamatserver, json=datacar, headers=headers)
        kirimdata.raise_for_status()
    except Exception as e:
        return f"Gagal menambah data ke MS2: {e}", 500
    return redirect(url_for('ms2'))


@app.route('/createcarsave_ms3', methods=['GET','POST'])
def createcarsave_ms3():
    fName = request.form['carName']
    fBrand = request.form['carBrand']
    fModel = request.form['carModel']
    fPrice = request.form['carPrice']
    fdesc = request.form['carDesc']

    datacar = {
        "carname" : fName,
        "carbrand" : fBrand, 
        "carmodel" : fModel,
        "carprice" : fPrice,
        "description":fdesc
    }

    alamatserver = "http://localhost:5053/cars"
    headers = {'Content-Type':'application/json', 'Accept':'text/plain'}
    try:
        kirimdata = requests.post(alamatserver, json=datacar, headers=headers)
        kirimdata.raise_for_status()
    except Exception as e:
        return f"Gagal menambah data ke MS3: {e}", 500
    return redirect(url_for('ms3'))


@app.route('/readcar/<ms>')
def readcar(ms):
    if ms in ['MS1','MS2']:
        alamatserver = "http://localhost:5051/cars"
        datas = requests.get(alamatserver)
        rows = json.loads(datas.text)

        return render_template('readcar.html', rows=rows, servermana=ms, DB='DB-A')

    elif ms in ['MS3']:
        alamatserver = "http://localhost:5053/cars"
        datas = requests.get(alamatserver)
        rows = json.loads(datas.text)
        return render_template('readcar.html', rows=rows, servermana=ms, DB='DB-B')

@app.route('/updatecar/<ms>/<car_id>', methods=['GET', 'POST'])
def updatecar(ms, car_id):
    if request.method == 'POST':
        fName = request.form['carName']
        fBrand = request.form['carBrand']
        fModel = request.form['carModel']
        fPrice = request.form['carPrice']
        fdesc = f"update from appx to {ms}"
        datacar = {
            "carname": fName,
            "carbrand": fBrand,
            "carmodel": fModel,
            "carprice": fPrice,
            "description": fdesc
        }
        datacar_json = json.dumps(datacar)
        if ms in ['MS1', 'MS2']:
            alamatserver = f"http://localhost:5051/cars/{car_id}"
        else:
            alamatserver = f"http://localhost:5053/cars/{car_id}"
        headers = {'Content-Type': 'application/json', 'Accept': 'text/plain'}
        requests.put(alamatserver, data=datacar_json, headers=headers)
        return redirect(url_for(ms.lower()))
    else:
        # Ambil data mobil lama untuk form
        if ms in ['MS1', 'MS2']:
            alamatserver = f"http://localhost:5051/cars/{car_id}"
        else:
            alamatserver = f"http://localhost:5053/cars/{car_id}"
        datas = requests.get(alamatserver)
        car = datas.json()
        return render_template('updatecar.html', car=car, servermana=ms, car_id=car_id)

@app.route('/searchcar', methods=['GET', 'POST'])
def searchcar():
    results = []
    keyword = ''
    if request.method == 'POST':
        keyword = request.form['keyword']
        # Search di MS1 dan MS3
        alamatserver_ms1 = f"http://localhost:5051/cars/search/{keyword}"
        alamatserver_ms3 = f"http://localhost:5053/cars/search/{keyword}"
        try:
            datas_ms1 = requests.get(alamatserver_ms1)
            results += datas_ms1.json()
        except:
            pass
        try:
            datas_ms3 = requests.get(alamatserver_ms3)
            results += datas_ms3.json()
        except:
            pass
    return render_template('searchcar.html', results=results, keyword=keyword)

@app.route('/deletecar/<ms>/<car_id>', methods=['POST'])
def deletecar(ms, car_id):
    if ms in ['MS1', 'MS2']:
        alamatserver = f"http://localhost:5051/cars/{car_id}"
    else:
        alamatserver = f"http://localhost:5053/cars/{car_id}"
    requests.delete(alamatserver)
    return redirect(url_for(ms.lower()))

if __name__ == '__main__':
    
    app.run(
        host = '0.0.0.0',
        debug = 'True'
        )