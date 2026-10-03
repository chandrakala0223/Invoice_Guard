# InvoiceGuard 🧾

### AI-Powered Invoice Verification and Discrepancy Detection System

InvoiceGuard is an AI-powered application that compares supplier invoices with purchase orders to identify possible discrepancies in item descriptions, quantities, prices, and totals. It uses Google Gemini to extract document information and sends a verification summary to Telegram for human review.

---

## 📌 Problem Statement

Businesses receive supplier invoices that need to be checked against their original purchase orders. Differences in item details, quantities, prices, or totals can be difficult to identify through manual verification.

InvoiceGuard simplifies this process by extracting information from both documents, comparing the details, and highlighting possible mismatches before payment processing.

## ✨ Key Features

- **Document Upload:** Upload a Supplier Invoice and Purchase Order in PDF, PNG, JPG, or JPEG format.
- **AI-Powered Extraction:** Uses Google Gemini to extract supplier name, document number, date, item descriptions, quantities, unit prices, and totals.
- **Invoice Verification:** Compares the extracted information from both documents.
- **Discrepancy Detection:** Identifies possible differences in:
  - Item descriptions
  - Quantities
  - Unit prices
  - Missing or additional items
  - Document totals
- **Verification Report:** Displays comparison results and highlights details that require attention.
- **Telegram Notifications:** Automatically sends a concise verification summary to the configured Telegram chat.
- **Interactive Interface:** Provides a user-friendly interface built with Streamlit.

## 🧪 Sample Documents for Testing

Use the following sample documents to test InvoiceGuard. Upload the Supplier Invoice and its corresponding Purchase Order together.

### 1. Sample Supplier Invoice

![Sample Supplier Invoice](https://github.com/user-attachments/assets/8639a0ed-6678-46f1-b0c7-b5f3240bf32b)

[View Sample Supplier Invoice](https://github.com/user-attachments/assets/8639a0ed-6678-46f1-b0c7-b5f3240bf32b)

### 2. Sample Purchase Order

![Sample Purchase Order](https://github.com/user-attachments/assets/8a968100-60e4-4676-93ed-5670f473d200)

[View Sample Purchase Order](https://github.com/user-attachments/assets/8a968100-60e4-4676-93ed-5670f473d200)

## 🔄 How It Works

1. The user opens InvoiceGuard and enters their name and Telegram Chat ID.
2. The user uploads a Supplier Invoice and its corresponding Purchase Order.
3. Google Gemini extracts the relevant information from both documents.
4. InvoiceGuard compares the extracted details.
5. The application generates a verification report highlighting possible discrepancies.
6. A summary of the report is automatically sent to the configured Telegram chat.
7. The user reviews the findings before taking any payment-related action.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Web application interface |
| Google Gemini API | Document information extraction and summary generation |
| Telegram Bot API | Sending verification reports |
| Requests | HTTP requests to Telegram |
| JSON | Handling extracted document data |

## 📂 Project Structure

```text
Invoice_Guard/
│
├── .streamlit/
│   └── secrets.toml
│
├── app.py
├── prompts.py
├── requirements.txt
├── .gitignore
└── README.md
```

### File Description

- `app.py` — Contains the Streamlit application, document processing, verification logic, report generation, and Telegram integration.
- `prompts.py` — Contains the AI system instructions, welcome message, and Telegram summary prompt.
- `requirements.txt` — Lists the Python dependencies.
- `.streamlit/secrets.toml` — Stores API credentials locally. This file must not be uploaded to GitHub.
- `.gitignore` — Excludes sensitive files and unnecessary folders from Git.

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/chandrakala0223/Invoice_Guard.git
cd Invoice_Guard
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Credentials

Create a folder named `.streamlit` in the project directory. Inside it, create a file named `secrets.toml`.

Add your credentials:

```toml
GEMINI_API_KEY = "your_gemini_api_key"
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
```

Replace the placeholder values with your own credentials.

**Important:** Never upload `secrets.toml` or share your API keys and Telegram bot token publicly.

### 5. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser.

## 🔐 API Configuration

### Google Gemini API

InvoiceGuard uses the Google Gemini API to extract information from uploaded documents and generate concise verification summaries.

Get an API key from [Google AI Studio](https://aistudio.google.com/).

### Telegram Bot

InvoiceGuard uses a Telegram bot to send verification summaries.

1. Create a bot using [BotFather](https://t.me/BotFather).
2. Copy the bot token.
3. Start a conversation with your bot.
4. Obtain your Telegram Chat ID.
5. Add the bot token to `.streamlit/secrets.toml`.
6. Enter your Chat ID in the application.

## 🚀 Deployment

InvoiceGuard can be deployed using [Streamlit Community Cloud](https://share.streamlit.io/).

1. Connect your GitHub repository.
2. Select the `main` branch.
3. Set the main file path to `app.py`.
4. Add `GEMINI_API_KEY` and `TELEGRAM_BOT_TOKEN` in the app's Secrets settings.
5. Deploy the application.

Do not commit API credentials to the repository.

## ⚠️ Important Note

InvoiceGuard is an invoice verification assistant, not an automated payment approval system. Its findings are intended for human review before any payment decision. The accuracy of extracted information depends on the quality and readability of the uploaded documents.

## 👩‍💻 Project Information

- **Project Name:** InvoiceGuard
- **Category:** AI-Powered Invoice Verification
- **GitHub Repository:** [Invoice_Guard](https://github.com/chandrakala0223/Invoice_Guard)
