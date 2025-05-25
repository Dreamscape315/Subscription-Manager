# 订阅管理系统

[English](README.md) | 中文版本

一个现代化的多用户代理订阅管理系统，支持多种客户端格式转换和永久链接生成，采用Subconverter作为后端。

## 🌟 主要功能

### 📋 核心功能
- **原始订阅管理** - 添加、编辑、删除原始订阅源
- **复合订阅生成** - 选择多个原始订阅进行合并
- **多格式转换** - 支持 Clash、V2Ray、Surge、Quan X 等格式
- **永久链接** - 生成友好的永久URL，客户端可直接使用
- **多用户支持** - 每个用户独立管理自己的订阅

## 🚀 快速开始

### 环境要求
- Python 3.7+
- pip

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/Dreamscape315/Subscription-Manager
cd NewSub
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行应用**
```bash
python run.py
```

4. **访问应用**
打开浏览器访问：http://localhost:5000

### 首次使用

1. 注册第一个用户（自动成为管理员）
2. 添加原始订阅源
3. 创建复合订阅，选择自定义URL，选择自定义规则配置
4. 复制生成的永久链接到客户端使用

## ⚙️ 系统设置

管理员可以配置以下设置：

- **Subconverter API地址** - 用于转换订阅格式
- **应用基础URL** - 用于生成永久链接


## 🛠️ 部署方式

### Docker部署（推荐）

```bash
# 使用Docker Compose快速启动
docker-compose up -d

# 或手动构建
docker build -t subscription-manager .
docker run -d -p 5000:5000 -v ./instance:/app/instance subscription-manager
```

### Linux Screen部署

```bash
# 使用安装脚本
chmod +x install_and_run.sh
./install_and_run.sh

# 或手动设置
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
screen -S subscription-manager
python3 run.py
# 按 Ctrl+A+D 分离screen会话
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 常见问题

### Q: 如何更换Subconverter API？
A: 管理员登录后，进入"系统设置"页面修改API地址。

### Q: 忘记管理员密码怎么办？
A: 删除数据库文件重新初始化，第一个注册的用户会自动成为管理员。

### Q: 支持自定义配置模板吗？
A: 支持，在创建复合订阅时可以指定自定义配置模板URL。

### Q: 如何备份数据？
A: 备份 `instance/subscription_manager.db` 文件即可。

### Q: 如何创建管理员账户？
A: 第一个注册的用户自动成为管理员，或由现有管理员直接创建。

### Q: 管理员能看到用户的订阅配置吗？
A: 不能。系统在架构层面限制了管理员权限，管理员只能管理用户账户，无法查看任何用户的订阅URL或配置内容。


**享受便捷的订阅管理体验！** 🎉 