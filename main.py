from flask import (
    Flask, render_template, request, jsonify,
    send_file, session, redirect, url_for, flash
)
import sqlite3, re, io, time, csv
import smtplib
from email.message import EmailMessage
from functools import wraps

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Spacer
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import os
from reportlab.lib.units import cm

buffer = io.BytesIO()
doc = SimpleDocTemplate(buffer, pagesize=A4)

styles = getSampleStyleSheet()

content = [] 




app = Flask(__name__)
app.secret_key = "YOUR_SECRET_KEY"

# =========================
# CONFIG
# =========================
ADMIN_USER = "admin"
ADMIN_PASS = "shriii@#"
ADMIN_EMAIL = "shriiishukla05@gmail.com"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "shriiishukla05@gmail.com"
SMTP_PASS = "your_app_password"   # Gmail App Password

# =========================
# UTILS
# =========================
def send_email(subject, body, to_email):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception as e:
        print("Email error:", e)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

# =========================
# PAGES
# =========================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")


# =========================
# CONTACT FORM API
# =========================
@app.before_request
def rate_limit():
    if request.endpoint == "contact_api" and request.method == "POST":
        ip = request.remote_addr
        now = time.time()

        data = session.get("contact_times", {})
        times = data.get(ip, [])
        times = [t for t in times if now - t < 60]

        if len(times) >= 5:
            return jsonify({"message": "Too many requests"}), 429

        times.append(now)
        data[ip] = times
        session["contact_times"] = data

@app.route("/api/contact", methods=["POST"])
def contact_api():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()
    website = request.form.get("website", "").strip()  # honeypot

    if website:
        return jsonify({"message": "Spam detected"}), 400
    if not name or not email or not message:
        return jsonify({"message": "All fields required"}), 400
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"message": "Invalid email"}), 400
    if len(message) < 10:
        return jsonify({"message": "Message too short"}), 400

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute(
        "INSERT INTO contacts (name,email,message) VALUES (?,?,?)",
        (name, email, message)
    )
    conn.commit()
    conn.close()

    send_email(
        f"New Contact: {name}",
        f"Name: {name}\nEmail: {email}\n\n{message}",
        ADMIN_EMAIL
    )

    return jsonify({"message": "Submitted successfully"}), 200

