from odoo import models, fields, api


class HospitalDoctor(models.Model):
    """Model for managing hospital doctors"""
    
    _name = 'hospital.doctor'
    _description = 'Hospital Doctor'
    _rec_name = 'name'
    _order = 'name'
    
    # Basic Fields
    name = fields.Char(
        string='Doctor Name',
        required=True,
        help='Full name of the doctor'
    )
    
    specialty = fields.Selection(
        selection=[
            ('cardiology', 'Cardiology'),
            ('pediatrics', 'Pediatrics'),
            ('neurology', 'Neurology'),
            ('orthopedics', 'Orthopedics'),
            ('general', 'General Medicine'),
            ('pediatric', 'Pediatrics'),
        ],
        string='Specialty',
        default='general',
        help='Medical specialty'
    )
    
    phone = fields.Char(
        string='Phone Number'
    )
    
    email = fields.Char(
        string='Email'
    )
    
    # New Fields
    consultation_fee = fields.Float(
        string='Consultation Fee',
        default=100.0,
        help='Fee per consultation'
    )
    
    max_patients = fields.Integer(
        string='Max Patients',
        default=50,
        help='Maximum number of patients'
    )
    
    availability = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('busy', 'Busy'),
            ('on_leave', 'On Leave'),
        ],
        string='Availability',
        compute='_compute_availability',
        store=True
    )
    
    # Relation with Patients (One2many)
    patient_ids = fields.One2many(
        comodel_name='hospital.patient',
        inverse_name='doctor_id',
        string='Patients',
        help='List of patients assigned to this doctor'
    )
    
    # Relation with Appointments (One2many)
    appointment_ids = fields.One2many(
        comodel_name='hospital.appointment',
        inverse_name='doctor_id',
        string='Appointments'
    )
    
    appointment_count = fields.Integer(
        string='Appointments',
        compute='_compute_appointment_count'
    )
    
    # Computed Field
    patient_count = fields.Integer(
        string='Number of Patients',
        compute='_compute_patient_count',
        store=True
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    @api.depends('patient_ids')
    def _compute_patient_count(self):
        """Compute total number of patients"""
        for record in self:
            record.patient_count = len(record.patient_ids)
    
    @api.depends('appointment_ids')
    def _compute_appointment_count(self):
        """Compute total number of appointments"""
        for record in self:
            record.appointment_count = len(record.appointment_ids)
    
    @api.depends('patient_count', 'max_patients')
    def _compute_availability(self):
        """Compute doctor availability based on patient count"""
        for record in self:
            if record.patient_count >= record.max_patients:
                record.availability = 'busy'
            elif record.patient_count > 0:
                record.availability = 'available'
            else:
                record.availability = 'available'
    
    # Onchange: Warning when max patients exceeded
    @api.onchange('patient_count')
    def _onchange_patient_count(self):
        """Show warning when max patients reached"""
        if self.patient_count >= self.max_patients:
            return {
                'warning': {
                    'title': 'Maximum Patients Reached',
                    'message': f'Doctor {self.name} has reached maximum patient capacity ({self.max_patients} patients).'
                }
            }
    
    # Constraint to prevent exceeding max patients
    @api.constrains('patient_ids', 'max_patients')
    def _check_max_patients(self):
        """Ensure doctor doesn't exceed max patients"""
        for record in self:
            if len(record.patient_ids) > record.max_patients:
                from odoo.exceptions import ValidationError
                raise ValidationError(
                    f'Doctor {record.name} cannot have more than {record.max_patients} patients!'
                )