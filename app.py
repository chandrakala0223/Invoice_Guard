import json
import requests
import streamlit as st
from google import genai
from google.genai import types
from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT
)

st.set_page_config(
    page_title="InvoiceGuard",
    page_icon="🧾",
    layout="centered"
)

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
MODEL_NAME = "gemini-2.5-flash"


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


def extract_document(uploaded_file):
    prompt = """
Read the uploaded business document and extract its information.

Return only valid JSON in this structure:
{
    "document_type": "purchase_order or invoice or unknown",
    "supplier_name": null,
    "document_number": null,
    "date": null,
    "items": [
        {
            "description": null,
            "quantity": null,
            "unit_price": null,
            "amount": null
        }
    ],
    "subtotal": null,
    "tax": null,
    "total": null
}

Rules:
- Identify whether this is a purchase order or supplier invoice.
- Do not invent missing values.
- Use null for missing or unclear values.
- Keep item descriptions as written in the document.
- Return quantities and money as numbers.
- Do not include currency symbols inside numeric values.
- Return JSON only, without markdown.
"""

    document_part = types.Part.from_bytes(
        data=uploaded_file.getvalue(),
        mime_type=uploaded_file.type
    )

    response = gemini_client.models.generate_content(
        model=MODEL_NAME,
        contents=[prompt, document_part],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json"
        )
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return json.loads(response.text)


def normalize_document_type(document_type):
    value = str(document_type or "").strip().lower().replace(" ", "_")

    if value in ["purchase_order", "po"]:
        return "purchase_order"

    if value in ["invoice", "supplier_invoice"]:
        return "invoice"

    return "unknown"


def verify_invoice(invoice, purchase_order):
    issues = []
    invoice_items = invoice.get("items") or []
    po_items = purchase_order.get("items") or []
    matched_po_indexes = set()

    for invoice_item in invoice_items:
        description = invoice_item.get("description") or "Unknown"
        normalized_description = str(description).strip().lower()

        matching_index = next(
            (
                index for index, po_item in enumerate(po_items)
                if str(po_item.get("description") or "").strip().lower()
                == normalized_description
            ),
            None
        )

        if matching_index is None:
            issues.append(
                f"Extra item on invoice: '{description}' was not found in the purchase order."
            )
            continue

        matched_po_indexes.add(matching_index)
        po_item = po_items[matching_index]

        invoice_quantity = invoice_item.get("quantity")
        po_quantity = po_item.get("quantity")

        if invoice_quantity is None or po_quantity is None:
            issues.append(
                f"{description}: quantity could not be verified."
            )
        elif invoice_quantity != po_quantity:
            issues.append(
                f"{description}: quantity differs. "
                f"PO: {po_quantity}, Invoice: {invoice_quantity}."
            )

        invoice_price = invoice_item.get("unit_price")
        po_price = po_item.get("unit_price")

        if invoice_price is None or po_price is None:
            issues.append(
                f"{description}: unit price could not be verified."
            )
        elif invoice_price != po_price:
            issues.append(
                f"{description}: unit price differs. "
                f"PO: ₹{po_price}, Invoice: ₹{invoice_price}."
            )

    for index, po_item in enumerate(po_items):
        if index not in matched_po_indexes:
            description = po_item.get("description") or "Unknown"
            issues.append(
                f"Item '{description}' from the purchase order was not found in the invoice."
            )

    if not invoice_items:
        issues.append("No invoice line items could be verified.")

    if not po_items:
        issues.append("No purchase order line items could be verified.")

    po_total = purchase_order.get("total")
    invoice_total = invoice.get("total")

    if po_total is None or invoice_total is None:
        issues.append("One or both document totals are missing or unclear.")
    elif po_total != invoice_total:
        issues.append(
            f"Document totals differ. PO total: ₹{po_total}, "
            f"Invoice total: ₹{invoice_total}."
        )

    status = "Review Required" if issues else "No Mismatches Found"

    return status, issues


def create_report(invoice, purchase_order, status, issues):
    invoice_total = invoice.get("total")
    po_total = purchase_order.get("total")

    report = (
        "🧾 InvoiceGuard Verification Report\n\n"
        f"Supplier: {invoice.get('supplier_name') or 'Not available'}\n"
        f"Invoice Number: {invoice.get('document_number') or 'Not available'}\n"
        f"PO Number: {purchase_order.get('document_number') or 'Not available'}\n"
        f"PO Total: {f'₹{po_total}' if po_total is not None else 'Not available'}\n"
        f"Invoice Total: {f'₹{invoice_total}' if invoice_total is not None else 'Not available'}\n"
        f"Status: {status}\n"
    )

    if issues:
        report += "\nDifferences requiring review:\n"
        for issue in issues:
            report += f"- {issue}\n"
    else:
        report += (
            "\nNo differences were found in the checked item descriptions, "
            "quantities, unit prices, and totals."
        )

    report += "\n\nPlease review the documents before processing payment."

    return report


