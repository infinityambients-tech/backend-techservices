from datetime import datetime
from models import db, Invoice, InvoiceSequence, Tenant
import os

class InvoiceService:
    @staticmethod
    def get_next_invoice_number():
        """Generates a number like FV/2026/02/0001."""
        now = datetime.utcnow()
        year = now.year
        month = now.month

        # Atomic increment check
        seq = InvoiceSequence.query.filter_by(year=year, month=month).first()
        if not seq:
            seq = InvoiceSequence(year=year, month=month, last_value=1)
            db.session.add(seq)
        else:
            seq.last_value += 1
        
        db.session.commit()
        
        return f"FV/{year}/{month:02d}/{seq.last_value:04d}"

    @staticmethod
    def calculate_vat(gross_amount_cents, vat_rate=23):
        """
        Gross = Net + VAT
        Net = Gross / (1 + Rate)
        """
        net = int(gross_amount_cents / (1 + (vat_rate / 100)))
        vat = gross_amount_cents - net
        return net, vat

    @staticmethod
    def generate_invoice_for_payment(payment):
        reservation = payment.reservation
        if not reservation:
            return None

        # Determine VAT rate (default 23% for PL)
        vat_rate = 23
        net, vat = InvoiceService.calculate_vat(payment.amount, vat_rate)
        
        invoice_num = InvoiceService.get_next_invoice_number()
        
        invoice = Invoice(
            tenant_id=payment.tenant_id,
            user_id=reservation.user_id,
            reservation_id=reservation.id,
            payment_id=payment.id,
            invoice_number=invoice_num,
            gross_amount=payment.amount,
            net_amount=net,
            vat_amount=vat,
            vat_rate=vat_rate,
            currency=payment.currency or "PLN",
            buyer_name=f"{reservation.user.first_name} {reservation.user.last_name}",
            buyer_address= "Dane z profilu", # Placeholder
            buyer_nip=None, # Placeholder
            issued_at=datetime.utcnow()
        )
        
        db.session.add(invoice)
        db.session.commit()
        
        # Placeholder for PDF generation
        # pdf_path = generate_pdf(invoice)
        # invoice.pdf_url = pdf_path
        # db.session.commit()
        
        print(f"[Invoice] Generated: {invoice_num} for payment {payment.id}")
        return invoice
