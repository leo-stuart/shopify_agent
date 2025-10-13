# Quick Start: Business Intelligence Setup

⏱️ **Setup Time**: ~15 minutes

## ✅ Pre-flight Checklist

Before starting, ensure you have:
- [ ] Shopify store with Admin and Storefront API access
- [ ] WhatsApp Business integration configured
- [ ] Python 3.12+ installed
- [ ] `uv` package manager installed

---

## 🚀 5-Step Setup

### Step 1: Install Dependencies (2 min)

```bash
cd behold_agent
uv install
```

**What this does**: Installs SQLAlchemy and PostgreSQL support for analytics.

---

### Step 2: Configure Database (1 min)

Edit your `.env` file:

```env
# For development (default - works out of the box)
DATABASE_URL=sqlite:///./behold_analytics.db

# For production (recommended)
# DATABASE_URL=postgresql://user:password@host:5432/dbname

# Optional: Enable SQL query logging for debugging
SQL_ECHO=false
```

**That's it!** The database will be created automatically when you start the app.

---

### Step 3: Start the Application (1 min)

```bash
python main.py
```

**Expected output:**
```
INFO - Starting Behold WhatsApp Shopify Agent
INFO - Creating database tables...
INFO - Database initialized successfully
INFO - Application startup complete.
INFO - Uvicorn running on http://0.0.0.0:8000
```

✅ **Database is ready!**

---

### Step 4: Set Up Shopify Webhook (5 min)

#### A. Get Your Webhook Secret

1. Open your **Shopify Admin**
2. Go to: **Settings → Notifications → Webhooks**
3. Click **"Create webhook"**
4. Fill in:
   - **Event**: `Order creation`
   - **Format**: `JSON`
   - **URL**: `https://your-app.com/webhooks/shopify/orders/create`
     - For local testing: Use ngrok or similar tunnel
     - For production: Your actual app URL
   - **API Version**: `2025-01` (or latest)
5. Click **Save**
6. **Copy the Webhook Secret** that appears

#### B. Add Secret to Environment

Add to your `.env`:

```env
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret_here
APP_URL=https://your-app.com
```

Restart the app:
```bash
python main.py
```

✅ **Webhook is ready to receive orders!**

---

### Step 5: Verify Everything Works (5 min)

#### Test 1: API is Running
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"healthy",...}`

#### Test 2: Database is Initialized
```bash
sqlite3 behold_analytics.db "SELECT name FROM sqlite_master WHERE type='table';"
```
Expected: List of tables (users, conversations, orders, etc.)

#### Test 3: Analytics Endpoint Works
```bash
curl http://localhost:8000/analytics/overview
```
Expected: JSON with metrics (all zeros initially)

#### Test 4: Webhook Documentation
```bash
curl http://localhost:8000/analytics/setup/webhooks
```
Expected: Webhook setup instructions

✅ **System is operational!**

---

## 🎯 Next Steps

### Test with a Real Order

1. **Interact with your agent via WhatsApp**
   - Start a conversation
   - Search for products
   - Add items to cart
   - Get checkout URL

2. **Complete the purchase on Shopify**
   - Open the checkout URL
   - Complete the order

3. **Check analytics**
   ```bash
   curl http://localhost:8000/analytics/overview
   ```
   You should see:
   - 1 conversation
   - 1 cart created
   - 1 order completed
   - Revenue recorded

4. **Verify order attribution**
   ```bash
   sqlite3 behold_analytics.db "SELECT id, conversation_id, total_amount FROM orders;"
   ```
   You should see your order linked to the conversation!

---

## 📊 Explore Analytics Endpoints

### Overview Dashboard
```bash
curl "http://localhost:8000/analytics/overview?days=30"
```

### Daily Revenue
```bash
curl "http://localhost:8000/analytics/revenue/daily?days=7"
```

### Top Products
```bash
curl "http://localhost:8000/analytics/products/top?limit=5"
```

### Conversion Funnel
```bash
curl "http://localhost:8000/analytics/funnel?days=30"
```

### Agent Performance
```bash
curl "http://localhost:8000/analytics/agent/performance?days=30"
```

### User Engagement
```bash
curl "http://localhost:8000/analytics/users/engagement?days=30"
```

### Interactive API Docs
Open in browser: **http://localhost:8000/docs**

---

## 🔍 Verify Order Attribution

After completing a test order, check that attribution worked:

### Check Database
```bash
sqlite3 behold_analytics.db

