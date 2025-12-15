from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HospitalBilling(models.Model):
    """Model for managing patient billing and invoicing"""
    
    _name = 'hospital.billing'
    _description = 'Hospital Billing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference'
    _order = 'billing_date desc'
    
    # Basic Fields
    reference = fields.Char(
        string='Bill Reference',
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
    
    # Billing Information
    billing_date = fields.Date(
        string='Billing Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    due_date = fields.Date(
        string='Due Date',
        tracking=True
    )
    
    # Line Items
    line_ids = fields.One2many(
        comodel_name='hospital.billing.line',
        inverse_name='billing_id',
        string='Billing Lines',
        copy=True
    )
    
    # Amounts
    subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_amounts',
        store=True
    )
    
    discount_percent = fields.Float(
        string='Discount (%)',
        default=0.0,
        tracking=True
    )
    
    discount_amount = fields.Float(
        string='Discount Amount',
        compute='_compute_amounts',
        store=True
    )
    
    tax_percent = fields.Float(
        string='Tax (%)',
        default=0.0,
        tracking=True
    )
    
    tax_amount = fields.Float(
        string='Tax Amount',
        compute='_compute_amounts',
        store=True
    )
    
    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_amounts',
        store=True,
        tracking=True
    )
    
    paid_amount = fields.Float(
        string='Paid Amount',
        default=0.0,
        tracking=True
    )
    
    balance_amount = fields.Float(
        string='Balance',
        compute='_compute_amounts',
        store=True
    )
    
    # Payment Information
    payment_method = fields.Selection(
        selection=[
            ('cash', 'Cash'),
            ('card', 'Credit/Debit Card'),
            ('bank_transfer', 'Bank Transfer'),
            ('insurance', 'Insurance'),
            ('online', 'Online Payment'),
        ],
        string='Payment Method',
        tracking=True
    )
    
    payment_status = fields.Selection(
        selection=[
            ('unpaid', 'Unpaid'),
            ('partial', 'Partially Paid'),
            ('paid', 'Paid'),
            ('refunded', 'Refunded'),
        ],
        string='Payment Status',
        compute='_compute_payment_status',
        store=True,
        tracking=True
    )
    
    # Related Fields
    patient_name = fields.Char(
        related='patient_id.name',
        string='Patient Name',
        readonly=True
    )
    
    patient_reference = fields.Char(
        related='patient_id.reference',
        string='Patient Reference',
        readonly=True
    )
    
    doctor_name = fields.Char(
        related='doctor_id.name',
        string='Doctor Name',
        readonly=True
    )
    
    # Status
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('paid', 'Paid'),
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
        string='Notes'
    )
    
    # ==========================================
    # Computed Fields
    # ==========================================
    
    @api.depends('line_ids.subtotal', 'discount_percent', 'tax_percent', 'paid_amount')
    def _compute_amounts(self):
        """Compute all amounts"""
        for record in self:
            # Subtotal from lines
            subtotal = sum(line.subtotal for line in record.line_ids)
            record.subtotal = subtotal
            
            # Discount
            discount = (subtotal * record.discount_percent) / 100
            record.discount_amount = discount
            
            # Amount after discount
            amount_after_discount = subtotal - discount
            
            # Tax
            tax = (amount_after_discount * record.tax_percent) / 100
            record.tax_amount = tax
            
            # Total
            total = amount_after_discount + tax
            record.total_amount = total
            
            # Balance
            record.balance_amount = total - record.paid_amount
    
    @api.depends('total_amount', 'paid_amount')
    def _compute_payment_status(self):
        """Compute payment status based on paid amount"""
        for record in self:
            if record.total_amount <= 0:
                record.payment_status = 'unpaid'
            elif record.paid_amount <= 0:
                record.payment_status = 'unpaid'
            elif record.paid_amount >= record.total_amount:
                record.payment_status = 'paid'
            else:
                record.payment_status = 'partial'
    
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
            
            # Add consultation fee as first line
            if not self.line_ids and self.doctor_id.consultation_fee > 0:
                self.line_ids = [(0, 0, {
                    'service_type': 'consultation',
                    'description': 'Medical Consultation',
                    'quantity': 1,
                    'unit_price': self.doctor_id.consultation_fee,
                })]
    
    @api.onchange('paid_amount')
    def _onchange_paid_amount(self):
        """Auto-update state when fully paid"""
        if self.paid_amount >= self.total_amount and self.total_amount > 0:
            if self.state == 'confirmed':
                self.state = 'paid'
    
    # ==========================================
    # Constraints
    # ==========================================
    
    @api.constrains('paid_amount', 'total_amount')
    def _check_paid_amount(self):
        """Ensure paid amount doesn't exceed total"""
        for record in self:
            if record.paid_amount > record.total_amount:
                raise ValidationError(
                    'Paid amount cannot exceed total amount!'
                )
    
    @api.constrains('discount_percent')
    def _check_discount_percent(self):
        """Ensure discount is between 0 and 100"""
        for record in self:
            if record.discount_percent < 0 or record.discount_percent > 100:
                raise ValidationError(
                    'Discount percentage must be between 0 and 100!'
                )
    
    @api.constrains('tax_percent')
    def _check_tax_percent(self):
        """Ensure tax is between 0 and 100"""
        for record in self:
            if record.tax_percent < 0 or record.tax_percent > 100:
                raise ValidationError(
                    'Tax percentage must be between 0 and 100!'
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
                    'hospital.billing'
                ) or 'New'
        return super().create(vals_list)
    
    # ==========================================
    # Action Methods
    # ==========================================
    
    def action_confirm(self):
        """Confirm billing"""
        for record in self:
            if record.state == 'draft':
                if not record.line_ids:
                    raise ValidationError('Please add at least one billing line!')
                record.state = 'confirmed'
                record.message_post(body='Billing confirmed.')
    
    def action_register_payment(self):
        """Open payment wizard"""
        self.ensure_one()
        return {
            'name': 'Register Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.billing.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_billing_id': self.id,
                'default_amount': self.balance_amount,
            }
        }
    
    def action_mark_as_paid(self):
        """Mark as fully paid"""
        for record in self:
            if record.state == 'confirmed':
                record.paid_amount = record.total_amount
                record.state = 'paid'
                record.message_post(body='Marked as fully paid.')
    
    def action_cancel(self):
        """Cancel billing"""
        for record in self:
            if record.state in ['draft', 'confirmed']:
                record.state = 'cancelled'
                record.message_post(body='Billing cancelled.')
    
    def action_reset_to_draft(self):
        """Reset to draft"""
        for record in self:
            record.state = 'draft'
            record.message_post(body='Reset to draft.')


