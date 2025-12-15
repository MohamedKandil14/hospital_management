from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HospitalPrescription(models.Model):
    """Model for managing medical prescriptions"""
    
    _name = 'hospital.prescription'
    _description = 'Medical Prescription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference'
    _order = 'prescription_date desc'
    
    # Basic Fields
    reference = fields.Char(
        string='Prescription Reference',
        required=True,
        readonly=True,
        copy=False,
        default='New'
    )
    
    patient_id = fields.Many2one(
        comodel_name='hospital.patient',
        string='Patient',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    doctor_id = fields.Many2one(
        comodel_name='hospital.doctor',
        string='Doctor',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    
    appointment_id = fields.Many2one(
        comodel_name='hospital.appointment',
        string='Related Appointment',
        ondelete='set null'
    )
    
    medical_record_id = fields.Many2one(
        comodel_name='hospital.medical.record',
        string='Medical Record',
        ondelete='set null'
    )
    
    # Prescription Information
    prescription_date = fields.Date(
        string='Prescription Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    diagnosis = fields.Text(
        string='Diagnosis',
        required=True,
        tracking=True
    )
    
    # Medicine Lines
    medicine_line_ids = fields.One2many(
        comodel_name='hospital.prescription.line',
        inverse_name='prescription_id',
        string='Medicines',
        copy=True
    )
    
    medicine_count = fields.Integer(
        string='Medicines Count',
        compute='_compute_medicine_count'
    )
    
    # Instructions
    general_instructions = fields.Text(
        string='General Instructions',
        help='General instructions for the patient'
    )
    
    dietary_advice = fields.Text(
        string='Dietary Advice',
        help='Dietary recommendations'
    )
    
    precautions = fields.Text(
        string='Precautions',
        help='Safety precautions and warnings'
    )
    
    follow_up_date = fields.Date(
        string='Follow-up Date',
        help='Next appointment date'
    )
    
    # Related Fields
    patient_name = fields.Char(
        related='patient_id.name',
        string='Patient Name',
        readonly=True
    )
    
    patient_age = fields.Integer(
        related='patient_id.age',
        string='Patient Age',
        readonly=True
    )
    
    patient_gender = fields.Selection(
        related='patient_id.gender',
        string='Patient Gender',
        readonly=True
    )
    
    doctor_name = fields.Char(
        related='doctor_id.name',
        string='Doctor Name',
        readonly=True
    )
    
    doctor_specialty = fields.Selection(
        related='doctor_id.specialty',
        string='Doctor Specialty',
        readonly=True
    )
    
    # Status
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('dispensed', 'Dispensed'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        tracking=True
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    notes = fields.Text(
        string='Additional Notes'
    )
    
    # ==========================================
    # Computed Fields
    # ==========================================
    
    @api.depends('medicine_line_ids')
    def _compute_medicine_count(self):
        """Compute total number of medicines"""
        for record in self:
            record.medicine_count = len(record.medicine_line_ids)
    
    # ==========================================
    # Onchange Methods
    # ==========================================
    
    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        """Auto-fill doctor when patient is selected"""
        if self.patient_id and self.patient_id.doctor_id:
            self.doctor_id = self.patient_id.doctor_id
    
    @api.onchange('appointment_id')
    def _onchange_appointment_id(self):
        """Auto-fill from appointment"""
        if self.appointment_id:
            self.patient_id = self.appointment_id.patient_id
            self.doctor_id = self.appointment_id.doctor_id
            if self.appointment_id.diagnosis:
                self.diagnosis = self.appointment_id.diagnosis
    
    @api.onchange('medical_record_id')
    def _onchange_medical_record_id(self):
        """Auto-fill from medical record"""
        if self.medical_record_id:
            self.patient_id = self.medical_record_id.patient_id
            self.doctor_id = self.medical_record_id.doctor_id
            if self.medical_record_id.diagnosis:
                self.diagnosis = self.medical_record_id.diagnosis
    
    # ==========================================
    # Constraints
    # ==========================================
    
    @api.constrains('medicine_line_ids')
    def _check_medicine_lines(self):
        """Ensure at least one medicine is prescribed"""
        for record in self:
            if record.state == 'confirmed' and not record.medicine_line_ids:
                raise ValidationError(
                    'Please add at least one medicine to the prescription!'
                )
    
    # ==========================================
    # CRUD Override
    # ==========================================
    
    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence number for reference"""
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'hospital.prescription'
                ) or 'New'
        return super().create(vals_list)
    
    # ==========================================
    # Action Methods
    # ==========================================
    
    def action_confirm(self):
        """Confirm prescription"""
        for record in self:
            if record.state == 'draft':
                if not record.medicine_line_ids:
                    raise ValidationError('Please add at least one medicine!')
                record.state = 'confirmed'
                record.message_post(body='Prescription confirmed.')
    
    def action_dispense(self):
        """Mark prescription as dispensed"""
        for record in self:
            if record.state == 'confirmed':
                record.state = 'dispensed'
                record.message_post(body='Medicines dispensed to patient.')
    
    def action_complete(self):
        """Mark prescription as completed"""
        for record in self:
            if record.state == 'dispensed':
                record.state = 'completed'
                record.message_post(body='Prescription treatment completed.')
    
    def action_cancel(self):
        """Cancel prescription"""
        for record in self:
            if record.state in ['draft', 'confirmed']:
                record.state = 'cancelled'
                record.message_post(body='Prescription cancelled.')
    
    def action_reset_to_draft(self):
        """Reset to draft"""
        for record in self:
            record.state = 'draft'
            record.message_post(body='Reset to draft.')
    
    def action_print_prescription(self):
        """Print prescription report"""
        self.ensure_one()
        return self.env.ref('hospital_management.action_report_prescription').report_action(self)


class HospitalPrescriptionLine(models.Model):
    """Model for prescription medicine lines"""
    
    _name = 'hospital.prescription.line'
    _description = 'Prescription Medicine Line'
    _order = 'sequence, id'
    
    prescription_id = fields.Many2one(
        comodel_name='hospital.prescription',
        string='Prescription',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    medicine_name = fields.Char(
        string='Medicine Name',
        required=True
    )
    
    medicine_type = fields.Selection(
        selection=[
            ('tablet', 'Tablet'),
            ('capsule', 'Capsule'),
            ('syrup', 'Syrup'),
            ('injection', 'Injection'),
            ('cream', 'Cream/Ointment'),
            ('drops', 'Drops'),
            ('inhaler', 'Inhaler'),
            ('other', 'Other'),
        ],
        string='Type',
        required=True,
        default='tablet'
    )
    
    dosage = fields.Char(
        string='Dosage',
        required=True,
        help='e.g., 500mg, 10ml, 1 puff'
    )
    
    frequency = fields.Selection(
        selection=[
            ('once_daily', 'Once Daily'),
            ('twice_daily', 'Twice Daily'),
            ('three_times', 'Three Times Daily'),
            ('four_times', 'Four Times Daily'),
            ('every_4_hours', 'Every 4 Hours'),
            ('every_6_hours', 'Every 6 Hours'),
            ('every_8_hours', 'Every 8 Hours'),
            ('every_12_hours', 'Every 12 Hours'),
            ('as_needed', 'As Needed'),
            ('before_meals', 'Before Meals'),
            ('after_meals', 'After Meals'),
            ('at_bedtime', 'At Bedtime'),
        ],
        string='Frequency',
        required=True,
        default='twice_daily'
    )
    
    duration_number = fields.Integer(
        string='Duration',
        default=7,
        help='Number of days/weeks'
    )
    
    duration_unit = fields.Selection(
        selection=[
            ('days', 'Days'),
            ('weeks', 'Weeks'),
            ('months', 'Months'),
        ],
        string='Unit',
        default='days'
    )
    
    quantity = fields.Integer(
        string='Quantity',
        default=1,
        help='Number of units to dispense'
    )
    
    timing = fields.Selection(
        selection=[
            ('before_food', 'Before Food'),
            ('after_food', 'After Food'),
            ('with_food', 'With Food'),
            ('empty_stomach', 'Empty Stomach'),
            ('anytime', 'Anytime'),
        ],
        string='Timing',
        default='after_food'
    )
    
    instructions = fields.Text(
        string='Special Instructions',
        help='Specific instructions for this medicine'
    )
    
    notes = fields.Text(
        string='Notes'
    )
    
    @api.constrains('duration_number', 'quantity')
    def _check_positive_values(self):
        """Ensure duration and quantity are positive"""
        for line in self:
            if line.duration_number <= 0:
                raise ValidationError('Duration must be greater than zero!')
            if line.quantity <= 0:
                raise ValidationError('Quantity must be greater than zero!')