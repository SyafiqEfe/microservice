from flask import Flask, jsonify
from peewee import *
from flask_restful import Resource, Api, reqparse 

app = Flask(__name__)
api = Api(app)

db = SqliteDatabase('../DB-A.db')

class BaseModel(Model):
    class Meta:
        database = db

class TBCarsWeb(BaseModel):
    carname = TextField()
    carbrand = TextField() 
    carmodel = TextField()
    carprice = TextField()
    description = TextField()

def create_tables():
    with db:
        db.create_tables([TBCarsWeb])

@app.route('/')
def masukkeindeks():
    return "MS2 Server Ready"

class CAR(Resource):
    def get(self):
        rows = TBCarsWeb.select()    
        datas=[]

        for row in rows:
            datas.append({
            'id':row.id,
            'carname':row.carname,
            'carbrand':row.carbrand,
            'carmodel':row.carmodel,
            'carprice':row.carprice,
            'description':row.description
        })
        return jsonify(datas)

    def post(self):
        parserData = reqparse.RequestParser()
        parserData.add_argument('carname')
        parserData.add_argument('carbrand')
        parserData.add_argument('carmodel')
        parserData.add_argument('carprice')
        parserData.add_argument('description')

        parserAmbilData = parserData.parse_args()

        fName = parserAmbilData.get('carname')
        fBrand = parserAmbilData.get('carbrand')
        fModel = parserAmbilData.get('carmodel')
        fPrice = parserAmbilData.get('carprice')
        fDescription = parserAmbilData.get('description')

        car_simpan = TBCarsWeb.create(
            carname = fName,
            carbrand = fBrand, 
            carmodel = fModel,
            carprice = fPrice,
            description = fDescription
            )

        rows = TBCarsWeb.select()    
        datas=[]
        for row in rows:
            datas.append({
                'id':row.id,
                'carname':row.carname,
                'carbrand':row.carbrand,
                'carmodel':row.carmodel,
                'carprice':row.carprice,
                'description':row.description
            })
        return jsonify(datas)

api.add_resource(CAR, '/cars', endpoint="cars")

class CAR_ID(Resource):
    def get(self, id):
        try:
            car = TBCarsWeb.get(TBCarsWeb.id == id)
            return jsonify({
                'id': car.id,
                'carname': car.carname,
                'carbrand': car.carbrand,
                'carmodel': car.carmodel,
                'carprice': car.carprice,
                'description': car.description
            })
        except TBCarsWeb.DoesNotExist:
            return jsonify({'error': 'Not found'}), 404

    def put(self, id):
        parserData = reqparse.RequestParser()
        parserData.add_argument('carname')
        parserData.add_argument('carbrand')
        parserData.add_argument('carmodel')
        parserData.add_argument('carprice')
        parserData.add_argument('description')
        parserAmbilData = parserData.parse_args()
        query = TBCarsWeb.update(
            carname=parserAmbilData.get('carname'),
            carbrand=parserAmbilData.get('carbrand'),
            carmodel=parserAmbilData.get('carmodel'),
            carprice=parserAmbilData.get('carprice'),
            description=parserAmbilData.get('description')
        ).where(TBCarsWeb.id == id)
        query.execute()
        return jsonify({'status': 'updated'})

    def delete(self, id):
        query = TBCarsWeb.delete().where(TBCarsWeb.id == id)
        query.execute()
        return jsonify({'status': 'deleted'})

api.add_resource(CAR_ID, '/cars/<int:id>')

class CAR_SEARCH(Resource):
    def get(self, keyword):
        rows = TBCarsWeb.select().where(
            (TBCarsWeb.carname.contains(keyword)) |
            (TBCarsWeb.carbrand.contains(keyword)) |
            (TBCarsWeb.carmodel.contains(keyword))
        )
        datas = []
        for row in rows:
            datas.append({
                'id': row.id,
                'carname': row.carname,
                'carbrand': row.carbrand,
                'carmodel': row.carmodel,
                'carprice': row.carprice,
                'description': row.description
            })
        return jsonify(datas)

api.add_resource(CAR_SEARCH, '/cars/search/<string:keyword>')


if __name__ == '__main__':
    create_tables()
    app.run(
        host = '0.0.0.0',
        debug = 'True',
        port=5052
        )