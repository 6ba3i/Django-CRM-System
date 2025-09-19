# Django CRM System

A comprehensive Customer Relationship Management (CRM) system built with Django and Firebase, featuring customer management, sales pipeline tracking, and analytics dashboard.

## Features

### 🏢 Customer Management
- Complete customer profiles with contact information
- Customer interaction tracking
- Customer segmentation and tagging
- Import/export customer data

### 💰 Sales Pipeline
- Deal management and tracking
- Sales stage progression
- Pipeline visualization
- Sales forecasting
- Revenue analytics

### 📊 Analytics Dashboard
- Real-time sales metrics
- Customer behavior analysis
- Revenue reporting
- Performance charts and graphs
- Data export capabilities

### 🔧 Core Features
- Firebase integration for cloud data storage
- Bootstrap 5 responsive UI
- User authentication and permissions
- RESTful API endpoints
- Advanced search and filtering

## Tech Stack

- **Backend**: Django 4.2.0
- **Database**: SQLite (local) + Firebase Firestore (cloud)
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Authentication**: Django built-in auth
- **Charts**: Chart.js, Matplotlib
- **API**: Django REST Framework

## Project Structure

```
crm_project/
├── crm_project/            # Main project settings
├── customers/              # Customer management app
│   ├── models.py          # Customer and Interaction models
│   ├── views.py           # Customer views and API endpoints
│   ├── forms.py           # Customer forms
│   └── urls.py            # Customer URL patterns
├── sales/                  # Sales management app
│   ├── models.py          # Deal and Pipeline models
│   ├── views.py           # Sales views and pipeline logic
│   ├── pipeline_logic.py  # Sales pipeline business logic
│   └── urls.py            # Sales URL patterns
├── analytics/              # Analytics and reporting app
│   ├── views.py           # Analytics dashboard views
│   ├── chart_generator.py # Chart generation utilities
│   └── data_processor.py  # Data processing functions
├── core/                   # Core utilities and configurations
│   ├── firebase_config.py # Firebase setup and configuration
│   ├── utils.py           # Utility functions
│   ├── decorators.py      # Custom decorators
│   └── serviceAccountKey.json # Firebase credentials (not in git)
├── templates/              # HTML templates
│   ├── base.html          # Base template
│   ├── dashboard.html     # Main dashboard
│   └── [app_templates]/   # App-specific templates
├── static/                 # Static files
│   ├── css/main.css       # Custom styles
│   └── js/main.js         # Custom JavaScript
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (not in git)
└── manage.py              # Django management script
```

## Installation

### Prerequisites
- Python 3.8+
- pip
- Git
- Firebase project (for cloud features)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd crm_project
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup**
   
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   FIREBASE_CREDENTIALS_PATH=core/serviceAccountKey.json
   FIREBASE_DATABASE_URL=https://your-project-id.firebaseio.com
   ```

5. **Firebase configuration**
   
   - Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
   - Generate a service account key
   - Save it as `core/serviceAccountKey.json`
   - Update your `.env` file with the correct Firebase URL

6. **Database setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Open your browser to `http://127.0.0.1:8000`
   - Admin panel: `http://127.0.0.1:8000/admin`

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Django Settings
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=core/serviceAccountKey.json
FIREBASE_DATABASE_URL=https://your-project-id.firebaseio.com

# Database (optional for production)
DATABASE_URL=your-database-url
```

### Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Enable Firestore Database
4. Generate service account credentials
5. Download the JSON file and save it as `core/serviceAccountKey.json`

## Usage

### Dashboard
- Access the main dashboard at `/dashboard/`
- View key metrics, recent activities, and quick actions

### Customer Management
- Add new customers at `/customers/create/`
- View customer list at `/customers/`
- Track customer interactions and history

### Sales Pipeline
- Manage deals at `/sales/deals/`
- View pipeline visualization at `/sales/pipeline/`
- Track deal progression through sales stages

### Analytics
- View comprehensive analytics at `/analytics/`
- Generate reports and export data
- Monitor sales performance and trends

## API Endpoints

The system provides RESTful API endpoints for integration:

- `GET /api/customers/` - List customers
- `GET /api/deals/` - List deals
- `GET /api/forecast/` - Sales forecast data
- `POST /api/customers/` - Create customer
- `PUT /api/deals/<id>/` - Update deal

## Development

### Adding New Features

1. Create new Django apps for major feature sets
2. Add models in `models.py`
3. Create forms in `forms.py`
4. Implement views in `views.py`
5. Add URL patterns in `urls.py`
6. Create templates in the `templates/` directory

### Code Style

- Follow PEP 8 guidelines
- Use Django best practices
- Add docstrings to functions and classes
- Write unit tests for new features

### Testing

```bash
python manage.py test
```

## Deployment

### Production Checklist

1. Set `DEBUG=False` in production
2. Configure production database
3. Set up static file serving
4. Configure proper `ALLOWED_HOSTS`
5. Use environment variables for sensitive data
6. Set up proper logging
7. Configure Firebase security rules

### Deployment Options

- **Heroku**: Use `gunicorn` and `whitenoise`
- **AWS**: Use Elastic Beanstalk or EC2
- **DigitalOcean**: App Platform or Droplets
- **Google Cloud**: App Engine or Compute Engine

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## Dependencies

### Main Dependencies
- Django 4.2.0 - Web framework
- firebase-admin 6.1.0 - Firebase integration
- djangorestframework 3.14.0 - API framework
- django-cors-headers 4.0.0 - CORS handling
- python-decouple 3.8 - Environment variables

### Data & Analytics
- pandas 2.0.2 - Data manipulation
- numpy 1.24.3 - Numerical computing
- matplotlib 3.7.1 - Chart generation

### Deployment
- gunicorn 20.1.0 - WSGI server
- whitenoise 6.4.0 - Static file serving

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the code comments

## Changelog

### v1.0.0
- Initial release
- Customer management system
- Sales pipeline tracking
- Analytics dashboard
- Firebase integration
- Bootstrap 5 UI