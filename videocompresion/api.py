from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from moviepy.editor import VideoFileClip
from PIL import Image
import os
import shutil
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uvicorn

app = FastAPI()

# Database setup
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, index=True)
    thumbnail_path = Column(String, index=True)
    workout_id = Column(Integer, index=True)
    set_id = Column(Integer, index=True)

Base.metadata.create_all(bind=engine)

@app.post("/upload/")
async def upload_video(file: UploadFile = File(...), workout_id: int = Form(...), set_id: int = Form(...)):
    # Define paths
    upload_dir = "uploaded_videos"
    compressed_dir = "compressed_videos"
    thumbnail_dir = "thumbnails"

    # Ensure directories exist
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(compressed_dir, exist_ok=True)
    os.makedirs(thumbnail_dir, exist_ok=True)

    # Save uploaded file
    upload_path = os.path.join(upload_dir, file.filename)
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Compress the video
    compressed_path = os.path.join(compressed_dir, f"compressed_{file.filename}")
    with VideoFileClip(upload_path) as video:
        video.write_videofile(compressed_path, codec="libx264", audio_codec="aac")

        # Generate thumbnail
        thumbnail_path = os.path.join(thumbnail_dir, f"{file.filename}.jpg")
        frame = video.get_frame(1)  # Get frame at 1 second
        image = Image.fromarray(frame)
        image.save(thumbnail_path)

    # Store metadata in the database
    db = SessionLocal()
    video_entry = Video(path=compressed_path, thumbnail_path=thumbnail_path, workout_id=workout_id, set_id=set_id)
    db.add(video_entry)
    db.commit()
    db.refresh(video_entry)
    db.close()

    return JSONResponse(content={"message": "Video uploaded and compressed successfully!"})

@app.get("/videos/")
async def get_videos():
    db = SessionLocal()
    videos = db.query(Video).all()
    db.close()
    return videos

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
