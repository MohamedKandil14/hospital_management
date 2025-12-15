from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HospitalLabTest(models.Model):
    """Model for managing laboratory tests"""
    
    _name = 'hospital.lab.test'
    _description = 'Laboratory Test'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference'
    _order = 'test_date desc'
    
    # Basic Fields
    reference = fields.Char(
        string='Test Reference',
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
        string='Requested By',
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
    
    # Test Information
    test_date = fields.Date(
        string='Test Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    test_type = fields.Many2one(
        comodel_name='hospital.lab.test.type',
        string='Test Type',
        required=True,
        tracking=True
    )
    
    test_category = fields.Selection(
        related='test_type.category',
        string='Category',
        readonly=True,
        store=True
    )
    
    # Test Results
    result_date = fields.Date(
        string='Result Date',
        tracking=True
    )
    
    line_ids = fields.One2many(
        comodel_name='hospital.lab.test.line',
        inverse_name='test_id',
        string='Test Parameters',
        copy=True
    )
    
    result_summary = fields.Text(
        string='Result Summary',
        tracking=True
    )
    
    lab_technician = fields.Char(
        string='Lab Technician',
        help='Name of lab technician who performed the test'
    )
    
    # Attachments
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='lab_test_attachment_rel',
        column1='test_id',
        column2='attachment_id',
        string='Attachments',
        help='Lab test reports, scans, images'
    )
    
    attachment_count = fields.Integer(
        string='Attachments',
        compute='_compute_attachment_count'
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
    
    test_name = fields.Char(
        related='test_type.name',
        string='Test Name',
        readonly=True
    )
    
    # Status
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('requested', 'Requested'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        tracking=True
    )
    
    result_status = fields.Selection(
        selection=[
            ('normal', 'Normal'),
            ('abnormal', 'Abnormal'),
            ('critical', 'Critical'),
        ],
        string='Result Status',
        tracking=True
    )
    
    priority = fields.Selection(
        selection=[
            ('routine', 'Routine'),
            ('urgent', 'Urgent'),
            ('stat', 'STAT'),
        ],
        string='Priority',
        default='routine',
        tracking=True
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    notes = fields.Text(
        string='Notes'
    )
    
    # ==========================================
    # Computed Fields
    # ==========================================
    
    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        """Compute number of attachments"""
        for record in self:
            record.attachment_count = len(record.attachment_ids)
    
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
    
    @api.onchange('test_type')
    def _onchange_test_type(self):
        """Auto-create test lines based on test type"""
        if self.test_type and self.test_type.parameter_ids:
            lines = []
            for param in self.test_type.parameter_ids:
                lines.append((0, 0, {
                    'parameter_name': param.name,
                    'unit': param.unit,
                    'normal_range': param.normal_range,
                    'sequence': param.sequence,
                }))
            self.line_ids = lines
    
    # ==========================================
    # Constraints
    # ==========================================
    
    @api.constrains('result_date', 'test_date')
    def _check_result_date(self):
        """Ensure result date is not before test date"""
        for record in self:
            if record.result_date and record.test_date:
                if record.result_date < record.test_date:
                    raise ValidationError(
                        'Result date cannot be before test date!'
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
                    'hospital.lab.test'
                ) or 'New'
        return super().create(vals_list)
    
    # ==========================================
    # Action Methods
    # ==========================================
    
    def action_request(self):
        """Request lab test"""
        for record in self:
            if record.state == 'draft':
                record.state = 'requested'
                record.message_post(body='Lab test requested.')
    
    def action_start_test(self):
        """Start processing test"""
        for record in self:
            if record.state == 'requested':
                record.state = 'in_progress'
                record.message_post(body='Test processing started.')
    
    def action_complete(self):
        """Complete lab test"""
        for record in self:
            if record.state == 'in_progress':
                if not record.result_date:
                    record.result_date = fields.Date.today()
                record.state = 'completed'
                record.message_post(body='Test completed.')
                
                # Auto-determine result status based on line results
                record._compute_result_status()
    
    def action_cancel(self):
        """Cancel lab test"""
        for record in self:
            if record.state in ['draft', 'requested']:
                record.state = 'cancelled'
                record.message_post(body='Test cancelled.')
    
    def action_reset_to_draft(self):
        """Reset to draft"""
        for record in self:
            record.state = 'draft'
            record.message_post(body='Reset to draft.')
    
    def action_view_attachments(self):
        """Open attachments view"""
        self.ensure_one()
        return {
            'name': 'Test Attachments',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', self.attachment_ids.ids)],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            }
        }
    
    def _compute_result_status(self):
        """Automatically determine result status based on test lines"""
        for record in self:
            if not record.line_ids:
                continue
            
            has_abnormal = any(line.is_abnormal for line in record.line_ids)
            has_critical = any(line.is_critical for line in record.line_ids)
            
            if has_critical:
                record.result_status = 'critical'
            elif has_abnormal:
                record.result_status = 'abnormal'
            else:
                record.result_status = 'normal'


class HospitalLabTestLine(models.Model):
    """Model for lab test result lines"""
    
    _name = 'hospital.lab.test.line'
    _description = 'Lab Test Result Line'
    _order = 'sequence, id'
    
    test_id = fields.Many2one(
        comodel_name='hospital.lab.test',
        string='Lab Test',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    parameter_name = fields.Char(
        string='Parameter',
        required=True
    )
    
    result_value = fields.Char(
        string='Result',
        tracking=True
    )
    
    unit = fields.Char(
        string='Unit'
    )
    
    normal_range = fields.Char(
        string='Normal Range',
        help='e.g., 80-120, <5.7, >100'
    )
    
    is_abnormal = fields.Boolean(
        string='Abnormal',
        default=False
    )
    
    is_critical = fields.Boolean(
        string='Critical',
        default=False
    )
    
    notes = fields.Text(
        string='Notes'
    )


class HospitalLabTestType(models.Model):
    """Model for lab test types/templates"""
    
    _name = 'hospital.lab.test.type'
    _description = 'Lab Test Type'
    _order = 'name'
    
    name = fields.Char(
        string='Test Name',
        required=True
    )
    
    code = fields.Char(
        string='Test Code',
        required=True
    )
    
    category = fields.Selection(
        selection=[
            ('hematology', 'Hematology'),
            ('biochemistry', 'Biochemistry'),
            ('microbiology', 'Microbiology'),
            ('serology', 'Serology'),
            ('urine', 'Urine Analysis'),
            ('hormone', 'Hormone'),
            ('immunology', 'Immunology'),
            ('pathology', 'Pathology'),
            ('radiology', 'Radiology'),
            ('other', 'Other'),
        ],
        string='Category',
        required=True,
        default='biochemistry'
    )
    
    description = fields.Text(
        string='Description'
    )
    
    cost = fields.Float(
        string='Test Cost',
        default=0.0
    )
    
    parameter_ids = fields.One2many(
        comodel_name='hospital.lab.test.parameter',
        inverse_name='test_type_id',
        string='Parameters'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )


class HospitalLabTestParameter(models.Model):
    """Model for lab test parameters/components"""
    
    _name = 'hospital.lab.test.parameter'
    _description = 'Lab Test Parameter'
    _order = 'sequence, name'
    
    test_type_id = fields.Many2one(
        comodel_name='hospital.lab.test.type',
        string='Test Type',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    name = fields.Char(
        string='Parameter Name',
        required=True
    )
    
    unit = fields.Char(
        string='Unit',
        help='e.g., mg/dL, mmol/L, %'
    )
    
    normal_range = fields.Char(
        string='Normal Range',
        help='e.g., 80-120, <5.7, >100'
    )
    
    notes = fields.Text(
        string='Notes'
    )