# import sqlite3
import time
import asyncio
from fastapi import FastAPI,Depends,HTTPException,Header,UploadFile,File,Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv
import os
import shutil
import requests
from bs4 import BeautifulSoup
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

from jose import jwt,JWTError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base,Session
from passlib.context import CryptContext

from config import settings

# load_dotenv()

app = FastAPI()

# DATABASE_URL = "sqlite:///./mydatabase.db"

# engin=create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

#allow origins
origins=settings.ORIGINS

if isinstance(origins, str):
    origins = [origin.strip() for origin in origins.split(",")]

if not origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False if "*" in origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
)
DATABASE_URL = settings.DATABASE_URL

SECRET_KEY = settings.SECRET_KEY


engin = create_engine(DATABASE_URL)



sessionLocal = sessionmaker(bind=engin)
Base=declarative_base()

class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    completed = Column(String)

    Base.metadata.create_all(bind=engin)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engin)

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/todos/")
def create_todo(title:str, db: Session = Depends(get_db)):
    todo = Todo(title=title, completed="False")
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return {"data": todo, "message": "Todo created successfully"}

@app.get("/todos/")
def read_todos(db: Session = Depends(get_db)):
    todos = db.query(Todo).all()
    return {"data": todos, "message": "Todos retrieved successfully","Total":len(todos)}

@app.get("/todos/{todo_id}")
def read_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo:
        return {"data": todo, "message": "Todo retrieved successfully"}
    else:
        return {"message": "Todo not found"}

@app.put("/todos/{todo_id}")
def update_todo(todo_id: int, title: str, completed: str, db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo:
        todo.title = title
        todo.completed = completed
        db.commit()
        db.refresh(todo)
        return {"data": todo, "message": "Todo updated successfully"}
    else:
        return {"message": "Todo not found"}  
@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo:
        db.delete(todo)
        db.commit()
        return {"message": "Todo deleted successfully"}
    else:
        return {"message": "Todo not found"}  

@app.get("/testapi")
async def testapi():
    await asyncio.sleep(3)
    return {"message": "Hello World VNV"}  



ALGORITHM = "HS256" 
ACCESS_TOKE_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

fack_user_db={"admin":{"username":"admin","password":pwd_context.hash("password")}}

def hash_password(password:str):
    return pwd_context.hash(password)

def verify_password(plain_password:str,hashed_password:str):
    return pwd_context.verify(plain_password,hashed_password)


# create token

def Create_token(data:dict):
    to_encode=data.copy()
    expire=datetime.now(timezone.utc)+timedelta(minutes=15)
    to_encode.update({"exp":expire})
    encoded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

    # login API token oauth2

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user=fack_user_db.get(form_data.username)
    if not user or not verify_password(form_data.password,user["password"]):
        raise HTTPException(status_code=401,detail="Invalid credentials")
    token_data={"sub":user["username"]}
    token=Create_token(token_data)
    return {"access_token":token,"token_type":"bearer"}
# def login(username:str,password:str):
#     if username=="admin" and password=="password":
#         token_data={"sub":username}
#         token=Create_token(token_data)
#         return {"access_token":token,"token_type":"bearer"}
#     else:
#         raise HTTPException(status_code=401,detail="Invalid credentials")

def verify_token(token:str=Depends(oauth2_scheme)):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username=payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401,detail="Invalid token")
        return username
    except jwt.JWTError:
        raise HTTPException(status_code=401,detail="Invalid token")
# def verify_token(token:str= Header(None)):
#     try:
#         payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
#         username=payload.get("sub")
#         if username is None:
#             raise HTTPException(status_code=401,detail="Invalid token")
#         return username
#     except jwt.JWTError:
#         raise HTTPException(status_code=401,detail="Invalid token")
@app.get("/protected")
def protected_route(user: str = Depends(verify_token)):
    return {"message": f"Hello {user}, you have access to the protected route!"}
# @app.get("/")
# def home(db: Session = Depends(get_db)):
#     return {"message": "SQL LIte Connected"}

# connect=sqlite3.connect("mydatabase.db",check_same_thread=False)
# cursor=connect.cursor()

