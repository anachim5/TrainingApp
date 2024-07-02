from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from typing import List, Optional
import enum

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    nickname = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    exercises = relationship("Exercise", back_populates="user")
    blocks = relationship("Block", back_populates="user")
    workouts = relationship("Workout", back_populates="user")
    sets_performed = relationship("SetPerformed", back_populates="user")

class ExerciseType(enum.Enum):
    COMP = "COMP"
    VARIATION = "VARIATION"
    ACCESSORY = "ACCESSORY"

class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True, index=True)
    exercise_type = Column(Enum(ExerciseType))
    exercise_name = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="exercises")
    sets_performed = relationship("SetPerformed", back_populates="exercise")

class Block(Base):
    __tablename__ = "blocks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="blocks")
    workouts = relationship("Workout", back_populates="block")

class Workout(Base):
    __tablename__ = "workouts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    block_id = Column(Integer, ForeignKey("blocks.id"))
    user = relationship("User", back_populates="workouts")
    block = relationship("Block", back_populates="workouts")
    sets_performed = relationship("SetPerformed", back_populates="workout")

class SetPerformed(Base):
    __tablename__ = "sets_performed"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    workout_id = Column(Integer, ForeignKey("workouts.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    date = Column(Date)
    weight = Column(Float)
    rpe = Column(Float, nullable=True)
    rir = Column(Float, nullable=True)
    repetitions = Column(Integer)
    user = relationship("User", back_populates="sets_performed")
    workout = relationship("Workout", back_populates="sets_performed")
    exercise = relationship("Exercise", back_populates="sets_performed")

Base.metadata.create_all(bind=engine)

# Pydantic models
class UserCreate(BaseModel):
    email: str
    nickname: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ExerciseCreate(BaseModel):
    exercise_type: ExerciseType
    exercise_name: str

class SetPerformedCreate(BaseModel):
    workout_id: int
    exercise_id: int
    date: str
    weight: float
    rpe: Optional[float] = None
    rir: Optional[float] = None
    repetitions: int

class BlockCreate(BaseModel):
    id: int = None

class WorkoutCreate(BaseModel):
    id: int = None
    block_id: int

class BlockResponse(BaseModel):
    id: int
    user_id: int

    class Config:
        orm_mode = True

# Helper functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# Endpoints
@app.post("/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, nickname=user.nickname, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/add_exercise")
async def add_exercise(exercise: ExerciseCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_exercise = Exercise(exercise_type=exercise.exercise_type, exercise_name=exercise.exercise_name, user_id=current_user.id)
    db.add(new_exercise)
    db.commit()
    db.refresh(new_exercise)
    return {"message": "Exercise added successfully", "exercise_id": new_exercise.id}

@app.post("/add_set_performed")
async def add_set_performed(set_performed: SetPerformedCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_set = SetPerformed(
        user_id=current_user.id,
        workout_id=set_performed.workout_id,
        exercise_id=set_performed.exercise_id,
        date=datetime.strptime(set_performed.date, "%Y-%m-%d").date(),
        weight=set_performed.weight,
        rpe=set_performed.rpe,
        rir=set_performed.rir,
        repetitions=set_performed.repetitions
    )
    db.add(new_set)
    db.commit()
    db.refresh(new_set)
    return {"message": "Set performed added successfully", "set_id": new_set.id}

@app.post("/create_block")
async def create_block(block: BlockCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_block = Block(id=block.id, user_id=current_user.id)
    db.add(new_block)
    db.commit()
    db.refresh(new_block)
    return {"message": "Block created successfully", "block_id": new_block.id}

@app.post("/create_workout")
async def create_workout(workout: WorkoutCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_workout = Workout(id=workout.id, user_id=current_user.id, block_id=workout.block_id)
    db.add(new_workout)
    db.commit()
    db.refresh(new_workout)
    return {"message": "Workout created successfully", "workout_id": new_workout.id}

@app.get("/user/{user_identifier}")
async def get_user(user_identifier: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.id == user_identifier) | 
        (User.nickname == user_identifier) | 
        (User.email == user_identifier)
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "nickname": user.nickname}

@app.get("/exercises")
async def list_exercises(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exercises = db.query(Exercise).filter(Exercise.user_id == current_user.id).all()
    return exercises

@app.get("/workouts")
async def list_workouts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    workouts = db.query(Workout).filter(Workout.user_id == current_user.id).all()
    return workouts

@app.get("/sets")
async def list_sets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sets = db.query(SetPerformed).filter(SetPerformed.user_id == current_user.id).all()
    return [
        {
            "id": set.id,
            "workout_id": set.workout_id,
            "exercise_id": set.exercise_id,
            "date": str(set.date),
            "weight": set.weight,
            "repetitions": set.repetitions,
            "rpe": set.rpe,
            "rir": set.rir
        } for set in sets
    ]

@app.get("/blocks")
async def list_blocks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    blocks = db.query(Block).filter(Block.user_id == current_user.id).all()
    return [
        {
            "id": block.id,
            "user_id": block.user_id,
            # Add any other block attributes you want to include
        } for block in blocks
    ]