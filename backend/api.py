from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from typing import Optional
from datetime import date

# Database connection (MySQL)
#DATABASE_URL = "mysql://user:password@localhost/dbname"
#engine = create_engine(DATABASE_URL)
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Database connection
DATABASE_URL = "sqlite:///./workout_tracker.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



Base = declarative_base()


# Models
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)

    blocks = relationship("Block", back_populates="user")
    workouts = relationship("Workout", back_populates="user")
    exercises = relationship("Exercise", back_populates="user")

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    exercise_type = Column(String, nullable=False)
    exercise_name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    sets = relationship("SetPerformed", back_populates="exercise")
    user = relationship("User", back_populates="exercises")

class Block(Base):
    __tablename__ = "blocks"

    block_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    workouts = relationship("Workout", back_populates="block")
    user = relationship("User", back_populates="blocks")

class Workout(Base):
    __tablename__ = "workouts"

    workout_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    block_id = Column(Integer, ForeignKey("blocks.block_id"), nullable=False)

    block = relationship("Block", back_populates="workouts")
    sets = relationship("SetPerformed", back_populates="workout")
    user = relationship("User", back_populates="workouts")

class SetPerformed(Base):
    __tablename__ = "sets_performed"

    set_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    workout_id = Column(Integer, ForeignKey("workouts.workout_id"), nullable=False)
    date = Column(Date, nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    weight = Column(Float, nullable=False)
    repetitions = Column(Integer, nullable=False)
    RPE = Column(Float)
    RIR = Column(Float)

    exercise = relationship("Exercise", back_populates="sets")
    workout = relationship("Workout", back_populates="sets")
    user = relationship("User", foreign_keys=[user_id])

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Pydantic models for request bodies
class UserCreate(BaseModel):
    nickname: str
    email: EmailStr

class UserResponse(BaseModel):
    user_id: int
    nickname: str
    email: str

class ExerciseCreate(BaseModel):
    exercise_type: str
    exercise_name: str
    user_id: int

class SetPerformedCreate(BaseModel):
    user_id: int
    workout_id: int
    date: date
    exercise_id: int
    weight: float
    repetitions: int
    RPE: Optional[float] = None
    RIR: Optional[float] = None

class BlockCreate(BaseModel):
    user_id: int

class WorkoutCreate(BaseModel):
    user_id: int
    block_id: int
# Pydantic models for response
class SetPerformedResponse(BaseModel):
    set_id: int
    user_id: int
    workout_id: int
    date: date
    exercise_id: int
    weight: float
    repetitions: int
    RPE: Optional[float]
    RIR: Optional[float]

class WorkoutResponse(BaseModel):
    workout_id: int
    user_id: int
    block_id: int

class ExerciseResponse(BaseModel):
    id: int
    exercise_type: str
    exercise_name: str
    user_id: int

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints
@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: SessionLocal = Depends(get_db)):
    db_user = User(nickname=user.nickname, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users", response_model=UserResponse)
def get_user(user_id: Optional[int] = None, nickname: Optional[str] = None, email: Optional[str] = None, db: SessionLocal = Depends(get_db)):
    if user_id:
        user = db.query(User).filter(User.user_id == user_id).first()
    elif nickname:
        user = db.query(User).filter(User.nickname == nickname).first()
    elif email:
        user = db.query(User).filter(User.email == email).first()
    else:
        raise HTTPException(status_code=400, detail="Please provide user_id, nickname, or email")
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/add_exercise")
def add_exercise(exercise: ExerciseCreate, db: SessionLocal = Depends(get_db)):
    db_exercise = Exercise(**exercise.dict())
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)
    return {"id": db_exercise.id, **exercise.dict()}

@app.post("/add_set_performed")
def add_set_performed(set_performed: SetPerformedCreate, db: SessionLocal = Depends(get_db)):
    db_set = SetPerformed(**set_performed.dict())
    db.add(db_set)
    db.commit()
    db.refresh(db_set)
    return {"set_id": db_set.set_id, **set_performed.dict()}

@app.post("/create_block")
def create_block(block: BlockCreate, db: SessionLocal = Depends(get_db)):
    db_block = Block(**block.dict())
    db.add(db_block)
    db.commit()
    db.refresh(db_block)
    return {"block_id": db_block.block_id, **block.dict()}

@app.post("/create_workout")
def create_workout(workout: WorkoutCreate, db: SessionLocal = Depends(get_db)):
    db_workout = Workout(**workout.dict())
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    return {"workout_id": db_workout.workout_id, **workout.dict()}

@app.get("/sets", response_model=List[SetPerformedResponse])
def list_sets(db: Session = Depends(get_db)):
    sets = db.query(SetPerformed).all()
    return sets

@app.get("/workouts", response_model=List[WorkoutResponse])
def list_workouts(db: Session = Depends(get_db)):
    workouts = db.query(Workout).all()
    return workouts

@app.get("/exercises", response_model=List[ExerciseResponse])
def list_exercises(db: Session = Depends(get_db)):
    exercises = db.query(Exercise).all()
    return exercises


@app.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@app.get("/user/{user_id}/workouts", response_model=List[WorkoutResponse])
def list_user_workouts(user_id: int, db: Session = Depends(get_db)):
    workouts = db.query(Workout).filter(Workout.user_id == user_id).all()
    return workouts

@app.get("/exercises", response_model=List[ExerciseResponse])
def list_exercises(
    exercise_id: Optional[int] = None,
    exercise_type: Optional[str] = None,
    exercise_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Exercise)
    if exercise_id:
        query = query.filter(Exercise.id == exercise_id)
    if exercise_type:
        query = query.filter(Exercise.exercise_type == exercise_type)
    if exercise_name:
        query = query.filter(Exercise.exercise_name.ilike(f"%{exercise_name}%"))
    return query.all()