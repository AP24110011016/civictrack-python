# 🏛️ CivicTrack — Full Python Backend

## Python Libraries Used
| Library | Purpose |
|---------|---------|
| Flask | Web framework + REST API |
| PyMongo | MongoDB database |
| bcrypt | Password hashing |
| Flask-JWT-Extended | Authentication |
| OpenCV | Image processing + classification |
| NumPy | Pixel feature extraction |
| Pandas | Data analytics engine |
| Matplotlib | Chart generation |
| ReportLab | PDF report generation |
| smtplib | Email notifications |

---

## Step by Step Setup

### Step 1 — Go to project folder
```
cd civictrack-python
```

### Step 2 — Create .env file
```
copy .env.example .env
```
Fill .env with your MongoDB URI.

### Step 3 — Install all Python packages
```
pip install -r requirements.txt
```

### Step 4 — Seed the database
```
python seed.py
```

### Step 5 — Start the server
```
python app.py
```

### Step 6 — Open frontend
Open static/index.html with Live Server in VS Code

---

## Login Accounts
| Role | Email | Password |
|------|-------|----------|
| Super Admin | superadmin@civic.in | admin123 |
| Admin | admin@civic.in | admin123 |
| Officer | officer1@civic.in | officer123 |
