# Deployment Guide for SAO Contact Manager

## Using Streamlit Cloud with Custom Domain (Recommended)

### Prerequisites
- GitHub repository (already set up)
- Custom domain (karpaylegal.com)
- Access to domain DNS settings

### Step 1: Deploy to Streamlit Cloud

1. Go to [https://streamlit.io/cloud](https://streamlit.io/cloud)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository: `davidkarpay/ASAntics`
5. Branch: `main`
6. Main file path: `sao_contact_manager.py`
7. Click "Deploy"

### Step 2: Configure Custom Domain

#### In Streamlit Cloud:
1. Go to your app settings
2. Under "General" tab, find "Custom subdomain"
3. Enter your desired subdomain (e.g., `sao-contacts`)
4. Your app will be available at: `https://sao-contacts.streamlit.app`

#### In Your DNS Provider (for karpaylegal.com):
1. Add a CNAME record:
   - Name: `sao` (or your preferred subdomain)
   - Value: `your-app-name.streamlit.app`
   - TTL: 3600 (or your preference)

2. Wait for DNS propagation (5-30 minutes)

3. Your app will be accessible at: `https://sao.karpaylegal.com`

### Step 3: Environment Variables (Optional)

If you need to add SMTP settings for real email sending:

1. In Streamlit Cloud app settings
2. Go to "Secrets" section
3. Add your secrets in TOML format:

```toml
[email]
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = "your-email@domain.com"
smtp_password = "your-app-password"
```

## Alternative: GitHub Pages + Backend Service

Since Streamlit requires a Python backend, you can use GitHub Pages for the landing page and deploy the actual app elsewhere:

### GitHub Pages Setup:
1. Go to repository Settings
2. Navigate to Pages
3. Source: Deploy from a branch
4. Branch: main / root
5. Save

### Custom Domain for GitHub Pages:
1. In GitHub Pages settings, add custom domain: `karpaylegal.com` or `www.karpaylegal.com`
2. In your DNS:
   - A record: `@` → `185.199.108.153` (GitHub Pages IP)
   - A record: `@` → `185.199.109.153`
   - A record: `@` → `185.199.110.153`
   - A record: `@` → `185.199.111.153`
   - CNAME record: `www` → `davidkarpay.github.io`

### Backend Deployment Options:

1. **Heroku** (Free tier available)
   - Add `Procfile`: `web: streamlit run sao_contact_manager.py`
   - Deploy with Heroku CLI or GitHub integration

2. **Railway.app** (Simple deployment)
   - Connect GitHub repo
   - Auto-deploys on push
   - Custom domain support

3. **Google Cloud Run**
   - Containerize with Docker
   - Deploy serverless
   - Pay per use

4. **VPS (DigitalOcean, Linode, etc.)**
   - Full control
   - Nginx reverse proxy
   - SSL with Let's Encrypt

## Security Considerations

1. **Environment Variables**: Never commit sensitive data
2. **SSL/HTTPS**: Ensure all deployments use HTTPS
3. **Database**: Consider using cloud database for production
4. **Backups**: Regular database backups
5. **Monitoring**: Set up uptime monitoring

## Domain Configuration Examples

### For Subdomain (sao.karpaylegal.com):
```
Type: CNAME
Name: sao
Value: your-deployment-url.com
TTL: 3600
```

### For Root Domain (karpaylegal.com):
```
Type: A
Name: @
Value: [Your server IP]
TTL: 3600
```

## Support

For Streamlit-specific issues: [Streamlit Community](https://discuss.streamlit.io/)
For deployment help: Check platform-specific documentation