# Analytics Integration - Deployment Update

## ✅ Changes Made

### 1. **Updated `main.py`**
Added complete analytics integration:
- ✅ Import analytics routers and database manager
- ✅ Database initialization on startup
- ✅ Analytics API routes enabled (`/analytics/*`)
- ✅ Webhook routes enabled (`/webhooks/shopify/*`)
- ✅ CORS middleware for dashboard access
- ✅ Updated root endpoint to show features

### 2. **Updated `requirements.txt`**
Added new dependencies for Railway Docker build:
- ✅ `sqlalchemy>=2.0.0` - Database ORM
- ✅ `psycopg2-binary>=2.9.9` - PostgreSQL driver

### 3. **Analytics Module**
Already in place at `behold_agent/analytics/`:
- ✅ 7 Python files (database, tracking, webhooks, etc.)
- ✅ Complete BI system ready to use

---

## 🚀 Next Steps for Deployment

### **1. Add PostgreSQL to Railway**
```
Railway Dashboard → Your Project → "New" → "Database" → "Add PostgreSQL"
```

### **2. Set Environment Variables**
Add these in Railway:
```env
# Database (Railway provides automatically)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Webhooks (get from Shopify after creating webhook)
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret
APP_URL=${{RAILWAY_PUBLIC_DOMAIN}}

# Optional
SQL_ECHO=false
```

### **3. Deploy**
Push to GitHub or redeploy in Railway dashboard.

Railway will:
1. Build Docker image with new requirements.txt
2. Install SQLAlchemy and psycopg2
3. Start app with analytics enabled
4. Create database tables automatically

### **4. Verify Deployment**
Check Railway logs for:
```
INFO - ✅ Analytics system loaded successfully
INFO - Creating database tables...
INFO - Database initialized successfully
INFO - ✅ Analytics routes enabled
INFO - ✅ Webhook routes enabled
```

Test endpoints:
```bash
curl https://your-app.railway.app/
# Should show analytics features

curl https://your-app.railway.app/analytics/overview
# Should return JSON (not 404)

curl https://your-app.railway.app/webhooks/shopify/orders/create
# Should return 401 (needs valid webhook) not 404
```

---

## 🔍 What Changed in Logs

### **Before:**
```
INFO: "POST /webhooks/shopify/orders/create HTTP/1.1" 404 Not Found ❌
```

### **After:**
```
INFO - ✅ Analytics system loaded successfully
INFO - Creating database tables...
INFO - Database initialized successfully
INFO - ✅ Analytics routes enabled
INFO - ✅ Webhook routes enabled
INFO: "POST /webhooks/shopify/orders/create HTTP/1.1" 401 Unauthorized ✅
# (401 is correct - means endpoint exists, needs valid signature)
```

---

## 📊 Available Endpoints After Deploy

### **Analytics API:**
- `GET /analytics/overview` - Dashboard metrics
- `GET /analytics/revenue/daily` - Revenue breakdown
- `GET /analytics/products/top` - Best sellers
- `GET /analytics/funnel` - Conversion funnel
- `GET /analytics/agent/performance` - Agent metrics
- `GET /analytics/users/engagement` - User behavior
- `GET /analytics/setup/webhooks` - Setup guide

### **Webhooks:**
- `POST /webhooks/shopify/orders/create` - Order completion
- `POST /webhooks/shopify/carts/create` - Cart creation (optional)

### **Health:**
- `GET /` - App info with features list
- `GET /health` - Health check
- `GET /docs` - Interactive API docs

---

## 🐛 Troubleshooting

### **"Analytics system not available" in logs**
**Cause:** Import error (missing dependencies or analytics folder)

**Fix:**
1. Verify `analytics/` folder exists in deployment
2. Check requirements.txt has sqlalchemy and psycopg2
3. Rebuild Docker image in Railway

### **"Failed to initialize database"**
**Cause:** DATABASE_URL not set or PostgreSQL not added

**Fix:**
1. Add PostgreSQL database in Railway
2. Set `DATABASE_URL=${{Postgres.DATABASE_URL}}`
3. Redeploy

### **Webhook still returns 404**
**Cause:** App not redeployed with updated main.py

**Fix:**
1. Verify changes are pushed to GitHub
2. Trigger redeploy in Railway
3. Check logs for "Webhook routes enabled"

---

## ✅ Verification Checklist

After deploying, verify:
- [ ] App starts without errors
- [ ] Logs show "Analytics system loaded successfully"
- [ ] Logs show "Database initialized successfully"
- [ ] Logs show "Analytics routes enabled"
- [ ] Logs show "Webhook routes enabled"
- [ ] `GET /` returns features list with analytics
- [ ] `GET /analytics/overview` returns JSON (not 404)
- [ ] `POST /webhooks/shopify/orders/create` returns 401 (not 404)
- [ ] `/docs` shows analytics and webhook endpoints

---

## 🎉 Success Criteria

You'll know it's working when:
1. ✅ Webhook endpoint exists (not 404)
2. ✅ Analytics API responds
3. ✅ Database tables created
4. ✅ Orders can be attributed to conversations

The 404 error will be fixed and you'll have complete business intelligence! 🚀
