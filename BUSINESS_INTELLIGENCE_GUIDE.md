# Business Intelligence & Sales Attribution System

## 📋 Overview

Your Shopify agent now has **complete sales attribution and business intelligence** capabilities. You can track exactly which sales were made by the agent and get detailed analytics on performance, revenue, conversion rates, and customer behavior.

## 🎯 What Problems This Solves

### Before:
- ❌ No way to know if a sale came from the agent
- ❌ No visibility into agent effectiveness
- ❌ No data on customer journey or conversion rates
- ❌ No product performance insights
- ❌ No ROI metrics for the agent

### After:
- ✅ Every order is attributed to agent conversations
- ✅ Complete analytics dashboard with all key metrics
- ✅ Conversion funnel tracking (message → search → cart → order)
- ✅ Product performance insights
- ✅ Revenue tracking and ROI calculation

---

## 🏗️ System Architecture

### 1. **Cart Attribution System**
When the agent creates a cart for a customer, it automatically tags it with:
- `_agent_conversation_id` - Links cart to conversation
- `_agent_user_id` - Links cart to WhatsApp user
- `_agent_source` - Identifies as agent-created

**When the customer completes checkout on Shopify:**
→ These tags are preserved in the order
→ Webhook sends order data to your system
→ Order is automatically attributed to the agent conversation

### 2. **Database Tracking**
All data is stored in a relational database (SQLite for dev, PostgreSQL for production):

**Tables:**
- `users` - WhatsApp users
- `conversations` - Chat sessions with metrics
- `messages` - All messages exchanged
- `agent_actions` - Every tool the agent uses
- `carts` - Carts created with attribution
- `orders` - Completed orders from Shopify
- `product_views` - Products shown to users

### 3. **Analytics Service**
Generates business intelligence from the tracked data:
- Revenue metrics
- Conversion rates
- Product performance
- Agent effectiveness
- User behavior patterns

### 4. **API Endpoints**
REST API for querying analytics:
- `/analytics/overview` - Dashboard summary
- `/analytics/revenue/daily` - Revenue breakdown
- `/analytics/products/top` - Best sellers
- `/analytics/funnel` - Conversion funnel
- `/analytics/agent/performance` - Agent metrics

---

## 🚀 Setup Instructions

### Step 1: Install Dependencies

```bash
cd behold_agent
uv install
```

New dependencies added:
- `sqlalchemy>=2.0.0` - Database ORM
- `psycopg2-binary>=2.9.9` - PostgreSQL support

### Step 2: Configure Environment

Add to your `.env`:

```env
# Database (SQLite for development)
DATABASE_URL=sqlite:///./behold_analytics.db

# For production, use PostgreSQL:
# DATABASE_URL=postgresql://user:password@host:5432/dbname

# Shopify Webhook Configuration
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret
APP_URL=https://your-app.com
```

### Step 3: Initialize Database

The database is **automatically initialized** when you start the app:

```bash
python main.py
```

You'll see:
```
INFO - Creating database tables...
INFO - Database initialized successfully
```

### Step 4: Set Up Shopify Webhook

This is **critical** for order attribution!

#### Option A: Via Shopify Admin (Recommended)
1. Go to your Shopify Admin
2. Navigate to: **Settings → Notifications → Webhooks**
3. Click **"Create webhook"**
4. Configure:
   - **Event**: `Order creation`
   - **Format**: `JSON`
   - **URL**: `https://your-app.com/webhooks/shopify/orders/create`
   - **API Version**: `2025-01` or latest

5. Click **Save**
6. Copy the **Webhook Secret** shown
7. Add to your `.env` as `SHOPIFY_WEBHOOK_SECRET`

#### Option B: Get Setup Instructions from API
```bash
GET https://your-app.com/analytics/setup/webhooks
```

### Step 5: Verify Setup

1. **Test the webhook endpoint:**
```bash
curl http://localhost:8000/health
```

