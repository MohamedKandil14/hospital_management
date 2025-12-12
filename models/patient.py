from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta


class HospitalPatient(models.Model):
    """Model for managing hospital patients"""
    
    _name = 'hospital.patient'
    _description = 'Hospital Patient'
    _rec_name = 'name'
    _order = 'name'
    
    # Basic Fields
    name = fields.Char(
        string='Patient Name',
        required=True,
        help='Full name of the patient'
    )
    
    age = fields.Integer(
        string='Age',
        readonly=True,
        help='Automatically calculated from date of birth'
    )
    
    gender = fields.Selection(
        selection=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')
        ],
        string='Gender',
        default='male'  # قيمة افتراضية
    )
    
    date_of_birth = fields.Date(
        string='Date of Birth'
    )
    
    # Relation with Doctor (Many2one)
    doctor_id = fields.Many2one(
        comodel_name='hospital.doctor',
        string='Doctor',
        help='Assigned doctor for this patient'
    )
    
    # New Fields
    reference = fields.Char(
        string='Reference',
        readonly=True,
        copy=False,
        default=lambda self: self._get_default_reference()
    )
    
    admission_date = fields.Date(
        string='Admission Date',
        default=fields.Date.today  # تاريخ اليوم تلقائياً
    )
    
    # Computed Field
    is_child = fields.Boolean(
        string='Is Child?',
        compute='_compute_is_child',
        store=True,
        help='Automatically determined if age is less than 18'
    )
    
    # Additional Fields
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    notes = fields.Text(
        string='Notes'
    )
    
    # Workflow Fields
    state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('waiting', 'Waiting'),
            ('consultation', 'In Consultation'),
            ('done', 'Done'),
            ('cancel', 'Cancelled')
        ],
        string='Status',
        default='new',
        required=True,
        tracking=True,
        help='Current state of the patient'
    )
    
    # Priority
    priority = fields.Selection(
        selection=[
            ('0', 'Normal'),
            ('1', 'Low'),
            ('2', 'High'),
            ('3', 'Very High'),
        ],
        string='Priority',
        default='0'
    )
    
    # Default Reference
    def _get_default_reference(self):
        """Generate default reference number"""
        return 'New'
    
    # Onchange: Calculate age from date of birth
    @api.onchange('date_of_birth')
    def _onchange_date_of_birth(self):
        """Calculate age automatically when date of birth changes"""
        if self.date_of_birth:
            today = date.today()
            dob = self.date_of_birth
            
            # حساب العمر بالسنوات
            age = relativedelta(today, dob).years
            self.age = age
        else:
            self.age = 0
    
    # Onchange: Suggest doctor based on age
    @api.onchange('age')
    def _onchange_age(self):
        """Suggest doctor based on patient age"""
        if self.age and self.age < 18:
            # ابحث عن دكتور أطفال
            pediatric_doctor = self.env['hospital.doctor'].search([
                ('specialty', 'ilike', 'pediatric')
            ], limit=1)
            
            if pediatric_doctor:
                self.doctor_id = pediatric_doctor.id
    
    @api.depends('age')
    def _compute_is_child(self):
        """Compute if patient is a child based on age"""
        for record in self:
            if record.age:
                record.is_child = record.age < 18
            else:
                record.is_child = False
    
    # ==========================================
    # Workflow Actions
    # ==========================================
    
    def action_waiting(self):
        """Move patient to waiting state"""
        for record in self:
            if record.state == 'new':
                record.state = 'waiting'
    
    def action_consultation(self):
        """Move patient to consultation state"""
        for record in self:
            if record.state == 'waiting':
                record.state = 'consultation'
    
    def action_done(self):
        """Move patient to done state"""
        for record in self:
            if record.state == 'consultation':
                record.state = 'done'
    
    def action_cancel(self):
        """Cancel patient appointment"""
        for record in self:
            if record.state in ['new', 'waiting', 'consultation']:
                record.state = 'cancel'
    
    def action_reset_to_new(self):
        """Reset patient to new state"""
        for record in self:
            record.state = 'new'
    
    # Override create to generate reference
    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence number for reference"""
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'hospital.patient'
                ) or 'New'
        return super().create(vals_list)