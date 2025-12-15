{
    'name': 'Hospital Management',
    'version': '18.0.1.0.0',
    'category': 'Healthcare',
    'summary': 'Complete Hospital Management System with Analytics Dashboard',
    'description': """
        Hospital Management System
        ==========================
        * Patient & Doctor Management
        * Appointment Scheduling with Calendar
        * Medical Records with File Attachments
        * Billing and Invoicing System
        * Prescription Management
        * Laboratory Test Integration
        * Analytics Dashboard with Charts
        * Multi-Language Support (Arabic & English)
        * Custom Theme & Styling
        * Email Notifications (Confirmation, Reminders, Welcome)
        * Automated Daily Reminders
        * Workflow Automation
        * PDF Reports
    """,
    'author': 'Mohamed Kandil',
    'website': 'https://github.com/MohamedKandil14/hospital_management',
    'depends': ['base', 'web', 'calendar', 'mail'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Data
        'data/sequence.xml',
        'data/email_templates.xml',
        'data/scheduled_actions.xml',
        
        # Reports
        'reports/report_template.xml',
        'reports/patient_report.xml',
        'reports/doctor_report.xml',
        
        # Views - IMPORTANT: patient_views.xml must be first (contains root menu)
        'views/patient_views.xml',  # Root menu is here
        'views/doctor_views.xml',
        'views/appointment_views.xml',
        'views/medical_record_views.xml',
        'views/billing_views.xml',
        'views/prescription_views.xml',
        'views/lab_test_views.xml',
        'views/dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # CSS Files
            'hospital_management/static/src/css/style.css',
            'hospital_management/static/src/css/custom_theme.css',
            
            # SCSS Files (optional - will be compiled to CSS)
            # 'hospital_management/static/src/scss/custom_theme.scss',
        ],
        'web.assets_frontend': [
            # Frontend assets (if needed for patient portal)
            'hospital_management/static/src/css/custom_theme.css',
        ],
    },
    'images': [
        'static/description/icon.png',
        'static/src/img/logo.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}