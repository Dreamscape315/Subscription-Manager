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

## 🚀 Quick Start

### Requirements
- Python 3.7+
- pip

### Installation Steps

1. **Clone the project**
```bash
git clone <repository-url>
cd NewSub
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python run.py
```

4. **Access the application**
Open browser and visit: http://localhost:5000

### First Use

1. Register the first user (automatically becomes admin)
2. Add original subscription sources
3. Create composite subscriptions, choose custom URL, select custom rule configuration
4. Copy the generated permanent links for use in clients

## ⚙️ System Settings

Administrators can configure the following settings:

- **Subconverter API Address** - Used for converting subscription formats
- **Application Base URL** - Used for generating permanent links

## 🛠️ Deployment

### Docker Deployment (Recommended)

```bash
# Quick start with Docker Compose
docker-compose up -d

# Or build manually
docker build -t subscription-manager .
docker run -d -p 5000:5000 -v ./instance:/app/instance subscription-manager
```

### Linux Screen Deployment

```bash
# Use installation script
chmod +x install_and_run.sh
./install_and_run.sh

# Or manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
screen -S subscription-manager
python3 run.py
# Press Ctrl+A+D to detach from screen
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 🆘 FAQ

### Q: How to change Subconverter API?
A: Admin login, go to "System Settings" page to modify API address.

### Q: Forgot admin password?
A: Delete database file and reinitialize, the first registered user will automatically become admin.

### Q: Does it support custom configuration templates?
A: Yes, you can specify custom configuration template URL when creating composite subscriptions.

### Q: How to backup data?
A: Backup the `instance/subscription_manager.db` file.

### Q: How to create admin accounts?
A: The first registered user automatically becomes admin, or existing admins can create them directly.

### Q: Can admins see users' subscription configurations?
A: No. The system architecturally limits admin permissions. Admins can only manage user accounts and cannot view any user's subscription URLs or configuration content.

---

**Enjoy convenient subscription management!** 🎉 