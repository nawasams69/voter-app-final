from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sqlite3
import uvicorn
import os
import glob

app = FastAPI()

DB_FILE = "voter.db"

# --- 1. STITCH LOGIC (The Magic) ---
def setup_database():
    if os.path.exists(DB_FILE): return # Already exists
    
    print("Stitching database parts...")
    parts = sorted(glob.glob("voter.db.part*"))
    
    if not parts:
        print("❌ No database parts found!")
        return

    with open(DB_FILE, "wb") as outfile:
        for part in parts:
            print(f"Merging {part}...")
            with open(part, "rb") as infile:
                outfile.write(infile.read())
    print("✅ Database ready!")

# Run setup immediately
setup_database()

# --- 2. FRONTEND ---
html_code = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voter Search</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-5">
    <div class="card shadow p-4 mx-auto" style="max-width: 600px;">
        <h3 class="text-center mb-4 text-primary">ভোটার তথ্য অনুসন্ধান</h3>
        
        <div class="mb-3">
            <label>এলাকা কোড *</label>
            <input type="number" id="area" class="form-control" placeholder="যেমন: 2797">
        </div>
        <div class="mb-3">
            <label>লিঙ্গ *</label>
            <select id="gender" class="form-select">
                <option value="পুরুষ">পুরুষ</option>
                <option value="মহিলা">মহিলা</option>
                <option value="হিজড়া">হিজড়া</option>
            </select>
        </div>
        <div class="mb-3">
            <label>নাম (ঐচ্ছিক)</label>
            <input type="text" id="name" class="form-control" placeholder="নামের অংশ...">
        </div>
        <button onclick="search()" class="btn btn-primary w-100">Search</button>
        
        <div id="results" class="mt-4"></div>
    </div>
</div>

<script>
    async function search() {
        const r = document.getElementById('results');
        r.innerHTML = 'Searching...';
        
        const a = document.getElementById('area').value;
        const g = document.getElementById('gender').value;
        const n = document.getElementById('name').value;
        
        if(!a) { r.innerHTML = 'Please enter Area Code'; return; }
        
        let url = `/api/search?area=${a}&gender=${g}`;
        if(n) url += `&name=${n}`;
        
        try {
            const req = await fetch(url);
            const data = await req.json();
            
            r.innerHTML = '';
            if(data.length === 0) { r.innerHTML = '<div class="alert alert-warning">No Data Found</div>'; return; }
            
            data.forEach(v => {
                r.innerHTML += `
                    <div class="alert alert-light border">
                        <h5>${v['নাম']}</h5>
                        <p class="mb-0">পিতা: ${v['পিতা']} | ভোটার নং: ${v['ভোটার নং']}</p>
                        <small class="text-muted">${v['ঠিকানা']}</small>
                    </div>
                `;
            });
        } catch(e) { r.innerHTML = 'Error connecting to server'; }
    }
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home(): return html_code

# --- 3. BACKEND API ---
@app.get("/api/search")
def search_api(area: str, gender: str, name: str = None):
    if not os.path.exists(DB_FILE): return []
    
    conn = sqlite3.connect(f'file:{DB_FILE}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM voters WHERE `ভোটার এলাকার নম্বর` = ? AND `লিঙ্গ` = ?"
    params = [area, gender]
    
    if name:
        query += " AND (`নাম` LIKE ? OR `পিতা` LIKE ?)"
        params.append(f"%{name}%")
        params.append(f"%{name}%")
        
    query += " LIMIT 20"
    
    cursor.execute(query, tuple(params))
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return data