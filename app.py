import streamlit as st
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import re
import io

st.set_page_config(page_title="Bulk Email Sender", page_icon="📧", layout="centered")

st.title("📧 Bulk Email Sender")
st.markdown("Apni Excel file upload karo aur sab clients ko ek click mein email bhejo!")

# ── SIDEBAR — Credentials ──
with st.sidebar:
    st.header("⚙️ Gmail Setup")
    gmail = st.text_input("Aapka Gmail", placeholder="example@gmail.com")
    app_password = st.text_input("Gmail App Password", type="password", placeholder="xxxx xxxx xxxx xxxx")
    st.caption("App Password kaise banayein? [Click here](https://myaccount.google.com/apppasswords)")
    st.markdown("---")
    st.markdown("**App Password Steps:**")
    st.markdown("1. Google Account → Security")
    st.markdown("2. 2-Step Verification ON karo")
    st.markdown("3. App Passwords → Generate")

# ── EMAIL CONTENT ──
st.subheader("📝 Email Content")
col1, col2 = st.columns([1,1])
with col1:
    subject = st.text_input("Subject", placeholder="Yahan subject likho")
with col2:
    st.write("")

body = st.text_area("Email Body", height=200, placeholder="Yahan apna email content likho...")

# ── EXCEL UPLOAD ──
st.subheader("📂 Clients Ki List")
uploaded_file = st.file_uploader("Excel file upload karo (.xlsx)", type=["xlsx", "xls", "csv"])

emails_list = []

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success(f"File load ho gayi! {len(df)} rows mili hain.")

        # Auto detect email column
        email_col = None
        for col in df.columns:
            sample = df[col].dropna().astype(str)
            if sample.str.contains('@').sum() > len(sample) * 0.5:
                email_col = col
                break

        if email_col:
            selected_col = st.selectbox("Email Column", df.columns.tolist(), index=df.columns.tolist().index(email_col))
        else:
            selected_col = st.selectbox("Email Column select karo", df.columns.tolist())

        # Extract valid emails
        pattern = r'^[\w\.\+\-]+@[\w\-]+(\.[\w\-]+)+$'
        raw_emails = df[selected_col].dropna().astype(str).tolist()
        emails_list = [e.strip() for e in raw_emails if re.match(pattern, e.strip())]
        invalid_count = len(raw_emails) - len(emails_list)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Rows", len(raw_emails))
        col2.metric("Valid Emails", len(emails_list), delta=f"-{invalid_count} invalid")
        col3.metric("Invalid Skip", invalid_count)

        with st.expander("Emails Preview dekhein"):
            st.write(emails_list[:10])
            if len(emails_list) > 10:
                st.caption(f"...aur {len(emails_list)-10} emails")

    except Exception as e:
        st.error(f"File error: {e}")

# ── SEND BUTTON ──
st.markdown("---")

def send_emails(gmail_addr, app_pwd, subj, msg_body, emails):
    def connect():
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(gmail_addr, app_pwd)
        return s

    server = connect()
    sent = 0
    failed = 0
    failed_list = []

    progress = st.progress(0)
    status_text = st.empty()
    results_box = st.empty()

    for i, email in enumerate(emails):
        try:
            msg = MIMEMultipart()
            msg['From'] = gmail_addr
            msg['To'] = email
            msg['Subject'] = subj
            msg.attach(MIMEText(msg_body, 'plain', 'utf-8'))

            try:
                server.send_message(msg)
            except Exception:
                try:
                    server.quit()
                except:
                    pass
                time.sleep(2)
                server = connect()
                server.send_message(msg)

            sent += 1
            status_text.success(f"[{i+1}/{len(emails)}] Sent: {email}")
            time.sleep(1.5)

        except Exception as e:
            failed += 1
            failed_list.append(email)
            status_text.error(f"[{i+1}/{len(emails)}] FAIL: {email}")

        progress.progress((i+1) / len(emails))

    try:
        server.quit()
    except:
        pass

    return sent, failed, failed_list

all_ok = gmail and app_password and subject and body and len(emails_list) > 0

if st.button("🚀 Sab Emails Bhejo!", type="primary", disabled=not all_ok, use_container_width=True):
    if not gmail or not app_password:
        st.error("Gmail aur App Password daalo sidebar mein!")
    elif not subject or not body:
        st.error("Subject aur Email Body zaroori hain!")
    elif len(emails_list) == 0:
        st.error("Koi valid email nahi mili!")
    else:
        st.info(f"Bhej raha hun {len(emails_list)} emails... (thoda waqt lagega)")
        with st.spinner("Emails ja rahi hain..."):
            sent, failed, failed_list = send_emails(gmail, app_password, subject, body, emails_list)

        st.balloons()
        st.success(f"✅ Kaam mukammal! {sent} emails bhej di gayi!")

        if failed > 0:
            st.warning(f"⚠️ {failed} emails fail ho gayi:")
            st.write(failed_list)

elif not all_ok and uploaded_file:
    missing = []
    if not gmail: missing.append("Gmail")
    if not app_password: missing.append("App Password")
    if not subject: missing.append("Subject")
    if not body: missing.append("Email Body")
    if missing:
        st.warning(f"Abhi baki hai: {', '.join(missing)}")

st.markdown("---")
st.caption("Made with ❤️ | Bulk Email Sender")
