/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

class HospitalDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        
        this.state = useState({
            kpis: {},
            loading: true,
        });

        onWillStart(async () => {
            await loadJS("https://cdn.jsdelivr.net/npm/chart.js");
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        try {
            const data = await this.orm.call(
                "hospital.dashboard",
                "get_dashboard_data",
                []
            );
            
            this.state.kpis = data.kpis;
            this.state.patientStats = data.patient_stats;
            this.state.appointmentStats = data.appointment_stats;
            this.state.revenueStats = data.revenue_stats;
            this.state.doctorStats = data.doctor_stats;
            this.state.labTestStats = data.lab_test_stats;
            this.state.loading = false;
            
            // Render charts after data is loaded
            setTimeout(() => this.renderCharts(), 100);
        } catch (error) {
            console.error("Error loading dashboard data:", error);
            this.state.loading = false;
        }
    }

    renderCharts() {
        // Patient Gender Chart
        if (this.state.patientStats?.gender) {
            this.renderPieChart('patientGenderChart', {
                labels: this.state.patientStats.gender.labels,
                data: this.state.patientStats.gender.data,
                colors: ['#4E73DF', '#E74A3B', '#F6C23E']
            });
        }

        // Patient Age Groups Chart
        if (this.state.patientStats?.age_groups) {
            this.renderBarChart('patientAgeChart', {
                labels: this.state.patientStats.age_groups.labels,
                data: this.state.patientStats.age_groups.data,
                label: 'Patients',
                color: '#36B9CC'
            });
        }

        // Appointments by Status Chart
        if (this.state.appointmentStats?.by_status) {
            this.renderDoughnutChart('appointmentStatusChart', {
                labels: this.state.appointmentStats.by_status.labels,
                data: this.state.appointmentStats.by_status.data,
                colors: ['#858796', '#4E73DF', '#1CC88A', '#F6C23E', '#36B9CC', '#E74A3B', '#5A5C69']
            });
        }

        // Revenue Trend Chart
        if (this.state.revenueStats?.monthly_trend) {
            this.renderLineChart('revenueTrendChart', {
                labels: this.state.revenueStats.monthly_trend.labels,
                data: this.state.revenueStats.monthly_trend.data,
                label: 'Revenue',
                color: '#1CC88A'
            });
        }

        // Lab Test Status Chart
        if (this.state.labTestStats?.by_status) {
            this.renderBarChart('labTestStatusChart', {
                labels: this.state.labTestStats.by_status.labels,
                data: this.state.labTestStats.by_status.data,
                label: 'Tests',
                color: '#6610f2'
            });
        }

        // Doctor Specialty Chart
        if (this.state.doctorStats?.by_specialty) {
            this.renderPieChart('doctorSpecialtyChart', {
                labels: this.state.doctorStats.by_specialty.labels,
                data: this.state.doctorStats.by_specialty.data,
                colors: ['#e83e8c', '#fd7e14', '#20c997', '#17a2b8', '#6c757d']
            });
        }
    }

    renderPieChart(canvasId, config) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: config.labels,
                datasets: [{
                    data: config.data,
                    backgroundColor: config.colors,
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    renderDoughnutChart(canvasId, config) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: config.labels,
                datasets: [{
                    data: config.data,
                    backgroundColor: config.colors,
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    renderBarChart(canvasId, config) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: config.labels,
                datasets: [{
                    label: config.label,
                    data: config.data,
                    backgroundColor: config.color,
                    borderColor: config.color,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    renderLineChart(canvasId, config) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: config.labels,
                datasets: [{
                    label: config.label,
                    data: config.data,
                    borderColor: config.color,
                    backgroundColor: config.color + '33',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    openPatients() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'hospital.patient',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    openAppointments() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'hospital.appointment',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    openBillings() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'hospital.billing',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    openLabTests() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'hospital.lab.test',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }
}

HospitalDashboard.template = "hospital_management.DashboardTemplate";

registry.category("actions").add("hospital_dashboard", HospitalDashboard);