# 🎓 EduSphere – Smart Education Management System

<p align="center">
  <strong>A Complete Platform for Managing Students, Teachers and Academic Activities</strong>
</p>

<p align="center">
  A web-based educational management system designed to simplify academic activities by bringing students, teachers, and administrators together in one platform.
</p>

---

## 📌 About EduSphere

**EduSphere** is a web-based Education Management System developed using Python and Flask. It provides a centralized platform where administrators, teachers, and students can manage their academic activities efficiently.

The system helps educational institutions organize subjects, chapters, attendance, assignments, quizzes, and study materials in one place.

## ✨ Key Features

### 👨‍💼 Admin Panel
- Manage student and teacher accounts.
- Create and manage academic subjects.
- Manage academic chapters.
- Assign subjects to teachers.
- Manage attendance records.
- Control academic activities.

### 👨‍🏫 Teacher Panel
- View assigned subjects and chapters.
- Upload and manage study materials.
- Upload chapter files (PDF and PPTX).
- Manage student attendance.
- Create and manage assignments.
- Review student academic activities.

### 👨‍🎓 Student Panel
- Access enrolled subjects.
- View chapters and study materials.
- Download learning resources.
- Access assignments and quizzes.
- View academic information.

### ☁️ Google Drive Integration
- Store study materials on Google Drive.
- Upload chapter resources.
- Organize educational files into folders.
- Access and download stored materials.

### 📚 Academic Management
- Subject management.
- Chapter management.
- Attendance tracking.
- Assignment management.
- Quiz management.
- Student and teacher management.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| HTML5 | Web page structure |
| CSS3 | Styling |
| JavaScript | Frontend interactions |
| Bootstrap | User interface |
| SQLite | Local database |
| SQLAlchemy | Database management |
| Flask-Login | User authentication |
| Google Drive API | Cloud file storage |

## 👥 User Roles

EduSphere provides three main user roles:

1. **Administrator:** Manages users, subjects, chapters, and academic operations.
2. **Teacher:** Manages assigned subjects, attendance, assignments, and study materials.
3. **Student:** Accesses enrolled subjects, learning resources, and academic activities.

## 💻 Installation and Setup

### Prerequisites

- Python 3.x
- Git
- Visual Studio Code (recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/saadkhan723/EduSphere.git
```

### 2. Open the Project Directory

```bash
cd EduSphere
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Environment Variables

Create a `.env` file in the project root directory and configure the required application settings, including:

- Flask secret key.
- Database configuration.
- Google Drive API credentials, where applicable.

**Important:** Never upload passwords, secret keys, OAuth tokens, or private credentials to GitHub.

### 7. Run the Application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

## 📁 Project Structure

```text
EduSphere/
│
├── app.py
├── config.py
├── requirements.txt
├── .gitignore
│
├── database/
├── models/
├── routes/
├── services/
│
├── static/
│   ├── css/
│   ├── images/
│   └── js/
│
├── templates/
│   ├── admin/
│   ├── auth/
│   ├── student/
│   ├── teacher/
│   └── errors/
│
└── uploads/
```

## 🔐 Security

EduSphere includes security-related features such as:

- Role-based access control.
- Password hashing.
- User authentication.
- CSRF protection.
- Protected administrative routes.
- Environment-based configuration for sensitive credentials.

## 📱 Responsive Design

EduSphere is being developed to support desktop, tablet, and mobile screens. Responsive design testing and improvements are part of the ongoing development process.

## 🚀 Future Improvements

- Complete responsive design optimization.
- Enhanced quiz generation features.
- Improved assignment evaluation.
- Advanced academic analytics.
- Production deployment.
- Additional security improvements.

## 🎯 Project Objective

The main objective of EduSphere is to simplify educational management by providing a centralized digital platform for administrators, teachers, and students.

## 👨‍💻 Developer

**Developed by:** Saad Khan

**Academic Program:** BSCS – Cyber Security

**Project Name:** EduSphere

**Category:** Education Management System

**Backend:** Python + Flask

**Frontend:** HTML, CSS, JavaScript, and Bootstrap

**GitHub:** [saadkhan723](https://github.com/saadkhan723)

**Repository:** [EduSphere](https://github.com/saadkhan723/EduSphere)

---

<p align="center">
  <strong>EduSphere – Making Education Management Simpler.</strong>
</p>