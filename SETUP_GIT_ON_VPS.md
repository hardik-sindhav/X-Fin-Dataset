# Setup Git on VPS for Auto-Deployment

If you want to use Git-based deployment (pulling code from GitHub), follow these steps:

## Step 1: Initialize Git on VPS

```bash
# On your VPS
cd /var/www/x-fin-dataset

# Initialize git (if not already)
git init

# Add your GitHub repository as remote
git remote add origin https://github.com/yourusername/your-repo.git
# OR if using SSH:
git remote add origin git@github.com:yourusername/your-repo.git

# Pull code
git pull origin main
# or
git pull origin master
```

## Step 2: Setup SSH Key for GitHub (Optional - if using SSH URL)

If you use SSH URL for git remote, you need to add GitHub's SSH key:

```bash
# On VPS, generate SSH key
ssh-keygen -t ed25519 -C "vps-deploy" -f ~/.ssh/github_vps

# Display public key
cat ~/.ssh/github_vps.pub
```

Add this public key to GitHub:
1. Go to GitHub → Settings → SSH and GPG keys
2. Click "New SSH key"
3. Paste the public key
4. Save

Then use SSH URL:
```bash
git remote set-url origin git@github.com:yourusername/your-repo.git
```

## Step 3: Use Git-Based Workflow

Use `.github/workflows/deploy-git.yml` instead of `deploy.yml`:

```bash
# On your local machine
git add .github/workflows/deploy-git.yml
git commit -m "Add git-based deployment"
git push origin main
```

## Step 4: Make VPS Repository Read-Only Safe

Since GitHub Actions will pull code, make sure VPS can handle it:

```bash
# On VPS
cd /var/www/x-fin-dataset

# Create .gitignore if needed (to ignore local files)
cat > .gitignore << EOF
venv/
__pycache__/
*.log
.env
node_modules/
*.json
EOF

# Don't commit .env file
git update-index --assume-unchanged backend/.env
```

## Benefits of Git-Based Deployment

✅ Simpler - just pull code
✅ No file copying needed
✅ Can track what's deployed
✅ Easy rollback with `git reset`

## Which Workflow to Use?

- **deploy-git.yml**: Uses `git pull` on VPS (simpler, requires git setup)
- **deploy-simple.yml**: Uses SCP to copy files (works without git on VPS)

Choose based on your preference!

