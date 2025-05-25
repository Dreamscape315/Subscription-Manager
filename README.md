# Subscription Management System

[中文版本](README_CN.md) | English

A modern multi-user proxy subscription management system that supports multiple client format conversions and permanent link generation, using Subconverter as backend.

## 🌟 Key Features

### 📋 Core Functions
- **Original Subscription Management** - Add, edit, delete original subscription sources
- **Composite Subscription Generation** - Select multiple original subscriptions for merging
- **Multi-format Conversion** - Support Clash, V2Ray, Surge, Quan X and other formats
- **Permanent Links** - Generate friendly permanent URLs that clients can use directly
- **Multi-user Support** - Each user independently manages their own subscriptions

### 🔒 Security Features
- **User Isolation** - Each user can only access their own subscriptions
- **Admin Management** - Administrators can manage users but cannot view subscription content
- **Session Security** - Secure session management with configurable expiration
- **Data Validation** - Comprehensive input validation and URL verification

## 🚀 Quick Start

### Method 1: Docker Deployment (Recommended)

```bash
# Pull the latest image
docker pull dreamscape315419/subscription-manager:latest
```
```
docker run -d \
  --name subscription-manager \
  -p 5000:5000 \
  -v ./data:/app/instance \
  dreamscape315419/subscription-manager:latest
```

### Method 2: Manual Installation

#### Requirements
- Python 3.7+
- pip

#### Installation Steps

1. **Clone the project**
```bash
git clone https://github.com/Dreamscape315/Subscription-Manager.git
cd Subscription-Manager
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python app.py
```

4. **Access the application**
Open browser and visit: http://localhost:5000

### First Use

1. Register the first user (automatically becomes admin)
2. Configure system settings (Subconverter API, Base URL)
3. Add original subscription sources
4. Create composite subscriptions with custom URLs
5. Copy generated permanent links for use in clients

## ⚙️ System Settings

Administrators can configure:

- **Subconverter API Address** - For subscription format conversion
- **Application Base URL** - For generating permanent links
- **User Management** - Create, edit, delete user accounts
- **System Information** - View Python/Flask versions and system status

## 🆘 FAQ

### Q: How to change Subconverter API?
A: Admin login, go to "System Settings" page to modify API address.

### Q: Does it support custom configuration templates?
A: Yes, you can specify custom configuration template URL when creating composite subscriptions.

### Q: Can admins see users' subscription configurations?
A: No. The system architecturally limits admin permissions. Admins can only manage user accounts and cannot view any user's subscription URLs or configuration content.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Enjoy convenient subscription management!** 🎉 