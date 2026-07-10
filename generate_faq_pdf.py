import os
import sys

def generate_pdf():
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
    except ImportError:
        print("ReportLab is not installed. Please install it using 'pip install reportlab' first.")
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs("data", exist_ok=True)
    pdf_path = os.path.join("data", "gigacorp_faq.pdf")

    # Set up document
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom Styles for professional look
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#4B5563'),
        spaceAfter=30
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SubSectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0D9488'),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor('#374151'),
        spaceAfter=8
    )

    story = []

    # PAGE 1: TITLE & INTRODUCTION
    story.append(Paragraph("GigaCorp Customer Support Manual", title_style))
    story.append(Paragraph("Official Frequently Asked Questions & Operational Guidelines", subtitle_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Section 1: Introduction to GigaCorp", h1_style))
    story.append(Paragraph(
        "Welcome to the GigaCorp Customer Support Manual. GigaCorp is a leading innovator in consumer electronics, "
        "smart home ecosystems, and high-performance technical gadgets. Our mission is to seamlessly integrate tech "
        "into daily life, backed by world-class support services. This manual acts as our official source of truth "
        "for customer support responses, policy interpretations, and hardware troubleshooting guidelines.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Section 1.1: Core Service Boundaries", h2_style))
    story.append(Paragraph(
        "GigaCorp provides customer support strictly for official GigaCorp hardware, software configurations, "
        "and subscription services. We support GigaPhone, GigaBook, GigaHome smart hubs, and GigaCare insurance plans. "
        "Support agents must never provide assistance for non-GigaCorp applications, custom operating systems, "
        "third-party accessories, or general internet questions. If a query falls outside our service boundaries, "
        "agents must politely decline and direct the user to their respective service provider.",
        body_style
    ))
    story.append(PageBreak())

    # PAGE 2: SHIPPING & DELIVERY
    story.append(Paragraph("Section 2: Shipping & Delivery Policies", h1_style))
    story.append(Paragraph(
        "GigaCorp ships products globally from multiple fulfillment centers to ensure rapid transit. All orders are processed "
        "within 24 business hours. Order cancellation is only possible before the item is handed over to the courier.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Section 2.1: Shipping Times & Methods", h2_style))
    story.append(Paragraph(
        "GigaCorp offers three primary shipping speeds:\n"
        "• Standard Shipping: Delivered in 3 to 5 business days.\n"
        "• Express Shipping: Delivered in 1 to 2 business days.\n"
        "• International Shipping: Delivered in 7 to 14 business days, depending on custom clearance times in the destination country.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Section 2.2: Shipping Rates", h2_style))
    story.append(Paragraph(
        "• Standard Shipping is free for all orders totaling $50 or more. For orders below $50, a flat standard rate of $4.99 applies.\n"
        "• Express Shipping is available for a flat rate of $14.99 on all orders regardless of value.\n"
        "• International shipping rates are calculated dynamically at checkout based on package weight and destination zone.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Section 2.3: Order Tracking & Issues", h2_style))
    story.append(Paragraph(
        "A tracking link is automatically emailed to the customer once the order is shipped. If a shipment is marked "
        "as delivered but the customer cannot locate it, they must contact customer support within 48 hours. GigaCorp will "
        "initiate an investigation with the courier, which takes up to 3 business days, before approving a replacement or refund.",
        body_style
    ))
    story.append(PageBreak())

    # PAGE 3: RETURNS, REFUNDS & WARRANTY
    story.append(Paragraph("Section 3: Return & Refund Policies", h1_style))
    story.append(Paragraph(
        "At GigaCorp, we strive to build quality products, but we understand that customer needs can change. This section "
        "outlines how support staff should manage refund requests, item exchanges, and warranty claims.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Section 3.1: Return Window & Conditions", h2_style))
    story.append(Paragraph(
        "Customers can return any GigaCorp product within 30 calendar days from the delivery date. To be eligible "
        "for a full refund, items must be in brand-new condition, containing all original packaging, manuals, accessories, "
        "and promotional freebies. Products showing signs of accidental damage, heavy wear, or user modification will "
        "not be eligible for returns.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Section 3.2: Return Shipping Fees", h2_style))
    story.append(Paragraph(
        "• Defective Items: If a product is verified defective on arrival or breaks under normal use within the warranty, "
        "GigaCorp provides a prepaid shipping label at no cost to the customer.\n"
        "• Change of Mind Returns: For standard returns where the product is functioning normally, the customer is responsible "
        "for return shipping fees. GigaCorp will deduct a flat label fee of $5.99 from the final refund amount if the customer "
        "chooses to use our generated shipping label.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Section 3.3: Refund Processing Times", h2_style))
    story.append(Paragraph(
        "Once a returned package arrives at our quality inspection warehouse, it is inspected within 48 hours. If approved, "
        "the refund is automatically initiated. The funds will appear in the customer's account in 5 to 7 business days, "
        "depending on their bank or financial institution. GigaCorp can only issue refunds to the original payment method used.",
        body_style
    ))
    story.append(PageBreak())

    # PAGE 4: BILLING & SUBSCRIPTIONS
    story.append(Paragraph("Section 4: Billing & Subscriptions", h1_style))
    story.append(Paragraph(
        "GigaCorp provides hardware and services billed on a one-time and recurring subscription basis. Agents must handle "
        "billing queries with high security awareness.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Section 4.1: Accepted Payment Methods", h2_style))
    story.append(Paragraph(
        "We accept major credit cards (Visa, MasterCard, American Express), PayPal, Apple Pay, and Google Pay. "
        "We also accept GigaPay, our proprietary digital checkout. We do not accept personal checks, cash on delivery (COD), "
        "or wire transfers.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Section 4.2: Subscriptions & Cancellation", h2_style))
    story.append(Paragraph(
        "GigaCare Protection and GigaCloud storage plans are billed monthly. Subscriptions automatically renew "
        "each month on the original signup date. Customers can cancel their subscription at any time via the GigaCorp "
        "online account dashboard or by calling support. Cancellations take effect at the end of the current billing cycle. "
        "GigaCorp does not issue partial-month refunds or prorated credits for unused periods.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Section 4.3: Chargebacks & Payment Failures", h2_style))
    story.append(Paragraph(
        "If a recurring payment fails, GigaCorp will retry charging the card on file three times over the next 9 days. "
        "If payment is still outstanding, the subscription is suspended. In the event of a chargeback, the customer account "
        "associated with the dispute is automatically locked pending safety review by the security department.",
        body_style
    ))
    story.append(PageBreak())

    # PAGE 5: ACCOUNT SECURITY & TECHNICAL SUPPORT
    story.append(Paragraph("Section 5: Account Security & Technical Support", h1_style))
    story.append(Paragraph(
        "Ensuring customer security and resolving hardware and firmware issues is vital. This section details security "
        "policies and essential troubleshooting methodologies.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Section 5.1: Password Reset Guidelines", h2_style))
    story.append(Paragraph(
        "Customers can trigger a password reset from the login screen by entering their registered email address. "
        "A secure, encrypted link is emailed and remains valid for exactly 15 minutes. Support agents can never see "
        "passwords or manually set a password for a customer. If a customer is not receiving the email, check spam folders "
        "or verify if the email matches their profile.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Section 5.2: Two-Factor Authentication (2FA)", h2_style))
    story.append(Paragraph(
        "GigaCorp strongly encourages customers to enable 2FA under Account Settings. We support SMS code delivery "
        "and TOTP authenticator apps (Google Authenticator, Duo). If a customer loses access to their 2FA device, "
        "they must present a valid government-issued ID matching their account profile before support agents can "
        "manually disable 2FA.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Section 5.3: Troubleshooting GigaDevices", h2_style))
    story.append(Paragraph(
        "When hardware or firmware errors occur on a GigaDevice (e.g. frozen display, poor connection), follow these steps:\n"
        "1. Perform a Soft Reset: Hold the power button down for 10 seconds until the screen goes blank and restarts.\n"
        "2. Check Firmware: Ensure the device is running the latest firmware using the GigaConnect smartphone app.\n"
        "3. Factory Reset: If soft reset fails, hold the Power and Volume Down buttons simultaneously for 15 seconds. "
        "Warning: This deletes all locally saved customer configurations and resets the device to factory settings.",
        body_style
    ))

    # Build the document
    doc.build(story)
    print(f"PDF generated successfully at {pdf_path}")

if __name__ == "__main__":
    generate_pdf()
