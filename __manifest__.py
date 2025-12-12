{
    'name': 'Hospital Management',
    'version': '18.0.1.0.0',
    'category': 'Healthcare',
    'summary': 'Manage Hospital Patients and Doctors with Workflow',
    'description': """
        Hospital Management System
        ==========================
        This module allows you to manage:
        * Patient Information with auto-generated references
        * Doctor Information with specialties
        * Patient-Doctor Relations
        * Workflow management (New → Waiting → Consultation → Done)
        * Priority management
        * PDF Reports for patients and doctors
    """,
    'author': 'Mohamed Kandil',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'reports/report_template.xml',
        'reports/patient_report.xml',
        'reports/doctor_report.xml',
        'views/patient_views.xml',
        'views/doctor_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hospital_management/static/src/css/style.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3', 
}