# See conversations
SELECT id, user_id, cart_created, order_completed, total_revenue FROM conversations;

# See carts with attribution
SELECT id, conversation_id, converted_to_order FROM carts;

# See orders with attribution
SELECT id, conversation_id, order_number, total_amount FROM orders;
```

### Check API
```bash
# Get overview
curl http://localhost:8000/analytics/overview | jq

# Should show:
# - orders_completed: 1
# - total_revenue: (your order amount)
# - cart_to_order_rate: 100% (if only one test)
```

---

## 🎨 Build a Simple Dashboard (Optional)

### Create a quick HTML dashboard:

```bash
cat > dashboard.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Agent Analytics</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        .metric { display: inline-block; padding: 20px; margin: 10px;
                  border: 2px solid #4CAF50; border-radius: 8px; }
        .metric h3 { margin: 0; color: #4CAF50; }
        .metric p { margin: 5px 0; font-size: 24px; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🎯 Agent Analytics Dashboard</h1>
    <div id="metrics"></div>

    <script>
        fetch('http://localhost:8000/analytics/overview?days=30')
            .then(r => r.json())
            .then(data => {
                document.getElementById('metrics').innerHTML = `
                    <div class="metric">
                        <h3>Total Revenue</h3>
                        <p>R$ ${data.commerce.total_revenue.toFixed(2)}</p>
                    </div>
                    <div class="metric">
                        <h3>Orders</h3>
                        <p>${data.commerce.orders_completed}</p>
                    </div>
                    <div class="metric">
                        <h3>Conversion Rate</h3>
                        <p>${data.conversion.conversation_to_order_rate.toFixed(2)}%</p>
                    </div>
                    <div class="metric">
                        <h3>Avg Order Value</h3>
                        <p>R$ ${data.commerce.avg_order_value.toFixed(2)}</p>
                    </div>
                `;
            });
    </script>
</body>
</html>
EOF
```

Open `dashboard.html` in your browser!

---

## 🐛 Troubleshooting

### ❌ "Database tables not created"
**Fix**: Check if app started successfully. Look for "Database initialized successfully" in logs.

### ❌ "Orders not being attributed"
**Fix**:
1. Verify webhook is registered in Shopify Admin
2. Check `SHOPIFY_WEBHOOK_SECRET` is set in `.env`
3. Ensure cart creation includes `conversation_id` and `user_id`

### ❌ "Analytics returning all zeros"
**Fix**:
1. Make sure you've had at least one conversation
2. Check database has data: `SELECT COUNT(*) FROM conversations;`
3. Verify tracking service is being called in your code

### ❌ "Webhook not receiving orders"
**Fix**:
1. Check webhook URL is publicly accessible
2. Test webhook in Shopify Admin (Settings → Notifications → Webhooks → Test)
3. Check logs for webhook processing: `grep webhook app.log`

---

## 📚 Documentation References

- **Complete Guide**: [BUSINESS_INTELLIGENCE_GUIDE.md](BUSINESS_INTELLIGENCE_GUIDE.md)
- **Technical Docs**: [behold_agent/analytics/README.md](behold_agent/analytics/README.md)
- **Implementation Details**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

## ✅ Success Criteria

You're all set when:

- [x] App starts without errors
- [x] Database tables created
- [x] Shopify webhook registered
- [x] Test order attributed correctly
- [x] Analytics endpoints return data
- [x] You can see revenue in analytics

---

## 🎉 You're Done!

Your agent now has **complete business intelligence**:
- ✅ Sales attribution
- ✅ Revenue tracking
- ✅ Conversion analytics
- ✅ Performance metrics

**Start driving sales and track your success!** 🚀
