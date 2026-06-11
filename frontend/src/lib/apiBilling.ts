/**
 * AI Healthcare System — Billing & Telemedicine API
 */
import { apiFetch } from './apiCore';

// ── Payments ─────────────────────────────────────────────────────
export interface PaymentOrder {
  id: string;
  amount: number;
  currency: string;
  status: string;
}

export interface PaymentVerification {
  success: boolean;
  message?: string;
  plan_tier?: string;
}

export async function createPaymentOrder(planId: string): Promise<PaymentOrder> {
  return apiFetch('/payments/create-order', { method: 'POST', body: JSON.stringify({ plan_id: planId }) });
}

export async function verifyPayment(data: { razorpay_order_id: string; razorpay_payment_id: string; razorpay_signature: string }): Promise<PaymentVerification> {
  return apiFetch('/payments/verify', { method: 'POST', body: JSON.stringify(data) });
}

// ── Telemedicine ─────────────────────────────────────────────────
export interface Appointment {
  id: number;
  doctor_id: number;
  appointment_date: string;
  status: string;
  notes?: string;
  doctor?: { name: string; specialization: string };
}

interface BackendAppointment {
  id: number;
  user_id: number;
  doctor_id: number | null;
  specialist: string;
  date_time: string;
  reason: string;
  status: string;
}

interface BackendDoctor {
  id: number;
  full_name?: string;
  name?: string;
  specialization?: string;
}

function splitAppointmentDate(value: string): { date: string; time: string } {
  const direct = value.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/);
  if (direct) {
    return { date: direct[1], time: direct[2] };
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    throw new Error('Invalid appointment date');
  }

  const pad = (n: number) => String(n).padStart(2, '0');
  return {
    date: `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())}`,
    time: `${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`,
  };
}

function normalizeAppointment(appointment: BackendAppointment): Appointment {
  return {
    id: appointment.id,
    doctor_id: appointment.doctor_id ?? 0,
    appointment_date: appointment.date_time,
    status: appointment.status,
    notes: appointment.reason,
    doctor: {
      name: appointment.specialist,
      specialization: appointment.specialist,
    },
  };
}

export async function getAppointments(): Promise<Appointment[]> {
  const appointments = await apiFetch<BackendAppointment[]>('/appointments/');
  return appointments.map(normalizeAppointment);
}

export async function bookAppointment(data: { doctor_id: number; appointment_date: string; notes?: string }): Promise<Appointment> {
  const { date, time } = splitAppointmentDate(data.appointment_date);
  const appointment = await apiFetch<BackendAppointment>('/appointments/', {
    method: 'POST',
    body: JSON.stringify({
      doctor_id: data.doctor_id,
      specialist: 'General Physician',
      date,
      time,
      reason: data.notes || '',
    }),
  });
  return normalizeAppointment(appointment);
}

export async function getDoctors(): Promise<{ id: number; name: string; specialization: string }[]> {
  const doctors = await apiFetch<BackendDoctor[]>('/appointments/doctors');
  return doctors.map((doctor) => ({
    id: doctor.id,
    name: doctor.name || doctor.full_name || 'Doctor',
    specialization: doctor.specialization || 'General Physician',
  }));
}
