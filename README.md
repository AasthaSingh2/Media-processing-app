
# 🎬 Media Processing App

A full-stack web application that processes media from a public URL using FFmpeg. Users can generate thumbnails, compress videos, or extract audio through a simple and interactive interface.

---

## 🚀 Features

- 🔗 Input public video URL
- 🖼 Generate thumbnail (frame extraction at ~2s)
- 📉 Compress video to reduce size
- 🎧 Extract audio from video (MP3)
- ⚡ Real-time processing using FastAPI backend
- 🎯 Clean UI with preview (image/video/audio)
- ❌ Error handling for invalid URLs and failures
- ⏳ Loading state + smooth user experience

---

## 🛠 Tech Stack

### Frontend
- React (Vite)
- CSS

### Backend
- FastAPI (Python)
- FFmpeg (via subprocess)
- Requests library

---

## ⚙️ How It Works

1. User enters a public video URL
2. Selects an operation (thumbnail / compress / extract audio)
3. Frontend sends request to FastAPI backend
4. Backend:
   - Downloads media file
   - Processes it using FFmpeg (subprocess)
   - Saves output file
5. Processed result is returned and displayed on UI

---

## 🔌 API Endpoint

### POST `/process`

#### Request:
```json
{
  "url": "https://example.com/video.mp4",
  "operation": "thumbnail"
}
````

#### Response:

```json
{
  "status": "success",
  "output": "http://localhost:8000/outputs/file.jpg",
  "operation": "thumbnail"
}
```

---

## 📂 Project Structure

```
media-processing-app/
  backend/
    main.py
    temp/
    outputs/
    requirements.txt
  frontend/
    src/
      App.jsx
      App.css
```

---

## ▶️ Setup Instructions

### 1. Clone repository

```bash
git clone <your-repo-link>
cd media-processing-app
```

---

### 2. Backend setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs at:

```
http://127.0.0.1:8000
```

---

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```
http://localhost:5173
```

---

## 📸 Sample Input

```
https://samplelib.com/lib/preview/mp4/sample-5s.mp4
```

---

## ⚠️ Assumptions

* Input URL must be publicly accessible
* Supported formats depend on FFmpeg compatibility
* Files are temporarily stored and cleaned after processing

---

## ❗ Error Handling

* Invalid URL handling
* FFmpeg execution failure handling
* Timeout for long-running processes
* User-friendly error messages on UI

---

## 🔮 Future Improvements

* Background job queue (Celery / Redis)
* Progress tracking for large files
* Cloud storage (AWS S3)
* Authentication system
* Drag-and-drop upload support

---

## 👩‍💻 Author

Aastha Singh