def create_telegram_summary(report):
    response = gemini_client.models.generate_content(
        model=MODEL_NAME,
        contents=SUMMARY_REQUEST_PROMPT + "\n\n" + report,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )
    )

    if not response.text:
        raise ValueError("Gemini could not create the Telegram summary.")

    return response.text.strip()


def send_telegram(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message[:4000]
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=15
        )

        result = response.json()

        if response.ok and result.get("ok"):
            return True, "Report sent successfully."

        return False, result.get(
            "description",
            "Telegram message failed."
        )

    except requests.RequestException as error:
        return False, str(error)


def process_documents(uploaded_files):
    if len(uploaded_files) != 2:
        raise ValueError(
            "Please upload exactly two files: one Purchase Order and one Supplier Invoice."
        )

    documents = []

    for uploaded_file in uploaded_files:
        with st.spinner(f"Reading {uploaded_file.name}..."):
            documents.append(extract_document(uploaded_file))

    purchase_order = None
    invoice = None

    for document in documents:
        document_type = normalize_document_type(
            document.get("document_type")
        )

        if document_type == "purchase_order":
            purchase_order = document
        elif document_type == "invoice":
            invoice = document

    if purchase_order is None or invoice is None:
        raise ValueError(
            "I couldn't identify both documents. Please upload one Purchase Order and one Supplier Invoice."
        )

    with st.spinner("Comparing the documents..."):
        status, issues = verify_invoice(invoice, purchase_order)

    report = create_report(
        invoice,
        purchase_order,
        status,
        issues
    )

    return invoice, purchase_order, status, issues, report


if "onboarded" not in st.session_state:
    st.title("🧾 InvoiceGuard")
    st.caption("Check invoices. Find discrepancies. Review before payment.")

    with st.form("onboarding_form"):
        name = st.text_input("Your name")
        chat_id = st.text_input("Telegram Chat ID")
        submitted = st.form_submit_button("Let's get started")

    if submitted:
        if not name.strip() or not chat_id.strip():
            st.warning("Please enter both your name and Telegram Chat ID.")
        else:
            st.session_state.name = name.strip()
            st.session_state.telegram_chat_id = chat_id.strip()
            st.session_state.onboarded = True
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": WELCOME_MESSAGE_TEMPLATE.format(
                        name=name.strip()
                    )
                }
            ]
            st.rerun()

    st.stop()


st.title("🧾 InvoiceGuard")
st.caption("Your invoice verification assistant")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": WELCOME_MESSAGE_TEMPLATE.format(
                name=st.session_state.name
            )
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


user_input = st.chat_input(
    "Ask InvoiceGuard or attach your documents...",
    accept_file="multiple",
    file_type=["pdf", "png", "jpg", "jpeg"]
)


if user_input is not None:
    message_text = user_input.text or ""
    uploaded_files = user_input.files or []

    if not uploaded_files and not message_text.strip():
        st.stop()

    if message_text.strip():
        st.session_state.messages.append(
            {
                "role": "user",
                "content": message_text
            }
        )
        with st.chat_message("user"):
            st.write(message_text)

    if uploaded_files:
        file_names = ", ".join(
            uploaded_file.name for uploaded_file in uploaded_files
        )

        if not message_text.strip():
            display_message = f"Uploaded documents: {file_names}"
        else:
            display_message = f"{message_text}\n\nUploaded documents: {file_names}"

        if message_text.strip():
            st.session_state.messages[-1]["content"] = display_message
        else:
            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": display_message
                }
            )

        if not message_text.strip():
            with st.chat_message("user"):
                st.write(display_message)

        with st.chat_message("assistant"):
            try:
                (
                    invoice,
                    purchase_order,
                    status,
                    issues,
                    report
                ) = process_documents(uploaded_files)

                st.markdown("### Verification Result")

                if status == "Review Required":
                    st.warning(status)
                else:
                    st.success(status)

                st.write(report)

                with st.expander("View extracted invoice details"):
                    st.json(invoice)

                with st.expander("View extracted purchase order details"):
                    st.json(purchase_order)

                with st.spinner("Preparing Telegram summary..."):
                    try:
                        telegram_message = create_telegram_summary(report)
                    except Exception:
                        telegram_message = report

                with st.spinner("Sending report to Telegram..."):
                    success, info = send_telegram(
                        st.session_state.telegram_chat_id,
                        telegram_message
                    )

                if success:
                    st.success("Verification summary sent to Telegram automatically.")
                    assistant_message = (
                        report + "\n\nTelegram notification sent."
                    )
                else:
                    st.error(f"Telegram sending failed: {info}")
                    assistant_message = (
                        report + f"\n\nTelegram sending failed: {info}"
                    )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_message
                    }
                )

            except Exception as error:
                error_message = f"Could not process the documents: {error}"
                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message
                    }
                )

    elif message_text.strip():
        with st.chat_message("assistant"):
            st.write(
                "Please attach both a Purchase Order and a Supplier Invoice "
                "so I can verify them."
            )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Please attach both a Purchase Order and a Supplier Invoice "
                    "so I can verify them."
                )
            }
        )