class HospitalBillingLine(models.Model):
    """Model for billing line items"""
    
    _name = 'hospital.billing.line'
    _description = 'Hospital Billing Line'
    _order = 'sequence, id'
    
    billing_id = fields.Many2one(
        comodel_name='hospital.billing',
        string='Billing',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    service_type = fields.Selection(
        selection=[
            ('consultation', 'Consultation'),
            ('lab_test', 'Lab Test'),
            ('xray', 'X-Ray'),
            ('scan', 'CT/MRI Scan'),
            ('surgery', 'Surgery'),
            ('medicine', 'Medicine'),
            ('room_charge', 'Room Charge'),
            ('other', 'Other'),
        ],
        string='Service Type',
        required=True,
        default='consultation'
    )
    
    description = fields.Char(
        string='Description',
        required=True
    )
    
    quantity = fields.Float(
        string='Quantity',
        default=1.0,
        required=True
    )
    
    unit_price = fields.Float(
        string='Unit Price',
        required=True
    )
    
    subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True
    )
    
    notes = fields.Text(
        string='Notes'
    )
    
    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        """Compute line subtotal"""
        for line in self:
            line.subtotal = line.quantity * line.unit_price
    
    @api.constrains('quantity', 'unit_price')
    def _check_positive_values(self):
        """Ensure quantity and price are positive"""
        for line in self:
            if line.quantity <= 0:
                raise ValidationError('Quantity must be greater than zero!')
            if line.unit_price < 0:
                raise ValidationError('Unit price cannot be negative!')