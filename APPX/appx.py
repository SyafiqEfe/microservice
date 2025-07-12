import uvicorn
import httpx
import asyncio
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette import status
from typing import List, Dict, Any

# --- 1. Inisialisasi Aplikasi FastAPI & Konfigurasi Template ---
app = FastAPI(title="Web Gateway")
# Memperbaiki error 'NoMatchFound' dengan mendaftarkan direktori 'static'
# Ini adalah baris kunci untuk file CSS/JS
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- 2. Konfigurasi Alamat Microservice ---
URL_MS1 = "http://localhost:5051/cars"
URL_MS2 = "http://localhost:5052/cars"
URL_MS3 = "http://localhost:5053/cars"

URL_MAP = {"MS1": URL_MS1, "MS2": URL_MS2, "MS3": URL_MS3}

# --- 3. Fungsi Bantuan (Helper) untuk Komunikasi Antar Service ---
async def get_data_from_service(client: httpx.AsyncClient, url: str) -> List[Dict[str, Any]]:
    """Fungsi async untuk mengambil data dari service lain."""
    try:
        response = await client.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        print(f"--- ERROR: Gagal terhubung ke {url}. Pesan: {e} ---")
        return []

# --- 4. Endpoints untuk Halaman Web ---

@app.get("/", response_class=HTMLResponse, summary="Halaman Utama")
async def get_main_page(request: Request):
    """Menampilkan halaman utama dengan data gabungan dari semua microservice."""
    async with httpx.AsyncClient() as client:
        tasks = [get_data_from_service(client, url) for url in URL_MAP.values()]
        results = await asyncio.gather(*tasks)
        rows_ms1, rows_ms2, rows_ms3 = results

    rows_dba = rows_ms1 + rows_ms2
    rows_dbb = rows_ms3
    
    return templates.TemplateResponse("index.html", {
        "request": request, "rows_dba": rows_dba, "rows_dbb": rows_dbb
    })

@app.get("/ms{service_num}", response_class=HTMLResponse, name="get_service_page")
async def get_service_page(request: Request, service_num: int):
    """Menampilkan halaman detail untuk MS1, MS2, atau MS3."""
    ms_map = {1: ("MS1", "DB-A"), 2: ("MS2", "DB-A"), 3: ("MS3", "DB-B")}
    if service_num not in ms_map:
        raise HTTPException(status_code=404, detail="Service tidak ditemukan")
    
    servermana, db_name = ms_map[service_num]
    target_url = URL_MAP[servermana]

    async with httpx.AsyncClient() as client:
        rows = await get_data_from_service(client, target_url)
    
    return templates.TemplateResponse("indexms.html", {
        "request": request, "rows": rows, "servermana": servermana, "DB": db_name
    })

# --- 5. Endpoints untuk Operasi CRUD ---

@app.get("/createcar/{ms}", response_class=HTMLResponse, name="show_create_car_form")
async def show_create_car_form(request: Request, ms: str):
    if ms not in URL_MAP:
        raise HTTPException(status_code=404, detail="Microservice tidak valid")
    return templates.TemplateResponse("createcar.html", {"request": request, "servermana": ms})

@app.post("/createcar/{ms}", name="handle_create_car_form")
async def handle_create_car_form(ms: str, carName: str = Form(...), carBrand: str = Form(...), carModel: str = Form(...), carPrice: str = Form(...), carDesc: str = Form(...)):
    target_url = URL_MAP.get(ms)
    if not target_url:
        raise HTTPException(status_code=404, detail="Microservice tidak valid")

    datacar = {"carname": carName, "carbrand": carBrand, "carmodel": carModel, "carprice": carPrice, "description": carDesc}
    
    async with httpx.AsyncClient() as client:
        try:
            await client.post(target_url, json=datacar)
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Gagal menambah data ke {ms}: {e}")

    redirect_url = app.url_path_for('get_service_page', service_num=int(ms[-1]))
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

@app.get("/updatecar/{ms}/{car_id}", response_class=HTMLResponse, name="show_update_car_form")
async def show_update_car_form(request: Request, ms: str, car_id: int):
    target_url = URL_MAP.get(ms)
    if not target_url:
        raise HTTPException(status_code=404, detail="Microservice tidak valid")

    async with httpx.AsyncClient() as client:
        url_car_specific = f"{target_url}/{car_id}"
        response = await client.get(url_car_specific, timeout=5)
        if response.status_code == 404:
             raise HTTPException(status_code=404, detail=f"Data mobil dengan ID {car_id} tidak ditemukan di {ms}")
        response.raise_for_status()
        car_data = response.json()
    
    return templates.TemplateResponse("updatecar.html", {"request": request, "car": car_data, "servermana": ms, "car_id": car_id})

@app.post("/updatecar/{ms}/{car_id}", name="handle_update_car_form")
async def handle_update_car_form(ms: str, car_id: int, carName: str = Form(...), carBrand: str = Form(...), carModel: str = Form(...), carPrice: str = Form(...)):
    target_url = URL_MAP.get(ms)
    if not target_url:
        raise HTTPException(status_code=404, detail="Microservice tidak valid")

    datacar = {"carname": carName, "carbrand": carBrand, "carmodel": carModel, "carprice": carPrice, "description": f"Updated from appx to {ms}"}

    async with httpx.AsyncClient() as client:
        try:
            await client.put(f"{target_url}/{car_id}", json=datacar)
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Gagal update data di {ms}: {e}")

    redirect_url = app.url_path_for('get_service_page', service_num=int(ms[-1]))
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

@app.post("/deletecar/{ms}/{car_id}", name="handle_delete_car")
async def handle_delete_car(request: Request, ms: str, car_id: int):
    target_url = URL_MAP.get(ms)
    if not target_url:
        raise HTTPException(status_code=404, detail="Microservice tidak valid")

    async with httpx.AsyncClient() as client:
        try:
            await client.delete(f"{target_url}/{car_id}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Gagal menghapus data di {ms}: {e}")

    redirect_url = app.url_path_for('get_service_page', service_num=int(ms[-1]))
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

@app.get("/searchcar", response_class=HTMLResponse, name="show_search_page")
async def show_search_page(request: Request):
    return templates.TemplateResponse("searchcar.html", {"request": request, "results": [], "keyword": ""})

@app.post("/searchcar", response_class=HTMLResponse, name="handle_search")
async def handle_search(request: Request, keyword: str = Form("")):
    results = []
    if keyword:
        async with httpx.AsyncClient() as client:
            tasks = [get_data_from_service(client, f"{url}/search/{keyword}") for url in URL_MAP.values()]
            search_results = await asyncio.gather(*tasks)
            for res_list in search_results:
                results.extend(res_list)

    return templates.TemplateResponse("searchcar.html", {"request": request, "results": results, "keyword": keyword})

# --- 6. Menjalankan Aplikasi ---
if __name__ == "__main__":
    uvicorn.run("appx:app", host="0.0.0.0", port=5000, reload=True)
