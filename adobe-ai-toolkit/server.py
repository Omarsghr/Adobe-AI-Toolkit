from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import json
import uvicorn
import sqlite3
from main import run_master_pipeline

from src.data_formatter.payload_validator import PayloadFormatter

app = FastAPI(title="Adobe AI Toolkit Server")

# Enable CORS for localhost connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add CSP header middleware to allow eval for Adobe ExtendScript


@app.middleware("http")
async def add_csp_header(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src *; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
    return response

# Configuration
UPLOAD_DIR = "incoming_jobs"
BASE_ASSET_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_ASSET_PATH, "src/database/project_memory.db")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"status": "Online", "message": "Gamer PC is ready to process video audio."}


@app.get("/health")
def health_check():
    """Endpoint for the Adobe Panel to check if backend is alive."""
    return {"status": "healthy", "service": "Adobe-AI-Toolkit-Backend"}


@app.post("/process-from-adobe")
async def handle_adobe_request(file: UploadFile = File(...)):
    """Receives audio/video, processes it through standard master pipeline."""
    try:
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"📥 Received Standard Job: {file.filename}")

        result_json_path = run_master_pipeline(
            file_location, video_mode="Business")

        if not os.path.exists(result_json_path):
            raise HTTPException(
                status_code=500, detail="Pipeline failed to generate screenplay.")

        with open(result_json_path, "r") as f:
            screenplay_payload = json.load(f)

        cleaned_payload = PayloadFormatter.prepare_for_transmission(
            screenplay_payload, BASE_ASSET_PATH)

        if not cleaned_payload:
            raise HTTPException(
                status_code=500, detail="Payload validation failed.")

        return {
            "status": "success",
            "message": "Processing complete.",
            "data": cleaned_payload
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 🚀 🚀 الـ ENDPOINT الجْدِيدَة د الـ FEW-SHOT ANALOGY LEARNING 🚀 🚀
@app.post("/process-with-analogy")
async def handle_adobe_analogy_request(
    # مَلَف الـ فيديو أو الـ أوديو المُرَاد مَوْنْطَاجُه
    file: UploadFile = File(...),
    # اسْم الـ سّْتِيل (مَثَلاً: Ali_Abdaal_Style)
    style_name: str = Form(...),
    # نَوْع الـ سّْياق (Educational, Business, Vlog, etc.)
    style_type: str = Form(...),
    # الـ JSON المَرْجِعِي لِّي جَبْتِيه مَن الـ وِيب كـ String
    reference_json_str: str = Form(...)
):
    """
    يَسْتَقْبِل الـ فيديو والـ JSON المَرْجِعِي ف دَقّة وَاحْدَة،
    يَقُوم بـ حِفْظ الـ Analogy ف الـ Database، ثُمَّ يُطْلِق الـ Pipeline الذَّكِي المُرْتَبِط بِهَا.
    """
    try:
        # 1. حِفْظ الـ مَلَف المُرْسَل مَن الـ Panel
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(
            f"📥 Received Analogy Job: {file.filename} | Target Style: {style_name}")

        # 2. التَّأَكُّد أَنَّ الـ JSON د الـ الويب صَالِح
        try:
            parsed_reference_json = json.loads(reference_json_str)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400, detail="The reference_json_str provided is not a valid JSON structure.")

        # 3. حِفْظ وتَحْدِيث الـ Template ف الـ SQLite Database بَاش الـ Director يَعْقَل عْلِيه
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # نَتَأَكّد مَن وُجُود الجَدْوَل أوَّلاً تفادياً لأي كراش
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS style_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                style_name TEXT UNIQUE,
                style_type TEXT,
                reference_json TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            INSERT OR REPLACE INTO style_templates (style_name, style_type, reference_json)
            VALUES (?, ?, ?)
        """, (style_name, style_type, json.dumps(parsed_reference_json)))
        conn.commit()
        conn.close()
        print(
            f"🧠 [DB Memory] Success: Analogy '{style_name}' ({style_type}) successfully injected into SQLite.")

        # 4. تَقْدِير وتَشْغِيل الـ Master Pipeline
        # مَلْحُوظَة: دَابَا تَقْدَر تْصِيفْط الـ style_type لـ الـ Pipeline بَاش الـ Director يَمْشِي يْقَلّب عْلِيه ف الـ DB
        result_json_path = run_master_pipeline(
            file_location, video_mode=style_type)

        if not os.path.exists(result_json_path):
            raise HTTPException(
                status_code=500, detail="Pipeline failed to generate screenplay using analogy.")

        # 5. قِرَاءَة الـ Payload وفَلْتَرَتْهُا لـ الـ CEP
        with open(result_json_path, "r") as f:
            screenplay_payload = json.load(f)

        cleaned_payload = PayloadFormatter.prepare_for_transmission(
            screenplay_payload, BASE_ASSET_PATH)

        return {
            "status": "success",
            "message": f"Adaptive prompt synced. Video analyzed based on '{style_name}' context template.",
            "style_applied": style_name,
            "data": cleaned_payload
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Server Error during analogy execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
