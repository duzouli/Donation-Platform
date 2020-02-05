# wuhan2020 Donation Platform

---

# precondition
* Python 3
	- Windows用户，推荐安装名为 Miniconda 的Python发行版
	- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) [Python 3.7 - Miniconda3 Windows 64-bit](https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe)

# step

## step-01 - Python包安装

### setup-01 - Miniconda(conda用户)
```bash
conda install --file requirements-conda.txt -y
pip install -r requirements-pip.txt
```

### setup-01 - 官方Python(pip用户)
```bash
pip install -r requirements-conda.txt
pip install -r requirements-pip.txt
```

## step-02 - 创建sql
> 注: 默认采用sqlite数据库, **step-02**无需操作

1. 创建数据库
	```sql
	CREATE DATABASE db_donation DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_general_ci;
	```
2. 修改 `main/settings.py`, 将 `DATABASES` 下的 `default` 项配置改为MySQL, 并修改为数据库相关配置

## step-03 - 初始化
```bash
# 数据库初始化(创建表)
python manage.py migrate
# 创建管理用户(用户名、手机号、密码)
python manage.py createsuperuser
# static文件初始化(deploy only required)
python manage.py collectstatic
```

## step-04 - 运行
```bash
# start server (use one of below 3 types of wsgi-server:)
# # wsgi-server 1: django server (worst performance)
python manage.py runserver 127.0.0.1:8989
# # wsgi-server 2: tornado (medium performance)
python tornado-server.py --port=8989
# # wsgi-server 3: hendrix(twisted) (best performance)
python twisted-server.py --port 8989
```
* 注: 不带`port`参数时, 默认端口为`8000`

## step-05 - 访问
- 前台页面: http://127.0.0.1:8989/
- ApiRoot: http://127.0.0.1:8989/api/
- 管理后台: http://127.0.0.1:8989/admin/

## tips
* 如果Windows平台的官方Python用户，使用pip安装Python包报错，错误提示信息中带有“MicroSoft Vistual C++”等信息，一般是因为所安装的库底层使用了C/C++代码加速，需要C/C++环境编译，此时推荐的解决办法是安装Miniconda。
	- 安装Miniconda时，推荐勾选添加到环境变量Path
	- Mac OSX 和 Linux 用户无需安装Miniconda，出现编译问题时，需要安装 gcc/g++ 等编译工具 和 python-dev 库。
* 国内用户使用pip安装包慢时，可以使用豆瓣源加速
	- 单个包-示例: `pip install -i https://pypi.doubanio.com/simple/ --trusted-host pypi.doubanio.com <package>`
	- 清单文件-示例: `pip install -i https://pypi.doubanio.com/simple/ --trusted-host pypi.doubanio.com -r requirements.txt`
* 开发阶段, 使用sqlite数据时, 若执行 `python manage.py migrate` 报MySQL相关的错(连接错误、数据库`db_donation`不存在等), 可暂时将 `main/settings.py` 中 `DATABASE` 下的 `mysql` 配置节暂时删除, 执行完 `migrate` 命令后再恢复`mysql` 配置节

## technology stack
* FrontEnd
	- BootStrap 3
	- jQuery 2
* BackEnd
	- Python 3
	- Django 2.2
	- Django REST framework
	- DataBase:
		+ develop: SQLite
		+ deploy: MySQL 5.6+
* VCS: git/GitHub