2. **Check analytics (should be empty initially):**
```bash
curl http://localhost:8000/analytics/overview
```

3. **View API documentation:**
Open browser: `http://localhost:8000/docs`

---

## 📊 How It Works - Complete Flow

### Scenario: Customer buys a product through the agent

**1. Customer starts conversation**
```
Customer: "Olá, quero comprar um tênis"
```
→ System creates `Conversation` record
→ Stores message in `messages` table

**2. Agent searches for products**
```python
agent calls: execute_shopify_operation('search products', {'query': 'tenis'})
```
→ Logged as `AgentAction` (type: 'search_products')
→ Products shown are recorded in `product_views`
→ Conversation metrics updated: `products_searched += 1`

**3. Customer picks a product**
```
Customer: "Quero o vermelho"
```
→ Agent identifies product
→ Records product view with `recommended_by_agent=True`
→ Conversation metrics updated: `products_viewed += 1`

**4. Agent creates cart**
```python
agent calls: execute_shopify_operation('create cart', {
    'lines': [...],
    'conversation_id': 'session_123',  # Attribution!
    'user_id': 'whatsapp_user_456'     # Attribution!
})
```
→ Cart created in Shopify **with attribution tags**
→ Recorded in `carts` table with `conversation_id`
→ Logged as `AgentAction` (type: 'create_cart')
→ Conversation updated: `cart_created = True`

**5. Agent provides checkout URL**
```
Agent: "Pronto! Tênis vermelho adicionado. Total: R$ 299,90
https://store.myshopify.com/cart/c/abc123"
```
→ Customer receives checkout link
→ Conversation updated: `checkout_initiated = True`

**6. Customer completes purchase on Shopify**
→ Shopify creates order
→ **Cart attributes are copied to order**
→ Shopify sends webhook to `/webhooks/shopify/orders/create`

**7. Your system receives webhook**
```python
# webhook_handler.py processes the order
attribution = extract_attribution_from_order(order_data)
# Returns:
# {
#   "conversation_id": "session_123",
#   "user_id": "whatsapp_user_456",
#   "is_agent_attributed": True
# }
```
→ Creates `Order` record linked to conversation
→ Updates conversation: `order_completed = True`, `total_revenue += 299.90`
→ Marks cart as `converted_to_order = True`
→ Marks product views as `purchased = True`

**8. Merchant views analytics**
```bash
GET /analytics/overview
```
→ Sees: 1 order, R$ 299.90 revenue, attributed to agent
→ Can see full conversion funnel
→ Can see which products are best sellers

---

## 📈 Using the Analytics API

### Overview Metrics
Get high-level dashboard metrics:

```bash
curl "http://localhost:8000/analytics/overview?days=30"
```

Response:
```json
{
  "period": {
    "start_date": "2025-09-13",
    "end_date": "2025-10-12",
    "days": 30
  },
  "conversations": {
    "total": 127,
    "unique_users": 98,
    "total_messages": 512,
    "avg_messages_per_conversation": 4.03
  },
  "commerce": {
    "carts_created": 34,
    "orders_completed": 9,
    "total_revenue": 2847.50,
    "avg_order_value": 316.39
  },
  "conversion": {
    "cart_to_order_rate": 26.47,
    "conversation_to_order_rate": 7.09
  }
}
```

### Daily Revenue Breakdown
Track revenue over time:

```bash
curl "http://localhost:8000/analytics/revenue/daily?days=7"
```

Response:
```json
{
  "period": {...},
  "daily_revenue": [
    {"date": "2025-10-06", "order_count": 2, "revenue": 458.90},
    {"date": "2025-10-07", "order_count": 1, "revenue": 299.90},
    {"date": "2025-10-08", "order_count": 0, "revenue": 0},
    {"date": "2025-10-09", "order_count": 3, "revenue": 987.60}
  ]
}
```

### Top Products
See which products are best sellers:

```bash
curl "http://localhost:8000/analytics/products/top?limit=5"
```

