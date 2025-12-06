from fastapi import FastAPI, Depends, HTTPException, status, Response 
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select 
from sqlalchemy.exc import IntegrityError 
from contextlib import asynccontextmanager 
from fastapi.middleware.cors import CORSMiddleware 
from .database import engine, SessionLocal 
from .models import Base, UserDB, AddressDB
from .schemas import (UserCreate, 
                      UserRead, 
                      UserUpdate,
                      AddressCreate,
                      AddressRead,
                      AddressUpdate,
                      AddressReadWithOwner)

@asynccontextmanager 
async def lifespan(app: FastAPI): 
    Base.metadata.create_all(bind=engine)    
    yield 
 
app = FastAPI(lifespan=lifespan) 
 
# CORS (add this block) 
app.add_middleware( 
    CORSMiddleware, 
    allow_origins=["*"],   # dev-friendly; tighten in prod 
    allow_methods=["*"], 
    allow_headers=["*"], 
) 

def commit_or_rollback(db: Session, error_msg: str):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=error_msg)

def get_db(): 
    db = SessionLocal() 
    try: 
        yield db 
    finally: 
        db.close() 
        

#------------- Health Check ---------------------
@app.get("/health")
def Health_Check():
    return {"status": "ok",  "service": "users"} 

#------------- Users Endpoints ------------------

# GET: All Users, User by ID
@app.get("/api/users", response_model=list[UserRead]) 
def list_users(db: Session = Depends(get_db)): 
    stmt = select(UserDB).order_by(UserDB.id) 
    return list(db.execute(stmt).scalars()) 
 
@app.get("/api/users/{user_id}", response_model=UserRead) 
def get_user(user_id: int, db: Session = Depends(get_db)): 
    user = db.get(UserDB, user_id) 
    if not user: 
        raise HTTPException(status_code=404, detail="User not found") 
    return user 
 
 #POST new user
@app.post("/api/users", response_model=UserRead, status_code=status.HTTP_201_CREATED) 
def Add_New_User(payload: UserCreate, db: Session = Depends(get_db)): 
    user = UserDB(**payload.model_dump()) 
    db.add(user) 
    try: 
        db.commit() 
        db.refresh(user) 
    except IntegrityError: 
        db.rollback() 
        raise HTTPException(status_code=409, detail="User already exists") 
    return user 

#PATCH user information - updates only what attributes have been changed 
@app.patch("/api/users/{user_id}", response_model=UserRead)
def Update_Partial_User_Information(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updates = payload.model_dump(exclude_unset=True, exclude_none=True) #exclude unset only changes the fields that have been updated 
    for field, value in updates.items():
        setattr(user, field, value)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User update failed (unique constraint)")
    return user

#PUT user information - updates all user attributes
@app.put("/api/users/{user_id}", response_model=UserRead)
def Update_Full_User_Information(user_id: int, payload: UserCreate, db: Session = Depends(get_db)):
    user = db.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field_name, field_value in payload.model_dump().items():
        setattr(user, field_name, field_value)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        # email, phone unique conflict, etc.
        raise HTTPException(status_code=409, detail="User already exists")
    return user

# DELETE a user by ID (triggers ORM cascade -> deletes their projects too)
@app.delete("/api/users/{user_id}", status_code=204)
def Delete_User(user_id: int, db: Session = Depends(get_db)) -> Response:
    user = db.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)  # <-- triggers cascade="all, delete-orphan" on projects
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

#------------- Address Endpoints ------------------
#List Addresses
@app.get("/api/addresses", response_model=list[AddressRead])
def list_addresses(db: Session = Depends(get_db)):
    stmt = select(AddressDB).order_by(AddressDB.id)
    return db.execute(stmt).scalars().all()

#Get user address
@app.get("/api/addresses/{address_id}", response_model=AddressReadWithOwner)
def Get_User_Address(address_id: int, db: Session = Depends(get_db)):
    stmt = (
        select(AddressDB)
        .where(AddressDB.id == address_id)
        .options(selectinload(AddressDB.resident))
    )
    addr = db.execute(stmt).scalar_one_or_none()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    return addr

@app.post("/api/addresses", response_model=AddressRead, status_code=201)
def Add_New_Address(address: AddressCreate, db: Session = Depends(get_db)):
    user = db.get(UserDB, address.resident_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    addr = AddressDB(
        address_line1 = address.address_line1,
        address_line2 = address.address_line2,
        apartment_block_number = address.apartment_block_number,
        county = address.county,
        post_code = address.post_code,
        resident_id = address.resident_id
    )
    db.add(addr)
    commit_or_rollback(db, "Address creation failed")
    db.refresh(addr)
    return addr

@app.patch("/api/addresses/{address_id}", response_model=AddressRead)
def update_address(address_id: int, payload: AddressUpdate, db: Session = Depends(get_db)):
    address = db.get(AddressDB, address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    updates = payload.model_dump(exclude_unset=True, exclude_none=True) #exclude unset only changes the fields that have been updated 
    for field, value in updates.items():
        setattr(address, field, value)

    try:
        db.commit()
        db.refresh(address)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Address update failed (unique constraint)")
    return address

@app.put("/api/addresses/{address_id}", response_model=AddressRead)
def update_address(address_id: int, payload: AddressCreate, db: Session = Depends(get_db)):
    address = db.get(AddressDB, address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    for field_name, field_value in payload.model_dump().items():
        setattr(address, field_name, field_value)
    try:
        db.commit()
        db.refresh(address)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Address already exists")
    return address

# DELETE a user by ID (triggers ORM cascade -> deletes their projects too)
@app.delete("/api/adrdesses/{adrdess_id}", status_code=204)
def Delete_Address(address_id: int, db: Session = Depends(get_db)) -> Response:
    address = db.get(AddressDB, address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    db.delete(address)  # <-- triggers cascade="all, delete-orphan" on projects
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)