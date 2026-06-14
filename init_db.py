"""初始化数据库并创建管理员账户"""
from app import app, db
from models import User

def init_database():
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表创建成功！")

        # 检查是否已存在管理员账户
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            # 创建默认管理员账户
            admin = User(
                username='admin',
                name='系统管理员',
                department='项目组',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("管理员账户创建成功！")
            print("用户名: admin")
            print("密码: admin123")
        else:
            print("管理员账户已存在")

if __name__ == '__main__':
    init_database()