# =========================
# =========================
# INVOICE PDF (FIXED)
# =========================
@app.route("/invoice")
def invoice_pdf():
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "title",
        parent=styles["Heading1"],
        alignment=1,
        spaceAfter=20
    )

    heading = ParagraphStyle(
        "heading",
        parent=styles["Heading2"],
        spaceBefore=15
    )

    body = ParagraphStyle(
        "body",
        parent=styles["BodyText"],
        spaceAfter=10
    )

    highlight = ParagraphStyle(
        "highlight",
        parent=styles["BodyText"],
        backColor="#e6faff",
        leftIndent=10,
        rightIndent=10,
        spaceAfter=15
    )

    terms_heading = ParagraphStyle(
        "TermsHeading",
        parent=styles["Heading2"],
        alignment=1,
        spaceAfter=14
    )

    content = []

    # =========================
    # HEADER
    # =========================
    content.append(Paragraph("Invoice & Pricing Details", title))
    content.append(Paragraph("ss web studio – Website Development Services", styles["Normal"]))
    content.append(Spacer(1, 20))

    # =========================
    # PACKAGES
    # =========================
    content.append(Paragraph("1. Standard Website", heading))
    content.append(Paragraph(
        "<b>Base Price:</b> ₹25,000<br/>"
        "• 5 pages<br/>• Responsive UI<br/>• SEO<br/>• Contact Form",
        body
    ))
    content.append(Paragraph("10% Offer Price: ₹22,000", highlight))

    content.append(Paragraph("2. Premium Website", heading))
    content.append(Paragraph(
        "<b>Base Price:</b> ₹40,000<br/>"
        "• 10+ pages<br/>• Animations<br/>• Advanced SEO",
        body
    ))
    content.append(Paragraph("10% Offer Price: ₹36,000", highlight))

    content.append(Paragraph("3. Enterprise Website", heading))
    content.append(Paragraph(
        "<b>Base Price:</b> ₹60,000<br/>"
        "• Admin Panel<br/>• Database<br/>• Full Stack",
        body
    ))
    content.append(Paragraph("10% Offer Price: ₹54,000", highlight))

    content.append(Spacer(1, 20))

    # =========================
    # OFFER & CONTACT
    # =========================
    content.append(Paragraph(
        "<b>Offer:</b> Pay 50% advance and get 10% OFF<br/>"
        "<b>Contact:</b> sswebstudio05@gmail.com",
        highlight
    ))

    # =========================
    # DISCOUNT OFFER CONDITIONS (MERGED & PROFESSIONAL)
    # =========================
    content.append(Paragraph("🎯 Special Discount Offer – Important Conditions", terms_heading))

    content.append(Paragraph(
        "<b>Offer Condition:</b><br/><br/>"
        "• <b>10% discount</b> is applicable <b>only if the client pays 50% advance of the discounted amount.</b><br/><br/>"

        "<b>Example:</b><br/>"
        "• Website Original Price: <b>₹40,000</b><br/>"
        "• 10% Discount: <b>₹4,000</b><br/>"
        "• Discounted Price: <b>₹36,000</b><br/><br/>"

        "<b>To get the discount:</b><br/>"
        "• Client must pay <b>50% of ₹36,000 = ₹18,000</b> as advance payment.<br/><br/>"

        "<b>If 50% advance is NOT paid:</b><br/>"
        "• ❌ Discount will <b>NOT</b> be applied.<br/>"
        "• Website price will remain <b>₹40,000</b>.<br/>"
        "• Normal advance payment rules will apply.",
        highlight
    ))

    # =========================
    # ACCEPTANCE
    # =========================
    content.append(Paragraph(
        "<b>Acceptance of Terms:</b> By approving this invoice, making any payment, or proceeding with the project, "
        "the client confirms that they have read, understood, and agreed to all the Terms & Conditions mentioned above.",
        highlight
    ))

    # =========================
    # TERMS & CONDITIONS
    # =========================
    content.append(Paragraph(
        "<b>Project Handover:</b> After full payment and successful project completion, we provide all source code, "
        "final files, assets, documentation, and necessary guidance.",
        body
    ))

    content.append(Paragraph(
        "<b>Payment Terms:</b> 50% advance payment is mandatory before project initiation. "
        "Remaining 50% must be paid before final delivery.",
        body
    ))

    content.append(Paragraph(
        "<b>Revisions:</b> Up to 2 minor revisions are included. Additional changes will be charged.",
        body
    ))

    content.append(Paragraph(
        "<b>Project Timeline:</b> Delays in feedback may extend delivery timelines.",
        body
    ))

    content.append(Paragraph(
        "<b>Client Responsibilities:</b> Client must provide all required content unless agreed otherwise.",
        body
    ))

    content.append(Paragraph(
        "<b>Ownership:</b> Full ownership will be transferred only after full payment.",
        body
    ))

    content.append(Paragraph(
        "<b>Hosting & Domain:</b> Not included unless explicitly mentioned.",
        body
    ))

    content.append(Paragraph(
        "<b>Post-Delivery Support:</b> 4 days free bug-fix support after delivery.",
        body
    ))

    content.append(Paragraph(
        "<b>Cancellation & Refund:</b> Advance payment is non-refundable once work has started.",
        body
    ))

    content.append(Paragraph(
        "<b>Payment Delay:</b> Final files will not be shared until full payment is received.",
        body
    ))

    content.append(Paragraph(
        "<b>Limitation of Liability:</b> ss web studio is not liable for indirect or consequential damages.",
        body
    ))

    content.append(Paragraph(
        "<b>Third-Party Services:</b> We are not responsible for issues caused by third-party services.",
        body
    ))

    content.append(Paragraph(
        "<b>Force Majeure:</b> Timelines may be affected due to uncontrollable circumstances.",
        body
    ))

    content.append(Paragraph(
        "<b>Note:</b> Any work not mentioned in this invoice is considered out of scope.",
        highlight
    ))

    # =========================
    # FOOTER WITH LOGO
    # =========================
    def draw_footer(canvas, doc):
        logo_path = os.path.join(app.root_path, "static", "logo.png")
        if os.path.exists(logo_path):
            canvas.drawImage(
                logo_path,
                (A4[0] - 4*cm) / 2,
                1.2 * cm,
                width=4*cm,
                height=2*cm,
                preserveAspectRatio=True,
                mask="auto"
            )

    doc.build(content, onFirstPage=draw_footer, onLaterPages=draw_footer)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="ss web studio-Website-Quote.pdf",
        mimetype="application/pdf"
    )







    content.append(Paragraph("Thanks for choosing ss web studio!", styles["Normal"]))
    

    doc.build(content)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Buildify-Website Quote.pdf",
        mimetype="application/pdf"
    )



# =========================
# ADMIN PANEL
# =========================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if (
            request.form.get("username") == ADMIN_USER
            and request.form.get("password") == ADMIN_PASS
        ):
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials")
    return render_template("admin_login.html")

@app.route("/admin/logout")
@login_required
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

@app.route("/admin")
@login_required
def admin_dashboard():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM contacts ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()
    return render_template("admin_dashboard.html", contacts=data)

@app.route("/admin/export")
@login_required
def admin_export():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT name,email,message,created_at FROM contacts")
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Email", "Message", "Date"])
    writer.writerows(rows)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        as_attachment=True,
        download_name="contacts.csv",
        mimetype="text/csv"
    )

# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
