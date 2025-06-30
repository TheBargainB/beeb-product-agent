# Deploying Product Retrieval Agent to LangGraph Platform

This guide explains how to deploy your product retrieval agent to LangGraph Platform Cloud SaaS.

## ✅ **Prerequisites Complete**

Your agent is ready for deployment:
- ✅ LangGraph API runs locally (`langgraph dev` works)
- ✅ `langgraph.json` configuration file created
- ✅ All dependencies specified in `pyproject.toml`
- ✅ Environment variables properly configured
- ✅ Comprehensive testing completed

## 🚀 **Deployment Steps**

### 1. **Push to GitHub**

First, ensure your code is in a GitHub repository:

```bash
# If not already a git repo
git init
git add .
git commit -m "Add product retrieval agent"

# Create GitHub repo and push
git remote add origin https://github.com/yourusername/your-repo-name.git
git branch -M main
git push -u origin main
```

### 2. **Create Deployment on LangGraph Platform**

1. **Access LangSmith UI**
   - Go to [LangSmith](https://smith.langchain.com)
   - Navigate to **LangGraph Platform** in the left panel

2. **Create New Deployment**
   - Click **+ New Deployment** (top-right corner)
   - Fill out the deployment form:

#### **Deployment Configuration**

| Field | Value |
|-------|-------|
| **Import Method** | Import from GitHub |
| **Repository** | Your GitHub repository |
| **Deployment Name** | `product-retrieval-agent` |
| **Git Branch** | `main` |
| **Config File Path** | `langgraph.json` |
| **Auto-update on push** | ✅ Checked |
| **Deployment Type** | Development (for testing) or Production |
| **Shareable via Studio** | ✅ Checked (for easy access) |

#### **Environment Variables & Secrets**

Configure these **secrets** (sensitive data):

| Secret Name | Value |
|-------------|-------|
| `OPENAI_API_KEY` | `sk-proj-YOUR_OPENAI_API_KEY_HERE` |
| `SUPABASE_ANON_KEY` | `your_supabase_anon_key_here` |

Configure these **environment variables** (non-sensitive):

| Variable Name | Value |
|---------------|-------|
| `SUPABASE_URL` | `https://oumhprsxyxnocgbzosvh.supabase.co` |
| `LANGSMITH_API_KEY` | `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` |

3. **Submit Deployment**
   - Click **Submit**
   - Wait for provisioning (few minutes)

### 3. **Monitor Deployment**

#### **Check Build Logs**
1. Select your deployment from the list
2. Click on the revision in the **Revisions** table
3. View **Build** tab for build logs
4. Switch to **Server** tab for runtime logs

#### **View Metrics**
1. Select your deployment
2. Click **Monitoring** tab
3. Monitor request metrics and performance

## 🔧 **Using Your Deployed Agent**

### **Via API**
Once deployed, you'll get an API endpoint:
```bash
curl -X POST "https://your-deployment-url/invoke" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_LANGSMITH_API_KEY" \
  -d '{
    "input": {
      "messages": [
        {"role": "user", "content": "Find me some chocolate products"}
      ]
    }
  }'
```

### **Via LangGraph Studio** (if enabled)
- Direct URL provided for browser-based testing
- Interactive chat interface
- Visual graph execution

## 📊 **Available Agent Features**

Your deployed agent supports:

- ✅ **Product Search**: "Find me chocolate products"
- ✅ **Brand Search**: "Show me Coca-Cola products"  
- ✅ **Category Search**: "What dairy products are available?"
- ✅ **GTIN Lookup**: "Tell me about product with GTIN 1234567890123"
- ✅ **General Queries**: "What products do you have?"
- ✅ **Intelligent Retries**: Automatic query improvement
- ✅ **Graceful Fallbacks**: Helpful responses when products not found

## 🛠️ **Creating New Revisions**

To deploy code updates:

1. Push changes to GitHub
2. If auto-update is enabled, deployment happens automatically
3. Or manually create a new revision:
   - Go to your deployment
   - Click **+ New Revision**
   - Configure and submit

## 🔍 **Troubleshooting**

### **Common Issues**

1. **Build Fails**
   - Check build logs in LangGraph Platform
   - Verify `langgraph.json` path is correct
   - Ensure all dependencies in `pyproject.toml`

2. **Runtime Errors**
   - Check server logs
   - Verify environment variables are set correctly
   - Test locally first with `langgraph dev`

3. **Database Connection Issues**
   - Verify Supabase credentials
   - Check network connectivity (whitelist IPs if needed)

### **Network Configuration**

If your Supabase instance has IP restrictions, whitelist these LangGraph Platform IPs:

**US Region:**
- 35.197.29.146
- 34.145.102.123
- 34.169.45.153
- 34.82.222.17
- 35.227.171.135
- 34.169.88.30
- 34.19.93.202
- 34.19.34.50

## 🎉 **Success!**

Your product retrieval agent is now deployed and ready to serve product search requests at scale!

### **Next Steps**
- Monitor performance in the Monitoring tab
- Set up alerts for errors
- Scale to Production deployment type when ready
- Add more product search features as needed

---

**Questions?** Check the [LangGraph Platform Documentation](https://langchain-ai.github.io/langgraph/cloud/) for more details. 