# 📧 Email Endpoint Testing Guide

Complete guide for testing the HomeWiz email endpoint with multiple methods.

## 🎯 Overview

The email endpoint (`POST /query/email`) processes natural language queries and returns **HTML-formatted email responses** suitable for sending via Gmail, Outlook, or other email clients.

**Endpoint:** `http://localhost:8002/query/email`

---

## ✅ Prerequisites

1. **Backend Running**: Make sure the backend server is running on port 8002
2. **Environment Variables**: Ensure `.env` file is configured with:
   - `GEMINI_API_KEY`
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### Check if Backend is Running

```bash
curl http://localhost:8002/
# Should return: {"message":"HomeWiz Backend API is running"}
```

### Start Backend (if not running)

```bash
cd backend
export $(cat .env | xargs)
python3 start_backend.py
```

---

## 🧪 Method 1: Using the Shell Script (Easiest) ⭐

The project includes a ready-to-use test script that handles everything automatically.

```bash
cd backend
bash test_email_endpoint.sh
```

**What it does:**
- ✅ Loads environment variables
- ✅ Starts the backend (if needed)
- ✅ Sends a test query
- ✅ Formats the JSON response nicely

**Sample Query:** "Show me cat-friendly units in San Francisco under $1500"

---

## 🧪 Method 2: Using cURL (Manual Testing)

Test the endpoint directly with cURL for custom queries.

### Basic Test

```bash
curl -X POST http://localhost:8002/query/email \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me cat-friendly units in San Francisco under $1500",
    "user_context": {
      "permissions": ["lead"],
      "role": "lead"
    }
  }' | jq '.'
```

### Custom Query Examples

**Find Available Rooms:**
```bash
curl -X POST http://localhost:8002/query/email \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find available rooms under $1200",
    "user_context": {
      "permissions": ["basic"],
      "role": "user"
    }
  }' | jq '.result.response'
```

**Analytics Query:**
```bash
curl -X POST http://localhost:8002/query/email \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me occupancy statistics for all buildings",
    "user_context": {
      "permissions": ["manager"],
      "role": "manager"
    }
  }' | jq '.'
```

**Maintenance Requests:**
```bash
curl -X POST http://localhost:8002/query/email \
  -H "Content-Type: application/json" \
  -d '{
    "query": "List all pending maintenance requests",
    "user_context": {
      "permissions": ["manager"],
      "role": "manager"
    }
  }' | jq '.'
```

---

## 🧪 Method 3: Test Email Formatter (Preview HTML)

Test the email formatting without hitting the full endpoint.

```bash
cd backend
python3 test_email_formatter.py
```

**What it does:**
- ✅ Generates sample email HTML
- ✅ Saves to `test_email_output.html`
- ✅ Shows both EMAIL and WEB formats for comparison

**Output Files:**
- `test_email_output.html` - Open in browser to preview

---

## 🧪 Method 4: Generate Sample Email

Create a standalone sample email for testing.

```bash
python3 simple_test_email.py
```

**Output:**
- `sample_email_output.html` - Sample email preview

---

## 📨 Sending Test Emails

### Option A: Save as .eml File (Open in Mail Client)

```bash
cd backend
python3 save_email_file.py
```

**What it does:**
- ✅ Creates `test_email.eml` file
- ✅ Opens in your default mail client (Mail.app on macOS, Outlook on Windows)
- ✅ You can forward/send the email from there

### Option B: Send via Gmail SMTP

```bash
cd backend
python3 send_email_easy.py YOUR_EMAIL@gmail.com
```

**Requirements:**
- Gmail account
- Gmail App Password (not your regular password)
- Get App Password: https://myaccount.google.com/apppasswords

**Example:**
```bash
python3 send_email_easy.py myemail@gmail.com
```

---

## 📊 Understanding the Response

### Response Structure

```json
{
  "success": true,
  "function_called": "universal_query_function",
  "result": {
    "success": true,
    "response": "<p>HTML email content here...</p>",
    "data": [...],
    "metadata": {
      "sql_query": "SELECT ...",
      "row_count": 20,
      "result_type": "property_search",
      "execution_time": 2.74
    }
  },
  "confidence": 0.95
}
```

### Key Fields

- **`result.response`**: HTML-formatted email body (ready to send)
- **`result.data`**: Structured JSON data
- **`result.metadata`**: Query execution details
- **`confidence`**: AI confidence score (0-1)

### Extract Just the HTML

```bash
curl -X POST http://localhost:8002/query/email \
  -H "Content-Type: application/json" \
  -d '{"query": "Find rooms", "user_context": {"permissions": ["basic"], "role": "user"}}' \
  | jq -r '.result.response' > email_body.html
```

---

## 🎨 Email Format Features

The email endpoint returns **professional HTML emails** with:

✅ **Clean HTML** (no markdown)
✅ **Inline CSS** (email client compatible)
✅ **Clickable building links** (if image URLs exist)
✅ **Professional tables** for data
✅ **Responsive design**
✅ **Gmail/Outlook compatible**

### Sample Email Structure

```html
<p>Thank you for your inquiry...</p>

<h2>Summary</h2>
<p>We found <strong>4 available rooms</strong>...</p>

<h2>Key Results</h2>
<ul>
  <li><strong>Building - Room</strong>: Details...</li>
</ul>

<table>
  <thead>
    <tr><th>Room</th><th>Rent</th><th>Status</th></tr>
  </thead>
  <tbody>
    <tr><td>Room 1</td><td>$995</td><td>Available</td></tr>
  </tbody>
</table>

<p>Best regards,<br>HomeWiz Team</p>
```

---

## 🔧 Troubleshooting

### Backend Not Running

```bash
# Check if backend is running
curl http://localhost:8002/

# If not, start it
cd backend
export $(cat .env | xargs)
python3 start_backend.py
```

### Environment Variables Not Loaded

```bash
# Load manually
cd backend
export $(cat .env | xargs)
```

### Missing Dependencies

```bash
pip3 install supabase fastapi uvicorn python-dotenv google-genai
```

### Port Already in Use

```bash
# Find process using port 8002
lsof -i :8002

# Kill it
kill -9 <PID>
```

---

## 📝 Testing Checklist

- [ ] Backend is running on port 8002
- [ ] Environment variables are loaded
- [ ] Test with shell script works
- [ ] cURL test returns HTML response
- [ ] HTML preview looks good in browser
- [ ] Email can be saved as .eml file
- [ ] Email can be sent via SMTP (optional)

---

## 🚀 Next Steps

1. **Test different queries** to see various email formats
2. **Integrate with your email service** (SendGrid, AWS SES, etc.)
3. **Customize email templates** in `text_response_formatter.py`
4. **Add email tracking** (open rates, click rates)
5. **Set up automated email campaigns**

---

## 📚 Related Files

- `backend/test_email_endpoint.sh` - Shell test script
- `backend/test_email_formatter.py` - Email formatter tester
- `backend/send_email_easy.py` - Gmail SMTP sender
- `backend/save_email_file.py` - .eml file generator
- `backend/app/endpoints/query.py` - Email endpoint implementation
- `backend/app/ai_services/text_response_formatter.py` - Email formatter

---

**Happy Testing! 📧✨**

