```bash
django-admin startproject main .
python manage.py startapp registration
python manage.py startapp api
python manage.py migrate
# password: Administrator
python manage.py createsuperuser --email notexist@qq.com --username admin
```

```python
# 终端中-模型直接操作
# python manage.py shell
from registration.models import User
User.objects.all()
User.objects.count()
```