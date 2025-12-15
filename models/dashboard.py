from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class HospitalDashboard(models.TransientModel):
    """Transient model for hospital dashboard analytics"""
    
    _name = 'hospital.dashboard'
    _description = 'Hospital Dashboard'
    
    name = fields.Char(string='Dashboard', default='Hospital Analytics', readonly=True)
    
    # Date Filters
    date_from = fields.Date(
        string='From Date', 
        default=lambda self: fields.Date.today() - relativedelta(months=1)
    )
    date_to = fields.Date(
        string='To Date', 
        default=fields.Date.today
    )
    
    # KPI Fields
    total_patients = fields.Integer(
        string='Total Patients',
        compute='_compute_kpis'
    )
    
    total_doctors = fields.Integer(
        string='Total Doctors',
        compute='_compute_kpis'
    )
    
    appointments_today = fields.Integer(
        string="Today's Appointments",
        compute='_compute_kpis'
    )
    
    appointments_period = fields.Integer(
        string='Appointments (Period)',
        compute='_compute_kpis'
    )
    
    total_revenue = fields.Float(
        string='Total Revenue',
        compute='_compute_kpis'
    )
    
    total_paid = fields.Float(
        string='Paid Amount',
        compute='_compute_kpis'
    )
    
    total_pending = fields.Float(
        string='Pending Amount',
        compute='_compute_kpis'
    )
    
    pending_lab_tests = fields.Integer(
        string='Pending Lab Tests',
        compute='_compute_kpis'
    )
    
    new_patients = fields.Integer(
        string='New Patients',
        compute='_compute_kpis'
    )
    
    # Gender Statistics
    male_patients = fields.Integer(
        string='Male Patients',
        compute='_compute_patient_stats'
    )
    
    female_patients = fields.Integer(
        string='Female Patients',
        compute='_compute_patient_stats'
    )
    
    # Appointment Statistics
    draft_appointments = fields.Integer(
        string='Draft',
        compute='_compute_appointment_stats'
    )
    
    confirmed_appointments = fields.Integer(
        string='Confirmed',
        compute='_compute_appointment_stats'
    )
    
    done_appointments = fields.Integer(
        string='Done',
        compute='_compute_appointment_stats'
    )
    
    cancelled_appointments = fields.Integer(
        string='Cancelled',
        compute='_compute_appointment_stats'
    )
    
    @api.depends('date_from', 'date_to')
    def _compute_kpis(self):
        """Compute Key Performance Indicators"""
        for record in self:
            Patient = self.env['hospital.patient']
            Appointment = self.env['hospital.appointment']
            Billing = self.env['hospital.billing']
            LabTest = self.env['hospital.lab.test']
            
            # Total counts
            record.total_patients = Patient.search_count([])
            record.total_doctors = self.env['hospital.doctor'].search_count([('active', '=', True)])
            
            # Today's appointments
            record.appointments_today = Appointment.search_count([
                ('appointment_date', '=', fields.Date.today())
            ])
            
            # Period appointments
            record.appointments_period = Appointment.search_count([
                ('appointment_date', '>=', record.date_from),
                ('appointment_date', '<=', record.date_to)
            ])
            
            # New patients in period
            record.new_patients = Patient.search_count([
                ('create_date', '>=', record.date_from),
                ('create_date', '<=', record.date_to)
            ])
            
            # Revenue
            billings = Billing.search([
                ('billing_date', '>=', record.date_from),
                ('billing_date', '<=', record.date_to)
            ])
            record.total_revenue = sum(billings.mapped('total_amount'))
            record.total_paid = sum(billings.mapped('paid_amount'))
            record.total_pending = record.total_revenue - record.total_paid
            
            # Pending lab tests
            record.pending_lab_tests = LabTest.search_count([
                ('state', 'in', ['requested', 'in_progress'])
            ])
    
    @api.depends('date_from', 'date_to')
    def _compute_patient_stats(self):
        """Compute patient statistics"""
        for record in self:
            Patient = self.env['hospital.patient']
            record.male_patients = Patient.search_count([('gender', '=', 'male')])
            record.female_patients = Patient.search_count([('gender', '=', 'female')])
    
    @api.depends('date_from', 'date_to')
    def _compute_appointment_stats(self):
        """Compute appointment statistics"""
        for record in self:
            Appointment = self.env['hospital.appointment']
            domain_base = [
                ('appointment_date', '>=', record.date_from),
                ('appointment_date', '<=', record.date_to)
            ]
            
            record.draft_appointments = Appointment.search_count(domain_base + [('state', '=', 'draft')])
            record.confirmed_appointments = Appointment.search_count(domain_base + [('state', '=', 'confirmed')])
            record.done_appointments = Appointment.search_count(domain_base + [('state', '=', 'done')])
            record.cancelled_appointments = Appointment.search_count(domain_base + [('state', '=', 'cancelled')])
    
    def action_view_patients(self):
        """Open patients view"""
        return {
            'name': 'Patients',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.patient',
            'view_mode': 'kanban,list,form',
            'target': 'current',
        }
    
    def action_view_appointments(self):
        """Open appointments view"""
        return {
            'name': 'Appointments',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.appointment',
            'view_mode': 'calendar,list,form',
            'target': 'current',
        }
    
    def action_view_billings(self):
        """Open billings view"""
        return {
            'name': 'Billings',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.billing',
            'view_mode': 'list,form',
            'target': 'current',
        }
    
    def action_view_lab_tests(self):
        """Open lab tests view"""
        return {
            'name': 'Lab Tests',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.lab.test',
            'view_mode': 'list,form',
            'domain': [('state', 'in', ['requested', 'in_progress'])],
            'target': 'current',
        }