Response:
```json
{
  "period": {...},
  "top_products": [
    {
      "product_id": "gid://shopify/Product/123",
      "product_title": "Tênis Vermelho",
      "views": 45,
      "cart_adds": 12,
      "purchases": 8,
      "conversion_rate": 17.78
    },
    ...
  ]
}
```

### Conversion Funnel
See drop-off at each stage:

```bash
curl "http://localhost:8000/analytics/funnel?days=30"
```

Response:
```json
{
  "funnel_stages": [
    {"stage": "Conversation Started", "count": 127, "percentage": 100.0, "drop_off": 0},
    {"stage": "Product Search", "count": 89, "percentage": 70.08, "drop_off": 38},
    {"stage": "Product Viewed", "count": 67, "percentage": 52.76, "drop_off": 22},
    {"stage": "Cart Created", "count": 34, "percentage": 26.77, "drop_off": 33},
    {"stage": "Checkout Initiated", "count": 34, "percentage": 26.77, "drop_off": 0},
    {"stage": "Order Completed", "count": 9, "percentage": 7.09, "drop_off": 25}
  ],
  "overall_conversion_rate": 7.09
}
```

### Agent Performance
Monitor agent effectiveness:

```bash
curl "http://localhost:8000/analytics/agent/performance?days=30"
```

Response:
```json
{
  "actions": {
    "total_actions": 456,
    "successful_actions": 447,
    "success_rate": 98.03,
    "failed_actions": 9
  },
  "performance": {
    "avg_response_time_ms": 234.56
  },
  "top_actions": [
    {"action_type": "search_products", "count": 156},
    {"action_type": "create_cart", "count": 34},
    {"action_type": "get_shipping", "count": 28}
  ]
}
```

---

## 🎨 Building a Dashboard

You can build a merchant dashboard using any frontend framework:

### Option 1: Simple HTML + JavaScript
```html
<!DOCTYPE html>
<html>
<head>
    <title>Agent Analytics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <h1>Sales Dashboard</h1>
    <div id="metrics"></div>
    <canvas id="revenueChart"></canvas>

    <script>
        // Fetch overview metrics
        fetch('http://localhost:8000/analytics/overview?days=30')
            .then(r => r.json())
            .then(data => {
                document.getElementById('metrics').innerHTML = `
                    <h2>Total Revenue: R$ ${data.commerce.total_revenue}</h2>
                    <p>Orders: ${data.commerce.orders_completed}</p>
                    <p>Conversion Rate: ${data.conversion.conversation_to_order_rate}%</p>
                `;
            });

        // Fetch and chart daily revenue
        fetch('http://localhost:8000/analytics/revenue/daily?days=30')
            .then(r => r.json())
            .then(data => {
                const ctx = document.getElementById('revenueChart').getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.daily_revenue.map(d => d.date),
                        datasets: [{
                            label: 'Daily Revenue',
                            data: data.daily_revenue.map(d => d.revenue),
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }]
                    }
                });
            });
    </script>
</body>
</html>
```

### Option 2: Python Streamlit (Quickest)
```python
# dashboard.py
import streamlit as st
import requests
import pandas as pd

st.title("Agent Analytics Dashboard")

# Fetch metrics
response = requests.get("http://localhost:8000/analytics/overview?days=30")
data = response.json()

# Display metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"R$ {data['commerce']['total_revenue']:.2f}")
col2.metric("Orders", data['commerce']['orders_completed'])
col3.metric("Conversion Rate", f"{data['conversion']['conversation_to_order_rate']:.2f}%")

# Revenue chart
revenue_data = requests.get("http://localhost:8000/analytics/revenue/daily?days=30").json()
df = pd.DataFrame(revenue_data['daily_revenue'])
st.line_chart(df.set_index('date')['revenue'])
```

Run: `streamlit run dashboard.py`

---

## 🔍 Querying the Database Directly

For custom queries, access the database directly:

