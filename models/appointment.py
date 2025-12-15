from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class HospitalAppointment(models.Model):
    """Model for managing hospital appointments"""
    
    _name = 'hospital.appointment'
    _description = 'Hospital Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference'
    _order = 'appointment_date desc, appointment_time'
    
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
    
    # Date & Time Fields
    appointment_date = fields.Date(
        string='Appointment Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    appointment_time = fields.Float(
        string='Appointment Time',
        required=True,
        help='Time in 24-hour format (e.g., 14.5 for 2:30 PM)'
    )
    
    appointment_datetime = fields.Datetime(
        string='Appointment Date & Time',
        compute='_compute_appointment_datetime',
        store=True,
        help='Combined date and time for calendar view'
    )
    
    duration = fields.Float(
        string='Duration (Hours)',
        default=1.0,
        help='Appointment duration in hours'
    )
    
    end_datetime = fields.Datetime(
        string='End Date & Time',
        compute='_compute_end_datetime',
        store=True
    )
    
    # Appointment Details
    appointment_type = fields.Selection(
        selection=[
            ('consultation', 'Consultation'),
            ('followup', 'Follow-up'),
            ('checkup', 'Check-up'),
            ('emergency', 'Emergency'),
        ],
        string='Appointment Type',
        default='consultation',
        required=True,
        tracking=True
    )
    
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('arrived', 'Patient Arrived'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
            ('no_show', 'No Show'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True
    )
    
    priority = fields.Selection(
        selection=[
            ('0', 'Normal'),
            ('1', 'Low'),
            ('2', 'High'),
            ('3', 'Very High'),
        ],
        string='Priority',
        default='0',
        tracking=True
    )
    
    # Related Fields (for easy access)
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
    
    doctor_specialty = fields.Selection(
        related='doctor_id.specialty',
        string='Doctor Specialty',
        readonly=True
    )
    
    consultation_fee = fields.Float(
        related='doctor_id.consultation_fee',
        string='Consultation Fee',
        readonly=True
    )
    
    # Additional Fields
    notes = fields.Text(
        string='Notes',
        tracking=True
    )
    
    diagnosis = fields.Text(
        string='Diagnosis',
        tracking=True
    )
    
    prescription = fields.Text(
        string='Prescription',
        tracking=True
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Color for Calendar View
    color = fields.Integer(
        string='Color',
        compute='_compute_color',
        store=True
    )
    
    # ==========================================
    # Computed Fields
    # ==========================================
    
    @api.depends('appointment_date', 'appointment_time')
    def _compute_appointment_datetime(self):
        """Combine date and time into datetime field"""
        for record in self:
            if record.appointment_date and record.appointment_time:
                # Convert float time to hours and minutes
                hours = int(record.appointment_time)
                minutes = int((record.appointment_time - hours) * 60)
                
                # Combine date and time
                dt = datetime.combine(
                    record.appointment_date,
                    datetime.min.time()
                ) + timedelta(hours=hours, minutes=minutes)
                
                record.appointment_datetime = dt
            else:
                record.appointment_datetime = False
    
    @api.depends('appointment_datetime', 'duration')
    def _compute_end_datetime(self):
        """Calculate end time based on duration"""
        for record in self:
            if record.appointment_datetime and record.duration:
                record.end_datetime = record.appointment_datetime + timedelta(hours=record.duration)
            else:
                record.end_datetime = False
    
    @api.depends('state', 'appointment_type')
    def _compute_color(self):
        """Compute color for calendar view based on state and type"""
        for record in self:
            if record.state == 'cancelled':
                record.color = 1  # Red
            elif record.state == 'done':
                record.color = 10  # Green
            elif record.state == 'in_progress':
                record.color = 7   # Blue
            elif record.state == 'confirmed':
                record.color = 4   # Yellow
            elif record.appointment_type == 'emergency':
                record.color = 9   # Orange
            else:
                record.color = 0   # Default
    
    # ==========================================
    # Onchange Methods
    # ==========================================
    
    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        """Suggest doctor when patient is selected"""
        if self.patient_id and self.patient_id.doctor_id:
            self.doctor_id = self.patient_id.doctor_id
    
    @api.onchange('appointment_type')
    def _onchange_appointment_type(self):
        """Set priority for emergency appointments"""
        if self.appointment_type == 'emergency':
            self.priority = '3'
            self.duration = 0.5  # 30 minutes for emergency
    
    # ==========================================
    # Constraints
    # ==========================================
    
    @api.constrains('appointment_date', 'appointment_time')
    def _check_appointment_datetime(self):
        """Validate appointment is in the future"""
        for record in self:
            if record.appointment_datetime:
                if record.appointment_datetime < datetime.now():
                    raise ValidationError(
                        'Appointment date and time must be in the future!'
                    )
    
    @api.constrains('appointment_time')
    def _check_appointment_time(self):
        """Validate time is between 8 AM and 8 PM"""
        for record in self:
            if record.appointment_time:
                if record.appointment_time < 8.0 or record.appointment_time >= 20.0:
                    raise ValidationError(
                        'Appointment time must be between 8:00 AM and 8:00 PM!'
                    )
    
    @api.constrains('doctor_id', 'appointment_datetime', 'duration')
    def _check_doctor_availability(self):
        """Check if doctor is available at the requested time"""
        for record in self:
            if record.doctor_id and record.appointment_datetime and record.state != 'cancelled':
                # Search for overlapping appointments
                overlapping = self.search([
                    ('id', '!=', record.id),
                    ('doctor_id', '=', record.doctor_id.id),
                    ('state', 'not in', ['cancelled', 'no_show']),
                    ('appointment_datetime', '<', record.end_datetime),
                    ('end_datetime', '>', record.appointment_datetime),
                ])
                
                if overlapping:
                    raise ValidationError(
                        f'Doctor {record.doctor_id.name} is not available at this time. '
                        f'Conflicting appointment: {overlapping[0].reference}'
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
                    'hospital.appointment'
                ) or 'New'
        return super().create(vals_list)
    
    # ==========================================
    # Action Methods
    # ==========================================
    
    def action_confirm(self):
        """Confirm appointment and send email"""
        for record in self:
            if record.state == 'draft':
                record.state = 'confirmed'
                record.message_post(body='Appointment confirmed.')
                # Send confirmation email
                record.send_confirmation_email()
    
    def action_arrived(self):
        """Mark patient as arrived"""
        for record in self:
            if record.state == 'confirmed':
                record.state = 'arrived'
                record.message_post(body='Patient has arrived.')
    
    def action_start(self):
        """Start appointment"""
        for record in self:
            if record.state == 'arrived':
                record.state = 'in_progress'
                record.message_post(body='Consultation started.')
    
    def action_done(self):
        """Complete appointment"""
        for record in self:
            if record.state == 'in_progress':
                record.state = 'done'
                record.message_post(body='Consultation completed.')
                # Update patient state if needed
                if record.patient_id.state == 'consultation':
                    record.patient_id.state = 'done'
    
    def action_cancel(self):
        """Cancel appointment"""
        for record in self:
            if record.state not in ['done', 'cancelled']:
                record.state = 'cancelled'
                record.message_post(body='Appointment cancelled.')
    
    def action_no_show(self):
        """Mark as no show"""
        for record in self:
            if record.state == 'confirmed':
                record.state = 'no_show'
                record.message_post(body='Patient did not show up.')
    
    def action_reset_to_draft(self):
        """Reset to draft"""
        for record in self:
            record.state = 'draft'
            record.message_post(body='Reset to draft.')
    
    # ==========================================
    # Email Notification Methods
    # ==========================================
    
    def send_confirmation_email(self):
        """Send confirmation email to patient"""
        self.ensure_one()
        template = self.env.ref('hospital_management.email_template_appointment_confirmation', raise_if_not_found=False)
        if template:
            try:
                template.send_mail(self.id, force_send=True)
                self.message_post(body='Confirmation email sent to patient.')
            except Exception as e:
                self.message_post(body=f'Failed to send email: {str(e)}')
    
    def send_reminder_email(self):
        """Send reminder email to patient"""
        self.ensure_one()
        template = self.env.ref('hospital_management.email_template_appointment_reminder', raise_if_not_found=False)
        if template:
            try:
                template.send_mail(self.id, force_send=True)
                self.message_post(body='Reminder email sent to patient.')
            except Exception as e:
                self.message_post(body=f'Failed to send reminder: {str(e)}')
    
    @api.model
    def send_daily_reminders(self):
        """Send reminder emails for appointments tomorrow (Called by Cron)"""
        tomorrow = fields.Date.today() + timedelta(days=1)
        appointments = self.search([
            ('appointment_date', '=', tomorrow),
            ('state', '=', 'confirmed')
        ])
        
        count = 0
        for appointment in appointments:
            appointment.send_reminder_email()
            count += 1
        
        # Log in system
        if count > 0:
            self.env['ir.logging'].sudo().create({
                'name': 'Appointment Reminders',
                'type': 'server',
                'level': 'INFO',
                'message': f'Sent {count} appointment reminder emails for {tomorrow}',
                'path': 'hospital.appointment',
                'func': 'send_daily_reminders',
            })
        
        return count