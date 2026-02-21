from fastapi import FastAPI,HTTPException,Depends
import sqlite3
from pydantic import BaseModel,EmailStr 
from typing import Optional
from passlib.context import CryptContext
from database import init_user_db
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi import File, UploadFile, Depends
import tensorflow as tf
import numpy as np
from PIL import Image
import io
from database import init_user_db
from seed_plants import seed_plants

app = FastAPI()

@app.on_event("startup")
def startup():
    init_user_db()
    seed_plants()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH='plants.db'

model = tf.keras.models.load_model("plant_identification_model2.keras")

class_names = [
    'Alpinia Galanga', 'Amaranthus Viridis', 'Artocarpus Heterophyllus',
    'Azadirachta Indica', 'Basella Alba',
    'Brassica Juncea', 'Carissa Carandas', 'Citrus Limon',
    'Ficus Auriculata', 'Ficus Religiosa',
    'Hibiscus Rosa-sinensis', 'Jasminum',
    'Mangifera Indica', 'Mentha',
    'Moringa Oleifera', 'Murraya Koenigii',
    'Nerium Oleander', 'Nyctanthes Arbor-tristis',
    'Ocimum Tenuiflorum', 'Piper Betle',
    'Plectranthus Amboinicus', 'Pongamia Pinnata',
    'Psidium Guajava', 'Punica Granatum',
    'Santalum Album', 'Syzygium Cumini',
    'Syzygium Jambos', 'Tabernaemontana Divaricata',
    'Trigonella Foenum-graecum', 'Wrightia Tinctoria'
]



class UserAuth(BaseModel):
    email:EmailStr
    password:str
    name: Optional[str]=None

SECRET_KEY = "ayurvision_jwt_secret_key_2026_very_secure_123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  

pwd_context=CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    
    conn=sqlite3.connect(DB_PATH,check_same_thread=False)

    conn.row_factory=sqlite3.Row

    try:
        yield conn
    
    finally:
        conn.close()

@app.post("/register")

async def register(user:UserAuth, db:sqlite3.Connection=Depends(get_db)):
    cursor=db.cursor()

    hashed_password =pwd_context.hash(user.password[:72])

    try:
        cursor.execute('INSERT INTO users(email,password,name) values(?,?,?)',
                       (user.email,hashed_password,user.name))

        db.commit()
        return{"success":True}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    

@app.post("/login")

async def login(user:UserAuth, db:sqlite3.Connection=Depends(get_db)):

    cursor=db.cursor()
    cursor.execute('SELECT id, password, name, email From users where email=?',(user.email,))
    record=cursor.fetchone()

    if record and pwd_context.verify(user.password[:72],record["password"]):

        access_token = create_access_token(
            data={"sub": record["email"], "name": record["name"], "id": record["id"]},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return{
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": record["id"],
                "name": record["name"],
                "email": record["email"]
            }
        }
    raise HTTPException(status_code=401,detail="Invalid credentials")




@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).resize((224, 224))
    img_array = np.array(image) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    predictions = model.predict(img_array)
    confidence = float(np.max(predictions))
    class_index = np.argmax(predictions)

    if confidence < 0.80:
        raise HTTPException(status_code=400, detail="No plant matched")

    plant_name = class_names[class_index]

    cursor = db.cursor()
    cursor.execute("SELECT * FROM plants WHERE scientific_name=?",
                   (plant_name,))
    plant = cursor.fetchone()


    cursor.execute("""
    INSERT INTO history(user_id, plant_name, confidence)
    VALUES (?, ?, ?)
    """, (user["id"], plant_name, confidence))

    db.commit()

    return {
        "scientific_name": plant["scientific_name"],
        "common_name": plant["common_name"],
        "description": plant["description"],
        "medicinal_uses": plant["medicinal_uses"],
        "properties": plant["properties"],
        "parts_used": plant["parts_used"],
        "preparation": plant["preparation"],
        "market_value": plant["market_value"],
        "sowing": plant["sowing"],
        "harvest": plant["harvest"],
        "toxicity": plant["toxicity"],
        "confidence": confidence
    }


@app.get("/history")
def get_history(user=Depends(get_current_user),
                db: sqlite3.Connection = Depends(get_db)):

    cursor = db.cursor()
    cursor.execute("""
    SELECT plant_name, confidence, date
    FROM history
    WHERE user_id=?
    ORDER BY date DESC
    """, (user["id"],))

    return cursor.fetchall()