# CI/CD Pipeline Documentation

## 🚀 Overview

Your Stellar Sales System now has a complete CI/CD pipeline setup with GitHub Actions. Here's what's been configured:

## 📦 What's Included

### 1. **CI Pipeline** (`ci.yml`)
Runs on every push and PR to main/develop branches:
- ✅ Code formatting check (autopep8)
- ✅ Linting (pylint)
- ✅ Type checking (mypy)
- ✅ Security scanning (bandit, safety)
- ✅ Unit tests with coverage
- ✅ Dependency vulnerability checks
- ✅ Uploads coverage reports to Codecov

### 2. **Docker Build & Push** (`docker-build.yml`)
Automatically builds and publishes Docker images:
- 🐳 Multi-arch builds (amd64 & arm64)
- 🏷️ Smart tagging (branch, PR, semver, sha)
- 🔒 Security scanning with Trivy
- 📦 Pushes to GitHub Container Registry
- ⚡ Build caching for speed

### 3. **Deployment Pipeline** (`deploy.yml`)
Deploy to staging/production:
- 🎯 Manual or automatic deployments
- 🌍 Environment-based deployments
- 📝 Pre-configured templates for:
  - Kubernetes
  - Docker Compose (SSH)
  - AWS ECS
  - Or customize your own!

### 4. **Security Audit** (`security-audit.yml`)
Weekly automated security checks:
- 🔍 Dependency vulnerability scanning
- 🛡️ Code security analysis
- 📊 Generates security reports
- 🚨 Auto-creates GitHub issues if vulnerabilities found

### 5. **Docker Configuration**
- `Dockerfile`: Multi-stage optimized build
- `docker-compose.prod.yml`: Production-ready compose file

## 🎯 Quick Start

### Enable GitHub Actions
1. Push these files to your GitHub repo
2. Go to **Settings** → **Actions** → **General**
3. Enable "Read and write permissions" for workflows

### Set Up Secrets (Optional)
For deployment, add these secrets in **Settings** → **Secrets**:
- `KUBE_CONFIG` - Kubernetes config (if using K8s)
- `SERVER_HOST`, `SERVER_USER`, `SSH_PRIVATE_KEY` - SSH deployment
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` - AWS deployment

### Test Locally
```bash
# Build Docker image
docker build -t stellar-sales-system:local .

# Run with Docker Compose
docker-compose -f docker-compose.prod.yml up

# Run tests
pytest tests/ -v --cov
```

## 🔧 Customization

### Adjust CI Checks
Edit `.github/workflows/ci.yml`:
- Change Python version
- Modify linting rules
- Add/remove security tools

### Configure Deployment
Edit `.github/workflows/deploy.yml`:
- Uncomment your deployment method
- Add custom deployment scripts
- Configure notifications

### Update Docker Build
Edit `.github/workflows/docker-build.yml`:
- Change target platforms
- Modify image tags
- Adjust build arguments

## 📊 Monitoring

### View Pipeline Status
- Go to **Actions** tab in GitHub
- Check individual workflow runs
- Download artifacts (test reports, security scans)

### Coverage Reports
- Coverage is automatically uploaded to Codecov
- Set up at https://codecov.io if needed

## 🎨 Workflow Triggers

| Workflow | Trigger |
|----------|---------|
| CI | Push/PR to main/develop |
| Docker Build | Push to main, version tags |
| Deploy | Push to main, manual trigger |
| Security Audit | Weekly Monday 9AM, manual |

## 🔄 Next Steps

1. **Push to GitHub** to trigger first CI run
2. **Configure deployment** based on your infrastructure
3. **Set up Codecov** for coverage tracking (optional)
4. **Enable branch protection** requiring CI to pass before merge

## 🐛 Troubleshooting

**CI failing?**
- Check Python dependencies are compatible
- Ensure tests pass locally first
- Review error logs in Actions tab

**Docker build failing?**
- Verify Dockerfile paths
- Check if all dependencies install correctly
- Test build locally first

**Deployment not working?**
- Uncomment and configure deployment method
- Verify secrets are set correctly
- Check server/cluster connectivity

## 📚 Resources

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

**Questions?** Check the workflow files for inline comments and examples!
