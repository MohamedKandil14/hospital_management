from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MedicalRecord(models.Model):
    """Model for managing patient medical records"""
    
    _name = 'hospital.medical.record'
    _description = 'Medical Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference'
    _order = 'record_date desc'
    
    # Basic Fields
    reference = fields.Char(
        string='Reference',
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
    
    # Record Details
    record_date = fields.Date(
        string='Record Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    record_type = fields.Selection(
        selection=[
            ('consultation', 'Consultation'),
            ('lab_test', 'Lab Test'),
            ('xray', 'X-Ray'),
            ('scan', 'CT/MRI Scan'),
            ('prescription', 'Prescription'),
            ('surgery', 'Surgery'),
            ('follow_up', 'Follow-up'),
            ('other', 'Other'),
        ],
        string='Record Type',
        required=True,
        default='consultation',
        tracking=True
    )
    
    # Medical Information
    diagnosis = fields.Text(
        string='Diagnosis',
        tracking=True
    )
    
    symptoms = fields.Text(
        string='Symptoms'
    )
    
    treatment = fields.Text(
        string='Treatment / Prescription',
        tracking=True
    )
    
    notes = fields.Text(
        string='Additional Notes'
    )
    
    # Vital Signs
    blood_pressure = fields.Char(
        string='Blood Pressure',
        help='e.g., 120/80'
    )
    
    temperature = fields.Float(
        string='Temperature (°C)'
    )
    
    pulse = fields.Integer(
        string='Pulse Rate (bpm)'
    )
    
    weight = fields.Float(
        string='Weight (kg)'
    )
    
    height = fields.Float(
        string='Height (cm)'
    )
    
    # Attachments
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='medical_record_attachment_rel',
        column1='record_id',
        column2='attachment_id',
        string='Attachments',
        help='Lab results, X-rays, scans, reports, etc.'
    )
    
    attachment_count = fields.Integer(
        string='Attachments',
        compute='_compute_attachment_count'
    )
    
    # Related Fields
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
    
    # Status
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('archived', 'Archived'),
        ],
        string='Status',
        default='draft',
        tracking=True
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Computed Fields
    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        """Compute number of attachments"""
        for record in self:
            record.attachment_count = len(record.attachment_ids)
    
    # CRUD Override
    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence number for reference"""
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'hospital.medical.record'
                ) or 'New'
        return super().create(vals_list)
    
    # Actions
    def action_confirm(self):
        """Confirm medical record"""
        for record in self:
            if record.state == 'draft':
                record.state = 'confirmed'
                record.message_post(body='Medical record confirmed.')
    
    def action_archive_record(self):
        """Archive medical record"""
        for record in self:
            if record.state == 'confirmed':
                record.state = 'archived'
                record.message_post(body='Medical record archived.')
    
    def action_reset_to_draft(self):
        """Reset to draft"""
        for record in self:
            record.state = 'draft'
            record.message_post(body='Reset to draft.')
    
    def action_view_attachments(self):
        """Open attachments view"""
        self.ensure_one()
        return {
            'name': 'Attachments',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', self.attachment_ids.ids)],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            }
        }