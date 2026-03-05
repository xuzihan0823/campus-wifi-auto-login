# Campus WiFi Auto Login

一个用于 **自动登录校园网（深澜 / ePortal）** 的脚本工具。
适用于需要在浏览器中输入账号密码才能联网的校园网络环境。

该项目使用 **Python + Playwright** 自动填写登录信息，实现：

* 一键登录校园网
* 断网自动重连（仍处于开发阶段）
* 支持多运营商选择（移动 / 电信 / 联通 / 校园网）

---

# 功能特性

* 自动填写账号密码并登录校园网
* 支持运营商选择
* 支持断网自动检测并重新登录
* 支持手动登录
* 支持 Windows 环境运行
* 使用 Playwright 自动化浏览器操作

---

# 运行环境

需要以下环境：

* Python **3.8+**
* Windows / Linux / macOS
* Playwright 浏览器运行时

---

# 安装步骤

## 1 安装 Python

如果没有 Python，请先安装：

https://www.python.org/downloads/

安装时建议勾选：

```
Add Python to PATH
```

---

## 2 克隆仓库

```bash
git clone https://github.com/yourname/campus-wifi-auto-login.git
cd campus-wifi-auto-login
```

或者直接下载 ZIP 并解压。

---

## 3 安装依赖

```bash
pip install -r requirements.txt
```

---

## 4 安装 Playwright 浏览器

```bash
python -m playwright install chromium
```

首次安装会下载浏览器运行环境。

---

# 使用方法

## 手动登录校园网

打开 `run_log.bat` 文件，修改以下内容：

```
set CAMPUS_USER=你的学号
set CAMPUS_PASS=你的密码
set CAMPUS_ISP=移动
set CAMPUS_PORTAL=http://172.16.54.18/eportal/
```

运营商支持：

```
移动
电信
联通
校园网
```

修改完成后，双击：

```
run_log.bat
```

即可自动登录校园网。

---

# 自动断网重连

如果电脑经常出现：

* 睡眠唤醒后断网
* WiFi 重新连接后需要重新登录

可以运行：

```
start_monitor.bat
```

该脚本会：

1. 每隔一段时间检测网络状态
2. 如果检测到断网
3. 自动执行登录脚本重新连接校园网

适合长期运行。

---

# 项目结构

```
campus-wifi-auto-login
│
├─ login.py            # 校园网登录脚本
├─ monitor.py          # 网络状态检测脚本
├─ run_log.bat         # 手动登录
├─ start_monitor.bat   # 自动重连
├─ requirements.txt
└─ README.md
```

---

# 常见问题

## 浏览器未安装

如果出现类似错误：

```
Executable doesn't exist
```

请运行：

```bash
python -m playwright install chromium
```

---

## 出现 ERR_ADDRESS_UNREACHABLE

请确认：

* 已连接校园网 WiFi
* 登录地址正确
* Portal 地址为：

```
http://172.16.54.18/eportal/
```

---

## 脚本无法运行

检查：

```
python --version
```

确保 Python 已正确安装。

---

# 安全提示

请不要将 **真实账号密码提交到 GitHub**。

建议：

* 在本地修改 `.bat` 文件填写账号密码
* 仓库中仅保留示例配置

示例：

```
set CAMPUS_USER=your_id
set CAMPUS_PASS=your_password
```

---

# 免责声明

本项目仅用于 **学习与研究自动化技术**。

请确保：

* 在合法授权范围内使用
* 遵守学校网络使用规定

作者不对因使用本项目造成的任何问题承担责任。

---

# License

MIT License
