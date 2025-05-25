# 订阅管理系统

[English](README.md) | 中文文档

一个现代化的多用户代理订阅管理系统，支持多种客户端格式转换和永久链接生成，采用[Subconverter](https://github.com/tindy2013/subconverter)作为后端。

## 🌟 主要功能

### 📋 核心功能
- **原始订阅管理** - 添加、编辑、删除原始订阅源
- **复合订阅生成** - 选择多个原始订阅进行合并
- **多格式转换** - 支持 Clash、V2Ray、Surge、Quan X 等格式
- **永久链接** - 生成友好的永久URL，客户端可直接使用
- **多用户支持** - 每个用户独立管理自己的订阅

### 🔒 安全特性
- **用户隔离** - 每个用户只能访问自己的订阅
- **管理员权限** - 管理员可管理用户但无法查看订阅内容
- **会话安全** - 安全的会话管理，可配置过期时间
- **数据验证** - 全面的输入验证和URL验证


## 🚀 快速开始

### 方式一：Docker部署（推荐）

```bash

docker pull dreamscape315419/subscription-manager:latest

```
```
docker run -d \
  --name subscription-manager \
  -p 5000:5000 \
  -v ./data:/app/instance \
  dreamscape315419/subscription-manager:latest
```

### 方式二：手动安装

#### 环境要求
- Python 3.7+
- pip

#### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/Dreamscape315/Subscription-Manager.git
cd Subscription-Manager
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行应用**
```bash
python app.py
```

4. **访问应用**
打开浏览器访问：http://localhost:5000



### 首次使用

1. 注册第一个用户（自动成为管理员）
2. 配置系统设置（Subconverter API、基础URL）
3. 添加原始订阅源
4. 创建复合订阅，设置自定义URL
5. 复制生成的永久链接到客户端使用



## ⚙️ 系统设置

管理员可以配置：

- **Subconverter API地址** - 用于订阅格式转换
- **应用基础URL** - 用于生成永久链接
- **用户管理** - 创建、编辑、删除用户账户
- **系统信息** - 查看Python/Flask版本和系统状态

## 🆘 常见问题

### Q: 如何更换Subconverter API？
A: 管理员登录后，进入"系统设置"页面修改API地址。

### Q: 支持自定义配置模板吗？
A: 支持，在创建复合订阅时可以指定自定义配置模板URL。

### Q: 管理员能看到用户的订阅配置吗？
A: 不能。系统在架构层面限制了管理员权限，管理员只能管理用户账户，无法查看任何用户的订阅URL或配置内容。


## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

**享受便捷的订阅管理体验！** 🎉 