# cursor.execute("CREATE TABLE IF NOT EXISTS todos (id INTEGER PRIMARY KEY, title TEXT,completed TEXT)")

# connect.commit()

# @app.get("/")
# def home():
#     return {"message": "SQL LIte Connected"}   
# from fastapi import FastAPI
# from pydantic import BaseModel

# app = FastAPI()

# class User(BaseModel):
#     name: str
#     age: int
#     email: str

# class Address(BaseModel):
#     city: str
#     zip_code: int
# class UserDetail(BaseModel):
#         name:str
#         age:int
#         address: Address

# @app.get("/")
# def home():
#     return {"message": "Hello World VNV"}


# # About Route
# @app.get("/about")
# def about():
#     return {"message": "This is about page"}


# # User Route
# @app.get("/users/{user_id}")
# def get_user(user_id:int):
#     return {"User ID":user_id}

#     # Product Route
# @app.get("/Products")
# def get_products(name:str=None):
#     return {"Name": name}


# @app.get("/items")
# def get_products(name:str=None,price:int=0):
#     return {"Name": name,"Price": price}


    
# @app.post("/Create_user")
# def Create_user(user:User):
#     return {"data": user,"message": "User created successfully"}  


# @app.post("/Create_userdetail")
# def Create_userdetail(user:UserDetail):
#             return {"data": user,"message": "User created successfully"}


# Step 1: Create a directory for uploads

UPLOAD_DIR="uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

    # Step 2: Create an endpoint for file uploads
app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")
@app.post("/uploadfile/")
def upload_file(file: UploadFile = File(...)):
    filename=file.filename
    file_location=os.path.join(UPLOAD_DIR,filename)
    if not filename:
        raise HTTPException(status_code=400,detail="No file uploaded")
    with open(file_location,"wb") as buffer:
        shutil.copyfileobj(file.file,buffer)
    return {"info": f"file '{filename}' saved at '{file_location}'"}

@app.get("/files/{filename}")
def get_file(filename:str):
    file_location=os.path.join(UPLOAD_DIR,filename)
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404,detail="File not found")
    return {"file_location": file_location}



@app.get("/add")
def add(a:int,b:int):
    return {"result": a+b}


# Third part API call
response = requests.get("https://jsonplaceholder.typicode.com/posts")

data=response.json()
print(data[:2])



# get all data

@app.get("/posts")

def get_posts():
    response = requests.get("https://jsonplaceholder.typicode.com/posts")
    data = response.json()
    return {"data": data}


# Web Ccrowling 
    Url="http://example.com"
    response=requests.get(Url)
    soup=BeautifulSoup(response.content,"html.parser")

    print(soup.title.text)


# Web Ccrowling 
@app.get("/crawl")
def get_news(page:int=1,limit:int=5):
    Url = "https://news.ycombinator.com/"
    response = requests.get(Url)
    soup = BeautifulSoup(response.content, "html.parser")

    title = []

    for item in soup.find_all("span", class_="titleline"):
        title.append(item.text)

    start=(page-1)*limit
    end=page*limit


    return {"page": page,"limit": limit,"data": title[start:end]}

cache_data=[]
last_updated=0

@app.get("/NEWS")
def get_newsDATA():
    global   cache_data, last_updated

    start = time.time()


    if(time.time()-last_updated>60):
        print("Data is updated")
        Url = "https://news.ycombinator.com/"
        response = requests.get(Url)
        soup = BeautifulSoup(response.text, "html.parser")

        cache_data = [
        item.text for item in soup.find_all("span", class_="titleline")]

        last_updated = time.time()
    else:
         print("Data is from cache")
    end=time.time()
    time_taken=round(end-start,4)

    print  ("Time taken:", time_taken)

    return {"data": cache_data}

    # one api calling multiple time then take 1 minit onl 5 time calll
limiter = Limiter(key_func=get_remote_address)
app.state.Limiter=limiter

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request, exc):
        return JSONResponse(
            status_code=429,
            content={"message": "Rate limit exceeded. Try again later."}
        )
@app.get("/limited")
@limiter.limit("5/minute")
def get_limited_data(request:Request):
    return {"message": "This endpoint is rate limited to 5 requests per minute."}


