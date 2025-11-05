# 🚀 Quick GitHub Auto-Deploy Setup (5 Minutes)

## Step 1: Generate SSH Key (On Your Computer)

```bash
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/github_deploy
# Press Enter 3 times (no passphrase)
```

## Step 2: Add Key to VPS

```bash
# Copy public key to VPS
ssh-copy-id -i ~/.ssh/github_deploy.pub root@your-vps-ip

# Test connection
ssh -i ~/.ssh/github_deploy root@your-vps-ip
# Should connect without password!
```

## Step 3: Add Secrets to GitHub

1. Go to: **Your Repo** → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**

Add these 3 secrets:

| Name | Value | Example |
|------|-------|---------|
| `VPS_HOST` | Your VPS IP | `123.45.67.89` |
| `VPS_USER` | SSH username | `root` |
| `VPS_SSH_KEY` | Your private key | See below |

**To get private key:**
```bash
cat ~/.ssh/github_deploy
# Copy ENTIRE output (including BEGIN/END lines)
```

## Step 4: Push Workflow to GitHub

```bash
# Make sure you're in project root
git add .github/workflows/deploy-simple.yml
git commit -m "Add auto-deployment"
git push origin main
```

## Step 5: Test It!

1. Make a small change:
   ```bash
   echo "Test" >> README.md
   git add README.md
   git commit -m "Test deployment"
   git push origin main
   ```

2. Go to **Actions** tab in GitHub
3. Watch it deploy! 🎉

---

## That's It!

Now every time you:
- ✅ Push to main/master
- ✅ Merge a PR

Your VPS will automatically update!

---

## Troubleshooting

**SSH fails?**
- Check key is in VPS: `cat ~/.ssh/authorized_keys`
- Test manually: `ssh -i ~/.ssh/github_deploy root@your-vps-ip`

**Deployment fails?**
- Check Actions tab for error logs
- Verify all 3 secrets are set correctly
- Make sure PM2 is installed on VPS: `npm install -g pm2`

---

**Need more details? See `GITHUB_DEPLOY_SETUP.md`**

