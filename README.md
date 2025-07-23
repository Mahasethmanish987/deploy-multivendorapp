# 🍔 Multivendor Food  Platform



## 🌟 Features
- **Dual Dashboard System**: Separate interfaces for customers/vendors
- **Real-time Order Management**: 
  - Live status updates (accept/cancel/complete)
  - Auto-cancellation after 4 hours (Celery scheduled tasks)
- **Payment Integration**:
  - Automatic refunds on cancellation
  - Commission-based vendor payouts (Stripe integration)
- **Vendor Management**:
  - Email activation workflow
  - Opening hours configuration
  - Live status indicators
- **AWS Deployment**:
  - EC2 (Django + Nginx)
  - RDS (PostgreSQL)
  - S3 (Static files)
  - Separate EC2 for Redis/Celery
- **CI/CD Pipeline**: GitHub Actions for auto-deployment
