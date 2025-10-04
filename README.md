# SIH25012-Infinity_loop
RFID + Facial Recognition based smart attendance system for rural schools. Students use RFID-enabled ID cards linked to stored facial embeddings. Live face capture is matched only against the cardholder’s embedding, ensuring accuracy, preventing proxy, and reducing compute needs under limited resources.

# 🎓 Smart Attendance System

A **RFID + Facial Recognition based smart attendance system** designed to solve the problem of unreliable attendance tracking in **rural schools**.  
This system works **offline-first**, is **cost-effective**, and prevents misuse of proxy attendance while being easy to deploy.

---

## 🌍 Problem Background
Rural schools face challenges that make traditional biometric or cloud-based attendance solutions impractical:
- ❌ Poor or no internet connectivity  
- ❌ Frequent power cuts  
- ❌ Limited technical staff and training  
- ❌ Expensive biometric hardware  

Our solution provides a **lightweight, software-first approach** that uses **RFID-enabled ID cards** combined with **local facial verification**.  
This ensures accurate attendance without the need for continuous internet or expensive infrastructure.

---

## ✅ Why RFID + Face Recognition?

- **RFID only?**  
  Anyone can tap multiple ID cards to fake attendance.  

- **Face recognition only?**  
  Requires matching live images against *all* student records → high compute + time cost.  

- **RFID + Face together ✅**  
  - RFID identifies *who should be present*  
  - Face recognition verifies the *actual student*  
  - One-to-one matching = **fast, accurate, secure**  

---

## ✨ Features
- 🪪 **RFID linked attendance** – Each student gets an RFID-enabled ID card.  
- 👤 **Facial verification** – Live camera feed confirms student identity.  
- ⚡ **Lightweight verification** – Match live face against *only* the cardholder’s embedding.  
- 📊 **Interactive Dashboard** – View live status, daily summary, logs, and charts.  
- 🏫 **Student Enrollment** – Register new students with RFID + face capture.  
- 🛠 **Offline-first design** – Works with local storage/database (SQLite).  
- 💰 **Low yearly cost** – Practical for government or NGO-driven adoption.  

---

## 🗂 Project Structure

```
├── sih_rfid.ino      # ESP32/Arduino code for RFID card reader
├── app.py            # Flask backend API for face verification & attendance
├── index.html        # Tailwind + Chart.js web dashboard (frontend UI)
├── /static           # (optional) Static assets - icons, CSS, JS
├── /database         # SQLite or local DB storing student data & attendance logs
└── README.md         # Project documentation
```

---

## ⚙️ Setup Instructions

### 1️⃣ Backend Setup

- Install Python 3.9+
- Clone this repository:
  ```bash
  git clone https://github.com/yourusername/smart-attendance.git
  cd smart-attendance
  ```
- Install dependencies:
  ```bash
  pip install flask opencv-python face-recognition numpy sqlite3
  ```
- Run the Flask server:
  ```bash
  python app.py
  ```
  The backend API will start on: [http://localhost:5000](http://localhost:5000)

### 2️⃣ Frontend Setup

- Open the file `index.html` in your browser.
- The dashboard automatically connects to the backend API.
- You can access:
  - Live Attendance View
  - Dashboard (Summary View)
  - Enroll Student
  - Attendance Logs

### 3️⃣ RFID Device Setup

- Open `sih_rfid.ino` in Arduino IDE or PlatformIO.
- Connect your ESP32/Arduino with an RC522 RFID module.
- Update the Wi-Fi credentials and backend URL inside the `.ino` file.
- Flash it to the board and run.
- The RFID module streams card UID data to the backend when a card is scanned.

---

## 🚀 How It Works

### Enrollment

1. Teacher opens the Enroll Student page.
2. Student’s RFID card is scanned → UID fetched automatically.
3. Face image is captured through the webcam.
4. System creates a master face embedding and saves:
   ```json
   {
     "name": "Student Name",
     "roll_number": "123",
     "rfid_uid": "04A1B2C3D4",
     "embedding": [...vector data...]
   }
   ```

### Attendance Process

1. Student taps their RFID card in the morning.
2. Backend fetches their face embedding.
3. Live camera image is captured.
4. The system verifies if the face matches the embedding.
5. On success → attendance marked with timestamp.
6. On failure → alert for possible proxy attempt.

### Dashboard

- Live verification view shows current scans.
- Dashboard displays total students, present/absent count, and daily stats.
- Attendance logs can be viewed chronologically.

---

## 📊 Dashboard Overview

| Section         | Description                                             |
| --------------- | ------------------------------------------------------- |
| Live Attendance | Displays real-time status and verification results      |
| Dashboard       | Shows total students, present/absent count, donut chart |
| Enroll Student  | Register new students using RFID and face capture       |
| Logs            | View full attendance history with timestamps            |

---

## 💡 Technical Highlights

**Frontend:**

- Built using TailwindCSS and Chart.js
- Real-time updates using Server-Sent Events (SSE)

**Backend:**

- Flask API serving `/api/enroll`, `/api/verify_attendance`, `/api/attendance`, `/api/stream`
- Uses `face_recognition` for facial embeddings & comparison
- Stores data locally (SQLite for offline-first usage)

**RFID Client:**

- ESP32/Arduino sketch sends RFID scans to backend over HTTP
- Minimal network usage, robust under low connectivity

---

## 🧠 Design Philosophy

- **Offline-first** – All data and verification happen locally.
- **Lightweight** – Optimized for low power and minimal compute.
- **Cost-effective** – Affordable for rural and government schools.
- **Scalable** – Can be expanded to multiple schools or central monitoring.

---

## 🔮 Future Enhancements

- Offline → Cloud sync when internet available
- Role-based admin dashboard (teacher, district officer)
- Mobile-compatible version
- Integration with government education data systems
- Automatic daily/weekly attendance reports

---

## 🤝 Contributing

Contributions are welcome!

To contribute:

1. Fork the repository
2. Create a new branch (`feature/my-feature`)
3. Commit your changes
4. Push to the branch and open a Pull Request

---

## 🧾 License

This project is licensed under the MIT License.
You are free to use, modify, and distribute with attribution.

---

## 🙌 Acknowledgements

- `face_recognition` – for facial embeddings and matching
- Flask – lightweight backend framework
- TailwindCSS – modern utility-first CSS
- Chart.js – data visualization for the dashboard

---

## 🖼️ System Workflow Diagram

```
[RFID Scan] → [Fetch Student Data] → [Capture Face] → [Compare with Embedding]
       ↓                ↓                        ↓
   UID Verified   Retrieve Embedding       Face Verified ✅
       ↓                ↓                        ↓
      └──────────────→ Attendance Logged (Local DB)
```

---

## 💬 Summary

This project offers a practical, software-first attendance solution built for schools with limited connectivity and resources.
By pairing RFID identification with facial verification, it creates a secure, efficient, and low-cost method to ensure accurate attendance — truly the right fit for rural education systems.
