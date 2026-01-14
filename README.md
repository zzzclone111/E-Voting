# E_voting system
## Installation
1. **Clone the repository**
```bash
git clone https://github.com/zzzclone111/E-Voting.git
cd E-Voting
```

2. **Set up virtual environment**
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment setup**
```bash
# Create .env file for environment variables
cp .env.production.template .env
# Edit .env with your configuration
```

5. **Database setup**
```bash
python manage.py migrate
python manage.py createsuperuser
```

6. **Run development server**
```bash
python manage.py runserver
```

7. **Access the application**
- Main application: http://127.0.0.1:8000/
- Admin interface: http://127.0.0.1:8000/admin/
