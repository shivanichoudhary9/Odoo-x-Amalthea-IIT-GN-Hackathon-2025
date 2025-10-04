# ExpenseFlow 💰

**Your automated solution for multi-level expense approvals.**

ExpenseFlow is a comprehensive expense management system built with Flask and PostgreSQL, designed to streamline expense reporting and approval workflows for companies of all sizes.

## 🌟 Features

### Core Functionality
- **Multi-role Authentication**: Admin, Manager, and Employee roles
- **Expense Submission**: Easy-to-use expense reporting interface
- **Multi-level Approval Workflows**: Configurable approval chains
- **Real-time Status Tracking**: Monitor expense approval progress
- **Company Management**: Multi-tenant architecture with company-specific settings
- **Currency Support**: Automatic currency detection based on country

### User Roles
- **👑 Admin**: Full system control, user management, approval rule configuration
- **👔 Manager**: Approve expenses, manage team members, view reports
- **👤 Employee**: Submit expenses, track approval status, view personal history

### Technical Features
- **RESTful API**: Clean API endpoints for all operations
- **JWT Authentication**: Secure token-based authentication
- **Database Migrations**: Alembic-powered database versioning
- **Responsive UI**: Modern, mobile-friendly interface with Tailwind CSS
- **External API Integration**: Automatic currency detection via REST Countries API

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Odoo-x-Amalthea-IIT-GN-Hackathon-2025
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv vir
   # On Windows
   vir\Scripts\activate
   # On macOS/Linux
   source vir/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   Edit `.env` with your configuration:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/expenseflow
   JWT_SECRET_KEY=your-secret-key-here
   FLASK_ENV=development
   FLASK_DEBUG=True
   ```

5. **Set up the database**
   ```bash
   # Create database migrations
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - Start with the landing page at `frontend/landingPage.html`

## 📁 Project Structure

```
├── app/                    # Flask application
│   ├── __init__.py        # App factory
│   ├── models.py          # Database models
│   └── routes.py          # API endpoints
├── frontend/              # HTML templates
│   ├── landingPage.html   # Welcome page
│   ├── login.html         # User login
│   ├── signup.html        # User registration
│   ├── admin.html         # Admin dashboard
│   ├── manager.html       # Manager dashboard
│   └── employee.html      # Employee dashboard
├── migrations/            # Database migrations
├── config.py              # Configuration settings
├── run.py                 # Application entry point
├── env.example            # Environment variables template
└── README.md              # This file
```

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login

### Companies
- `GET /api/companies` - List companies
- `POST /api/companies` - Create company

### Users
- `GET /api/users` - List users (Admin only)
- `POST /api/users` - Create user (Admin only)
- `GET /api/users/me` - Get current user profile

### Expenses
- `GET /api/expenses` - List expenses
- `POST /api/expenses` - Create expense
- `PUT /api/expenses/<id>` - Update expense
- `DELETE /api/expenses/<id>` - Delete expense

### Approval Rules
- `GET /api/approval-rules` - List approval rules
- `POST /api/approval-rules` - Create approval rule
- `PUT /api/approval-rules/<id>` - Update approval rule

### Approvals
- `GET /api/approvals` - List pending approvals
- `POST /api/approvals/<id>/approve` - Approve expense
- `POST /api/approvals/<id>/reject` - Reject expense

## 🗄️ Database Schema

### Core Tables
- **companies**: Company information and settings
- **users**: User accounts with role-based access
- **expenses**: Individual expense claims
- **approval_rules**: Configurable approval workflows
- **approval_steps**: Steps within approval workflows
- **expense_approvals**: Approval tracking and history

## 🎨 Frontend

The frontend is built with modern HTML5, CSS3, and JavaScript, using Tailwind CSS for styling. It provides:

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Role-based Dashboards**: Different interfaces for each user role
- **Real-time Updates**: Dynamic content updates without page refresh
- **Form Validation**: Client-side and server-side validation
- **Modern UI/UX**: Clean, professional interface

## 🔐 Security Features

- **Password Hashing**: bcrypt for secure password storage
- **JWT Tokens**: Secure authentication tokens
- **Role-based Access Control**: Granular permissions
- **Input Validation**: Protection against common attacks
- **Environment Variables**: Sensitive data protection

## 🌍 Internationalization

- **Multi-currency Support**: Automatic currency detection
- **Country-based Configuration**: Currency mapping via REST Countries API
- **Flexible Localization**: Ready for multiple language support

## 🚀 Deployment

### Production Setup
1. Set `FLASK_ENV=production` in your environment
2. Use a production WSGI server (e.g., Gunicorn)
3. Set up a reverse proxy (e.g., Nginx)
4. Configure SSL certificates
5. Set up database backups

### Environment Variables
```env
DATABASE_URL=postgresql://user:pass@host:port/db
JWT_SECRET_KEY=your-production-secret-key
FLASK_ENV=production
FLASK_DEBUG=False
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🏆 Hackathon Project

This project was developed for the **Odoo x Amalthea IIT-GN Hackathon 2025**, showcasing modern web development practices and innovative expense management solutions.

---

**Built with ❤️ using Flask, PostgreSQL, and modern web technologies.**
