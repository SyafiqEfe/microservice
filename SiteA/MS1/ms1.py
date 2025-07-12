import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from peewee import *
from typing import List

# --- 1. Konfigurasi Database (Sama seperti sebelumnya) ---
db = SqliteDatabase('../DB-A.db')

class BaseModelDB(Model):
    class Meta:
        database = db

class TBCarsWeb(BaseModelDB):
    carname = TextField()
    carbrand = TextField()
    carmodel = TextField()
    carprice = TextField()
    description = TextField()

def create_tables():
    with db:
        db.create_tables([TBCarsWeb], safe=True)

# --- 2. Pydantic Models (Validasi Data) ---
# Model ini digunakan untuk validasi data yang masuk (request body)
class CarCreate(BaseModel):
    carname: str
    carbrand: str
    carmodel: str
    carprice: str
    description: str

# Model ini digunakan untuk data yang dikirim keluar (response)
class Car(CarCreate):
    id: int

# --- 3. Inisialisasi Aplikasi FastAPI ---
app = FastAPI(
    title="Microservice 1 API",
    description="API untuk mengelola data mobil di Database A.",
    version="1.0.0"
)

# --- 4. Event Handler (Menghubungkan ke DB saat startup) ---
@app.on_event("startup")
def startup():
    if db.is_closed():
        db.connect()

@app.on_event("shutdown")
def shutdown():
    if not db.is_closed():
        db.close()

# --- 5. Endpoints API ---

@app.get("/", summary="Cek Status Server")
def root():
    return {"message": "MS1 Server (FastAPI) is Ready"}

@app.get("/cars", response_model=List[Car], summary="Ambil Semua Data Mobil")
def get_all_cars():
    cars = TBCarsWeb.select()
    return [car for car in cars.dicts()]

@app.post("/cars", response_model=Car, status_code=status.HTTP_201_CREATED, summary="Tambah Mobil Baru")
def create_car(car: CarCreate):
    new_car = TBCarsWeb.create(**car.dict())
    return new_car.__data__

@app.get("/cars/{car_id}", response_model=Car, summary="Ambil Mobil Berdasarkan ID")
def get_car_by_id(car_id: int):
    try:
        car = TBCarsWeb.get_by_id(car_id)
        return car.__data__
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Car not found")

@app.put("/cars/{car_id}", response_model=Car, summary="Update Data Mobil")
def update_car(car_id: int, car_data: CarCreate):
    try:
        query = TBCarsWeb.update(**car_data.dict()).where(TBCarsWeb.id == car_id)
        query.execute()
        return get_car_by_id(car_id) # Kembalikan data yang sudah diupdate
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Car not found")

@app.delete("/cars/{car_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Hapus Mobil")
def delete_car(car_id: int):
    try:
        car_to_delete = TBCarsWeb.get_by_id(car_id)
        car_to_delete.delete_instance()
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Car not found")

@app.get("/cars/search/{keyword}", response_model=List[Car], summary="Cari Mobil Berdasarkan Keyword")
def search_car(keyword: str):
    cars = TBCarsWeb.select().where(
        (TBCarsWeb.carname.contains(keyword)) |
        (TBCarsWeb.carbrand.contains(keyword)) |
        (TBCarsWeb.carmodel.contains(keyword))
    )
    return [car for car in cars.dicts()]

# --- 6. Menjalankan Aplikasi ---
if __name__ == '__main__':
    create_tables()
    # Gunakan uvicorn untuk menjalankan server FastAPI
    uvicorn.run("ms1:app", host="0.0.0.0", port=5051, reload=True)
