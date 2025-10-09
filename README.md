# 🚀 Django Firebase CRM System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.0-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557c?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)

A cloud-based Customer Relationship Management system built with Django and Firebase, featuring real-time data synchronization, interactive dashboards, and comprehensive analytics.

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [API Documentation](#-api-documentation)
- [Installation](#-installation)
- [Project Structure](#-project-structure)
- [What I Learned](#-what-i-learned)

---

## 🎯 Overview

This CRM system is a full-stack web application that helps businesses manage customer relationships, track sales pipelines, monitor team performance, and generate analytics reports. Built as a school project, it demonstrates modern web development practices using Django as the backend framework and Firebase for real-time cloud data storage.

**Key Highlights:**
- 📊 Real-time dashboard with live metrics
- 👥 Complete customer lifecycle management
- 💼 Sales pipeline tracking with stage visualization
- 📈 Advanced analytics and reporting with chart generation
- ☁️ Cloud-based data storage using Firebase Firestore
- 🔐 Secure authentication and role-based access control
- 📱 Responsive design for mobile and desktop

---

## ✨ Features

### 🏢 Customer Management
- Create, read, update, and delete customer records
- Track customer status (Lead, Active, Inactive)
- Manage customer contact information and company details
- Add custom tags and notes for each customer
- Filter and search capabilities

### 💰 Sales Pipeline
- Deal creation and tracking across multiple stages
- Pipeline stages: Lead, Qualified, Proposal, Negotiation, Closed Won, Closed Lost
- Deal value tracking and probability assessment
- Visual pipeline representation
- Stage-by-stage revenue analytics

### 👥 Employee Management
- Employee profiles with department and role information
- Skills tracking using lists
- Salary and hire date management
- Department-wise analytics

### ✅ Task Management
- Create and assign tasks to team members
- Priority levels (High, Medium, Low)
- Due date tracking
- Task status monitoring
- Overdue task alerts

### 📊 Analytics Dashboard
- Real-time metrics and KPIs
- Interactive charts using Matplotlib and Chart.js
- Customer status distribution (pie charts)
- Deal pipeline visualization (bar charts)
- Revenue trends over time (line charts)
- Department distribution analysis (donut charts)
- Data export capabilities

---

## 🏗️ System Architecture

### Technology Stack

**Backend:**
- **Django 4.2** - Web framework for building the application
- **Python 3.8+** - Core programming language
- **Firebase Admin SDK** - Real-time cloud database integration
- **Django REST Framework** - API endpoints

**Frontend:**
- **Bootstrap 5** - Responsive UI framework
- **HTML5/CSS3** - Modern web standards
- **JavaScript (Vanilla)** - Interactive functionality
- **Chart.js** - Client-side charting

**Data & Analytics:**
- **Matplotlib** - Python chart generation
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computations

**Deployment:**
- **Gunicorn** - WSGI HTTP server
- **WhiteNoise** - Static file serving

### Database Architecture

The application uses a hybrid approach:
- **Firebase Firestore** - Primary cloud database for all CRM data (customers, deals, employees, tasks)
- **SQLite** - Minimal local database for Django sessions and authentication only

**Firebase Collections:**
```
firestore
├── customers/      # Customer records
├── employees/      # Employee data
├── deals/         # Sales opportunities
└── tasks/         # Task assignments
```

Each collection stores documents with structured data using Python dictionaries, with automatic timestamp management and user tracking.

---

## 🔌 API Documentation

### Authentication
All API endpoints require authentication. Include session cookie or authentication token.

### Endpoints

#### Customer API
```http
GET /api/customers/
```
Returns list of all customers with filtering options.

**Query Parameters:**
- `status` - Filter by customer status (Lead, Active, Inactive)

**Response:**
```json
[
  {
    "id": "abc123",
    "name": "John Doe",
    "email": "john@example.com",
    "company": "Tech Corp",
    "status": "Active",
    "value": 50000,
    "created_at": "2025-01-15T10:30:00"
  }
]
```

#### Deal API
```http
GET /api/deals/
```
Returns all deals in the sales pipeline.

**Response:**
```json
[
  {
    "id": "deal123",
    "title": "Enterprise License",
    "customer_id": "abc123",
    "value": 75000,
    "stage": "Proposal",
    "probability": 60,
    "expected_close": "2025-03-01"
  }
]
```

#### Create Customer
```http
POST /api/customer/add/
```
Creates a new customer record.

**Request Body:**
```json
{
  "name": "Jane Smith",
  "email": "jane@company.com",
  "phone": "+1234567890",
  "company": "ABC Inc",
  "status": "Lead",
  "value": 25000,
  "notes": "Interested in premium package"
}
```

#### Update Record
```http
POST /api/<collection>/<doc_id>/update/
```
Updates any record in Firebase.

**Path Parameters:**
- `collection` - The Firebase collection (customers, deals, employees, tasks)
- `doc_id` - Document ID to update

#### Delete Record
```http
POST /api/<collection>/<doc_id>/delete/
```
Deletes a record from Firebase.

### Data Structures

**Customer Object:**
- `name` (string) - Customer full name
- `email` (string) - Email address
- `phone` (string) - Phone number
- `company` (string) - Company name
- `status` (string) - Lead | Active | Inactive
- `value` (number) - Potential revenue
- `tags` (array) - Custom tags
- `notes` (string) - Additional notes

**Deal Object:**
- `title` (string) - Deal name
- `customer_id` (string) - Associated customer
- `value` (number) - Deal value
- `stage` (string) - Pipeline stage
- `probability` (number) - Win probability (0-100)
- `expected_close` (date) - Expected close date

---

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Firebase account
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/6ba3i/Django-CRM-System
   cd crm_project
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Firebase Configuration**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a new project
   - Enable Firestore Database
   - Navigate to Project Settings > Service Accounts
   - Generate a new private key
   - Download the JSON file and save it as `core/serviceAccountKey.json`

5. **Environment Setup**
   
   Copy `.env.template` to `.env`:
   ```bash
   cp .env.template .env
   ```
   
   Generate a Django secret key:
   ```bash
   python generate_secret_key.py
   ```
   
   Update `.env` with your Firebase configuration:
   ```env
   SECRET_KEY=<generated-secret-key>
   DEBUG=True
   FIREBASE_CREDENTIALS_PATH=core/serviceAccountKey.json
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_DATABASE_URL=https://your-project-id.firebaseio.com
   ```

6. **Verify Setup**
   ```bash
   python check_setup.py
   ```

7. **Run the Application**
   ```bash
   python run_firebase_crm.py
   ```
   
   The application will be available at `http://127.0.0.1:8000`

8. **Access the System**
   - Open your browser to `http://127.0.0.1:8000`
   - Create an account or use demo credentials (if configured in `.env`)

---

## 📁 Project Structure

```
crm_project/
│
├── core/                          # Core configurations
│   ├── firebase_config.py        # Firebase initialization and setup
│   ├── utils.py                  # Utility functions
│   └── serviceAccountKey.json    # Firebase credentials (not in git)
│
├── customers/                     # Customer management module
│   ├── models.py                 # Customer data models
│   ├── views.py                  # Customer CRUD operations
│   └── templates/                # Customer-specific templates
│
├── sales/                         # Sales pipeline module
│   ├── models.py                 # Deal and pipeline models
│   ├── views.py                  # Sales tracking logic
│   ├── pipeline_logic.py         # Pipeline calculations
│   └── templates/                # Sales-specific templates
│
├── analytics/                     # Analytics and reporting
│   ├── views.py                  # Analytics dashboard
│   ├── chart_generator.py        # Matplotlib chart generation
│   └── data_processor.py         # Data analysis functions
│
├── crm_project/                   # Main Django project
│   ├── settings.py               # Django settings
│   ├── urls.py                   # URL routing
│   ├── views.py                  # Main views (dashboard, auth)
│   └── wsgi.py                   # WSGI configuration
│
├── templates/                     # HTML templates
│   ├── base.html                 # Base template with navbar
│   ├── dashboard.html            # Main dashboard
│   ├── customers.html            # Customer list view
│   ├── deals.html                # Sales pipeline view
│   ├── tasks.html                # Task management view
│   └── analytics.html            # Analytics dashboard
│
├── static/                        # Static files
│   ├── css/                      # Stylesheets
│   └── js/                       # JavaScript files
│
├── requirements.txt               # Python dependencies
├── .env                          # Environment variables (not in git)
├── .gitignore                    # Git ignore rules
├── run_firebase_crm.py           # Application launcher
├── check_setup.py                # Setup verification script
└── generate_secret_key.py        # Secret key generator
```

### Key Components

**Firebase Integration (`core/firebase_config.py`):**
- Initializes Firebase Admin SDK
- Provides database connection
- Handles authentication with service account

**Data Layer:**
- Uses Firebase Firestore collections
- Python dictionaries for data structures
- Real-time synchronization

**View Layer:**
- Django class-based and function-based views
- Template rendering with Jinja2
- Form handling and validation

**Analytics Engine:**
- Matplotlib for server-side chart generation
- Chart.js for interactive client-side charts
- Pandas for data aggregation

---

## 🎓 What I Learned

This project was developed as part of my computer science coursework and provided hands-on experience with modern web development technologies and practices.

### Technical Skills Acquired

**Backend Development:**
- Building RESTful APIs with Django and Django REST Framework
- Implementing authentication and authorization systems
- Working with cloud databases (Firebase Firestore)
- Understanding MVC architecture and separation of concerns
- Environment variable management and security best practices

**Frontend Development:**
- Creating responsive web interfaces with Bootstrap 5
- Implementing interactive features with vanilla JavaScript
- Working with modern HTML5 and CSS3 standards
- Integrating client-side charting libraries (Chart.js)

**Database Management:**
- NoSQL database design with Firestore
- Data modeling for business applications
- CRUD operations in a cloud environment
- Real-time data synchronization

**Python Programming:**
- Advanced use of Python data structures (lists, dictionaries, sets)
- Data analysis with Pandas and NumPy
- Visualization with Matplotlib
- Object-oriented programming principles

**Software Engineering:**
- Version control with Git
- Project structure and organization
- Code documentation and commenting
- Error handling and debugging
- Environment configuration management

### Problem-Solving & Design

- **System Design:** Architected a scalable CRM system with modular components
- **Data Flow:** Designed efficient data flow between frontend, backend, and database
- **User Experience:** Created intuitive interfaces for different user roles
- **Performance:** Optimized queries and implemented caching strategies

### Business Understanding

- **CRM Concepts:** Learned about customer lifecycle management, sales pipelines, and business metrics
- **Analytics:** Understanding KPIs and how to present business data effectively
- **User Stories:** Translating business requirements into technical features

### Challenges Overcome

1. **Firebase Integration:** Learning to work with Firebase's document-based structure instead of traditional SQL
2. **Real-time Updates:** Implementing live data synchronization across multiple users
3. **Chart Generation:** Creating both server-side (Matplotlib) and client-side (Chart.js) visualizations
4. **Security:** Implementing proper authentication and protecting sensitive credentials
5. **Deployment:** Understanding production vs development environments

### Future Applications

The skills learned in this project are directly applicable to:
- Building other web applications with Django
- Working with cloud services (Firebase, AWS, Google Cloud)
- Developing data-driven applications
- Creating business intelligence dashboards
- Implementing APIs for mobile or web clients

---

## 📸 Screenshots

*Coming soon - Dashboard, Pipeline View, Analytics*

---

## 🤝 Contributing

This is a school project, but suggestions and feedback are welcome! Feel free to open an issue or contact me.

---

## 📄 License

This project is for educational purposes.

---

## 👤 Author

Created as a school project to demonstrate full-stack web development skills.

---

## 🙏 Acknowledgments

- Django documentation and community
- Firebase documentation
- Bootstrap framework
- Chart.js library
- All open-source contributors

---

<div align="center">

**Built with ❤️ using Django and Firebase**

</div>