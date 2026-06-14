"""启动脚本 - 初始化数据库并运行应用"""
import os
import sys

# 确保在正确的目录中
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def init_database():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        print("[OK] 数据库初始化成功")

        # 检查是否已存在管理员
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(
                username='admin',
                name='系统管理员',
                department='项目组',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("[OK] 管理员账户创建成功")
            print("     用户名: admin")
            print("     密码: admin123")
        else:
            print("[INFO] 管理员账户已存在")

def main():
    """主函数"""
    print("\n" + "="*50)
    print("海豚计划四期人才测评系统")
    print("="*50 + "\n")

    # 初始化数据库
    init_database()

    print("\n" + "="*50)
    print("启动服务器...")
    print("访问地址: http://localhost:5000")
    print("管理员登录: admin / admin123")
    print("="*50 + "\n")

    # 启动Flask应用
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