```python
from analytics import db_manager

session = db_manager.get_session()

# Get total revenue
from analytics import Order
from sqlalchemy import func

total = session.query(func.sum(Order.total_amount)).scalar()
print(f"Total revenue: R$ {total}")

# Get best customer
from analytics import User, Conversation
top_customer = session.query(
    User.id,
    func.sum(Conversation.total_revenue).label('revenue')
).join(Conversation).group_by(User.id).order_by('revenue DESC').first()
print(f"Top customer: {top_customer.id}, R$ {top_customer.revenue}")
```

---

## 🎯 Key Metrics Explained

### Conversion Rates
- **Cart-to-Order Rate**: % of carts that became orders (target: >20%)
- **Conversation-to-Order Rate**: % of chats that led to sales (target: >5%)

### Agent Performance
- **Action Success Rate**: % of agent actions that succeeded (target: >95%)
- **Average Response Time**: How fast agent responds (target: <500ms)

### Product Performance
- **View-to-Purchase Rate**: Product conversion rate (target: >10%)
- **Cart Add Rate**: % of views that add to cart (target: >30%)

---

## 🚨 Troubleshooting

### Orders not being attributed?

**Check 1: Webhook registered?**
```bash
# Go to Shopify Admin → Settings → Notifications → Webhooks
# Should see: orders/create webhook with your URL
```

**Check 2: Webhook secret set?**
```bash
grep SHOPIFY_WEBHOOK_SECRET .env
# Should show: SHOPIFY_WEBHOOK_SECRET=xxx
```

**Check 3: Cart attribution enabled?**
```python
# In shopify_tool.py, verify cart creation passes conversation_id and user_id
_execute_cart_creation(lines, conversation_id="xxx", user_id="yyy")
```

**Check 4: Check logs**
```bash
# Look for webhook processing
tail -f app.log | grep webhook
```

### No data in analytics?

**Check if tracking is running:**
```bash
# Connect to database
sqlite3 behold_analytics.db

# Check for data
SELECT COUNT(*) FROM conversations;
SELECT COUNT(*) FROM orders;
```

If empty → tracking service not being called

**Check if conversations are being created:**
```python
from analytics import tracking_service

# Should be called at conversation start
tracking_service.start_conversation("session_id", "user_id")
```

---

## 📝 Next Steps

### Immediate:
1. ✅ Set up Shopify webhook (critical!)
2. ✅ Test with a real order to verify attribution
3. ✅ Check analytics endpoints return data

### Short-term:
1. Build a dashboard (Streamlit recommended for speed)
2. Set up monitoring/alerts for webhook failures
3. Add API authentication for analytics endpoints

### Long-term:
1. Migrate to PostgreSQL for production
2. Implement data retention policies
3. Add more advanced analytics (cohort analysis, LTV, etc.)
4. Create automated reports/emails for merchants

---

## 🎓 Understanding the Value

### ROI Calculation Example:

**Scenario**: You have 100 conversations per day

**Without agent:**
- Manual customer service: 100 chats × 10 min = 1000 min/day
- Cost: ~$50/day in labor
- Conversion: ~2% = 2 orders/day
- Revenue: 2 × $100 = $200/day

**With agent:**
- Automated: 100 chats × 0 min = 0 min/day
- Cost: $0/day in labor (only server costs)
- Conversion: ~7% = 7 orders/day (from analytics)
- Revenue: 7 × $100 = $700/day

**Impact:**
- **Labor savings**: $50/day = $1,500/month
- **Revenue increase**: $500/day = $15,000/month
- **Total value**: $16,500/month

You can now **prove this with data** from your analytics!

---

## 📚 Additional Resources

- [Analytics Package README](behold_agent/analytics/README.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Shopify Webhooks Guide](https://shopify.dev/docs/api/webhooks)

---

## 🤝 Support

For questions or issues:
1. Check logs: `tail -f app.log`
2. Test endpoints: `http://localhost:8000/docs`
3. Verify database: `sqlite3 behold_analytics.db`
