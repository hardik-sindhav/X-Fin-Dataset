# 🚀 START HERE - Quick Deployment

## Your VPS Details
- **IP**: 147.93.97.60
- **User**: root
- **Hostname**: srv1107349.hstgr.cloud

---

## 🎯 Quick Start (Choose One)

### Option 1: Manual Step-by-Step (Recommended)
👉 Follow `DEPLOY_WITH_YOUR_DETAILS.md` - it has exact commands for your VPS

### Option 2: Automated Script
👉 Follow `SIMPLE_DEPLOY.md` - but replace `your-vps-ip` with `147.93.97.60`

---

## 📋 First Steps

### 1. Connect to VPS
```bash
ssh root@147.93.97.60
```

### 2. Install Software
```bash
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip python3-dev nodejs npm nginx git
npm install -g pm2
```

### 3. Upload Project
**From your Windows computer:**
```powershell
cd "C:\Users\HP\Desktop\X Fin Dataset"
scp -r * root@147.93.97.60:/var/www/x-fin-dataset/
```

### 4. Follow `DEPLOY_WITH_YOUR_DETAILS.md` for remaining steps

---

## 🔑 GitHub Auto-Deploy Setup

1. **Generate SSH key:**
   ```bash
   ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/github_deploy
   ```

2. **Add to VPS:**
   ```bash
   ssh-copy-id -i ~/.ssh/github_deploy.pub root@147.93.97.60
   ```

3. **Add GitHub Secrets:**
   - VPS_HOST: `147.93.97.60`
   - VPS_USER: `root`
   - VPS_SSH_KEY: (Your private key)

4. **See `QUICK_GITHUB_DEPLOY.md` for details**

---

## 📁 Important Files

- `DEPLOY_WITH_YOUR_DETAILS.md` - **Start here!** Complete guide with your IP
- `SIMPLE_DEPLOY.md` - General deployment guide
- `QUICK_GITHUB_DEPLOY.md` - Auto-deployment setup
- `connect-vps.bat` - Quick connect script (Windows)
- `upload-to-vps.bat` - Quick upload script (Windows)

---

## ✅ Checklist

- [ ] Connected to VPS: `ssh root@147.93.97.60`
- [ ] Installed Python, Node.js, Nginx, PM2
- [ ] Uploaded project to `/var/www/x-fin-dataset`
- [ ] Backend setup complete
- [ ] Frontend built
- [ ] Nginx configured
- [ ] SSL certificate installed
- [ ] Site is live!

---

**Need help? Check `DEPLOY_WITH_YOUR_DETAILS.md` for detailed steps!**

