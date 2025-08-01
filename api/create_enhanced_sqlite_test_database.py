import sqlite3
import os
from datetime import datetime, timedelta
import random

def create_enhanced_test_database():
    """创建增强版的 SQLite 测试数据库"""
    
    # 数据库文件路径
    db_path = "test_database.db"
    
    # 如果文件已存在，删除它
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"已删除现有的数据库文件: {db_path}")
    
    # 创建数据库连接
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 创建配置相关表
        print("创建配置相关表...")
        
        # 数据源表
        cursor.execute('''
            CREATE TABLE data_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_key TEXT UNIQUE NOT NULL,
                table_name TEXT NOT NULL,
                table_des TEXT,
                table_order TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                database_type TEXT DEFAULT 'sqlite'
            )
        ''')
        
        # 数据源列表
        cursor.execute('''
            CREATE TABLE data_source_columns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                column_name TEXT NOT NULL,
                column_display_name TEXT,
                column_order INTEGER,
                FOREIGN KEY (source_id) REFERENCES data_sources (id) ON DELETE CASCADE
            )
        ''')
        
        # 分析模板表
        cursor.execute('''
            CREATE TABLE analysis_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id TEXT UNIQUE NOT NULL,
                template_name TEXT NOT NULL,
                summary TEXT,
                analysis_goal TEXT,
                insights_template TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 模板必需列
        cursor.execute('''
            CREATE TABLE template_required_columns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER,
                column_name TEXT NOT NULL,
                column_type TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (template_id) REFERENCES analysis_templates (id) ON DELETE CASCADE
            )
        ''')
        
        # 模板可选列
        cursor.execute('''
            CREATE TABLE template_optional_columns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER,
                column_name TEXT NOT NULL,
                column_type TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (template_id) REFERENCES analysis_templates (id) ON DELETE CASCADE
            )
        ''')
        
        # 模板执行步骤
        cursor.execute('''
            CREATE TABLE template_execution_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER,
                step_order INTEGER NOT NULL,
                prompt TEXT NOT NULL,
                save_to_variable TEXT,
                FOREIGN KEY (template_id) REFERENCES analysis_templates (id) ON DELETE CASCADE
            )
        ''')
        
        # 模板输出文件
        cursor.execute('''
            CREATE TABLE template_output_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER,
                file_type TEXT NOT NULL,
                title TEXT NOT NULL,
                source_variable TEXT,
                tool TEXT,
                FOREIGN KEY (template_id) REFERENCES analysis_templates (id) ON DELETE CASCADE
            )
        ''')
        
        # 2. 创建业务数据表
        print("创建业务数据表...")
        
        # 销售记录表
        cursor.execute('''
            CREATE TABLE sales_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                product_id INTEGER,
                sale_date DATE NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                discount_rate DECIMAL(5,2) DEFAULT 0,
                sales_person TEXT,
                region TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 客户表
        cursor.execute('''
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_code TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                customer_type TEXT NOT NULL,
                registration_date DATE,
                phone TEXT,
                email TEXT,
                address TEXT,
                city TEXT,
                province TEXT,
                credit_level TEXT,
                is_vip BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 产品表
        cursor.execute('''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT UNIQUE NOT NULL,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                brand TEXT,
                unit_cost DECIMAL(10,2),
                list_price DECIMAL(10,2),
                stock_quantity INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 员工绩效表
        cursor.execute('''
            CREATE TABLE employee_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                department TEXT NOT NULL,
                position TEXT,
                performance_date DATE NOT NULL,
                sales_target DECIMAL(12,2),
                sales_actual DECIMAL(12,2),
                achievement_rate DECIMAL(5,2),
                customer_satisfaction DECIMAL(3,1),
                call_volume INTEGER,
                work_hours DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 客户投诉表
        cursor.execute('''
            CREATE TABLE customer_complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                complaint_date DATE NOT NULL,
                complaint_type TEXT NOT NULL,
                complaint_category TEXT,
                description TEXT,
                priority_level TEXT,
                status TEXT DEFAULT '待处理',
                assigned_to TEXT,
                resolution_date DATE,
                satisfaction_score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 3. 插入配置数据
        print("插入配置数据...")
        
        # 插入数据源
        data_sources = [
            ('sales_data', 'sales_records', '销售记录数据表', '1', 'sqlite'),
            ('customer_data', 'customers', '客户信息数据表', '2', 'sqlite'),
            ('product_data', 'products', '产品信息数据表', '3', 'sqlite'),
            ('performance_data', 'employee_performance', '员工绩效数据表', '4', 'sqlite'),
            ('complaint_data', 'customer_complaints', '客户投诉数据表', '5', 'sqlite'),
            ('mobile_complaint', 'tb_rp_ct_acpt_wrkfm_detail_311_day', '移动公司投诉明细数据', '6', 'sqlite'),
            ('staff_efficiency', 'tb_rp_ct_86hl_staff_index_summ_day', '86热线员工效能日报', '7', 'sqlite'),
            ('service_request', 'tb_rp_ct_ngcs_wf_service_request_city_311_day', '河北服务请求按地市日报表', '8', 'sqlite')
        ]
        
        for source in data_sources:
            cursor.execute('''
                INSERT INTO data_sources (source_key, table_name, table_des, table_order, database_type)
                VALUES (?, ?, ?, ?, ?)
            ''', source)
        
        # 插入数据源列信息
        source_columns = [
            # 销售记录列
            (1, 'order_id', '订单编号', 1),
            (1, 'customer_id', '客户ID', 2),
            (1, 'product_id', '产品ID', 3),
            (1, 'sale_date', '销售日期', 4),
            (1, 'quantity', '销售数量', 5),
            (1, 'unit_price', '单价', 6),
            (1, 'total_amount', '总金额', 7),
            (1, 'sales_person', '销售员', 8),
            (1, 'region', '销售区域', 9),
            
            # 客户信息列
            (2, 'customer_code', '客户编码', 1),
            (2, 'customer_name', '客户名称', 2),
            (2, 'customer_type', '客户类型', 3),
            (2, 'city', '城市', 4),
            (2, 'province', '省份', 5),
            (2, 'is_vip', '是否VIP', 6),
            
            # 产品信息列
            (3, 'product_code', '产品编码', 1),
            (3, 'product_name', '产品名称', 2),
            (3, 'category', '产品类别', 3),
            (3, 'brand', '品牌', 4),
            (3, 'list_price', '标价', 5),
            
            # 员工绩效列
            (4, 'employee_id', '员工编号', 1),
            (4, 'employee_name', '员工姓名', 2),
            (4, 'department', '部门', 3),
            (4, 'sales_actual', '实际销售额', 4),
            (4, 'achievement_rate', '完成率', 5),
            
            # 客户投诉列
            (5, 'complaint_id', '投诉编号', 1),
            (5, 'customer_id', '客户ID', 2),
            (5, 'complaint_type', '投诉类型', 3),
            (5, 'status', '处理状态', 4),
            (5, 'satisfaction_score', '满意度评分', 5)
        ]
        
        for col in source_columns:
            cursor.execute('''
                INSERT INTO data_source_columns (source_id, column_name, column_display_name, column_order)
                VALUES (?, ?, ?, ?)
            ''', col)
        
        # 插入分析模板
        templates = [
            ('sales_analysis', '销售数据分析', '销售业绩综合分析', '分析销售趋势、产品表现和区域分布', '基于销售数据进行多维度分析，识别销售趋势和增长机会'),
            ('customer_segmentation', '客户细分分析', '客户群体细分与画像', '根据客户行为和特征进行细分', '通过客户数据分析，识别不同客户群体的特征和价值'),
            ('performance_evaluation', '员工绩效评估', '员工绩效综合评估', '评估员工工作表现和效率', '基于多项指标评估员工绩效，识别优秀员工和改进机会'),
            ('complaint_analysis', '投诉分析报告', '客户投诉趋势分析', '分析投诉类型、频率和解决效率', '通过投诉数据分析，识别服务问题和改进方向'),
            ('mobile_service_analysis', '移动服务分析', '移动公司服务质量分析', '分析移动服务请求和投诉情况', '基于移动公司数据分析服务质量和客户满意度')
        ]
        
        for template in templates:
            cursor.execute('''
                INSERT INTO analysis_templates (template_id, template_name, summary, analysis_goal, insights_template)
                VALUES (?, ?, ?, ?, ?)
            ''', template)
        
        # 插入模板必需列
        required_columns = [
            (1, 'sale_date', 'DATE', '销售日期'),
            (1, 'total_amount', 'DECIMAL', '销售金额'),
            (2, 'customer_type', 'TEXT', '客户类型'),
            (2, 'registration_date', 'DATE', '注册日期'),
            (3, 'performance_date', 'DATE', '绩效日期'),
            (3, 'achievement_rate', 'DECIMAL', '完成率'),
            (4, 'complaint_date', 'DATE', '投诉日期'),
            (4, 'complaint_type', 'TEXT', '投诉类型'),
            (5, 'statis_date', 'DATE', '统计日期')
        ]
        
        for col in required_columns:
            cursor.execute('''
                INSERT INTO template_required_columns (template_id, column_name, column_type, description)
                VALUES (?, ?, ?, ?)
            ''', col)
        
        # 插入模板可选列
        optional_columns = [
            (1, 'region', 'TEXT', '销售区域'),
            (1, 'sales_person', 'TEXT', '销售员'),
            (2, 'city', 'TEXT', '城市'),
            (2, 'is_vip', 'BOOLEAN', '是否VIP客户'),
            (3, 'department', 'TEXT', '部门'),
            (4, 'priority_level', 'TEXT', '优先级'),
            (5, 'prov_name', 'TEXT', '省份名称')
        ]
        
        for col in optional_columns:
            cursor.execute('''
                INSERT INTO template_optional_columns (template_id, column_name, column_type, description)
                VALUES (?, ?, ?, ?)
            ''', col)
        
        # 插入执行步骤
        execution_steps = [
            (1, 1, '分析销售趋势：按时间维度统计销售额变化', 'sales_trend'),
            (1, 2, '分析产品表现：统计各产品销售情况', 'product_performance'),
            (1, 3, '分析区域分布：统计各区域销售情况', 'region_analysis'),
            (2, 1, '客户类型分析：统计不同类型客户分布', 'customer_types'),
            (2, 2, '客户价值分析：计算客户生命周期价值', 'customer_value'),
            (3, 1, '绩效指标统计：计算各项绩效指标', 'performance_metrics'),
            (3, 2, '部门对比分析：对比各部门绩效', 'department_comparison'),
            (4, 1, '投诉趋势分析：统计投诉数量变化', 'complaint_trend'),
            (4, 2, '投诉类型分析：分析投诉类型分布', 'complaint_types'),
            (5, 1, '服务质量分析：分析服务指标', 'service_quality')
        ]
        
        for step in execution_steps:
            cursor.execute('''
                INSERT INTO template_execution_steps (template_id, step_order, prompt, save_to_variable)
                VALUES (?, ?, ?, ?)
            ''', step)
        
        # 插入输出文件配置
        output_files = [
            (1, 'chart', '销售趋势图', 'sales_trend', 'matplotlib'),
            (1, 'report', '销售分析报告', 'sales_analysis', 'docx'),
            (2, 'chart', '客户分布图', 'customer_types', 'matplotlib'),
            (3, 'chart', '绩效对比图', 'performance_metrics', 'matplotlib'),
            (4, 'chart', '投诉趋势图', 'complaint_trend', 'matplotlib'),
            (5, 'dashboard', '服务质量仪表板', 'service_quality', 'plotly')
        ]
        
        for file_config in output_files:
            cursor.execute('''
                INSERT INTO template_output_files (template_id, file_type, title, source_variable, tool)
                VALUES (?, ?, ?, ?, ?)
            ''', file_config)
        
        # 4. 插入业务测试数据
        print("插入业务测试数据...")
        
        # 插入客户数据
        customers_data = [
            ('CUST001', '北京科技有限公司', '企业客户', '2023-01-15', '010-12345678', 'contact@bjtech.com', '北京市朝阳区', '北京', '北京', 'A', 1),
            ('CUST002', '上海贸易公司', '企业客户', '2023-02-20', '021-87654321', 'info@shtrade.com', '上海市浦东新区', '上海', '上海', 'B', 0),
            ('CUST003', '张三', '个人客户', '2023-03-10', '138-0000-1111', 'zhangsan@email.com', '广州市天河区', '广州', '广东', 'C', 0),
            ('CUST004', '深圳创新科技', '企业客户', '2023-01-25', '0755-1234567', 'service@szcx.com', '深圳市南山区', '深圳', '广东', 'A', 1),
            ('CUST005', '李四', '个人客户', '2023-04-05', '139-0000-2222', 'lisi@email.com', '杭州市西湖区', '杭州', '浙江', 'B', 0)
        ]
        
        for customer in customers_data:
            cursor.execute('''
                INSERT INTO customers (customer_code, customer_name, customer_type, registration_date, 
                                     phone, email, address, city, province, credit_level, is_vip)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', customer)
        
        # 插入产品数据
        products_data = [
            ('PROD001', '智能手机A1', '电子产品', '华为', 2000.00, 3999.00, 100, 1),
            ('PROD002', '笔记本电脑B1', '电子产品', '联想', 3500.00, 5999.00, 50, 1),
            ('PROD003', '无线耳机C1', '电子产品', '小米', 150.00, 299.00, 200, 1),
            ('PROD004', '智能手表D1', '电子产品', '苹果', 1500.00, 2999.00, 80, 1),
            ('PROD005', '平板电脑E1', '电子产品', '华为', 1800.00, 3299.00, 60, 1)
        ]
        
        for product in products_data:
            cursor.execute('''
                INSERT INTO products (product_code, product_name, category, brand, 
                                    unit_cost, list_price, stock_quantity, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', product)
        
        # 插入销售记录数据
        base_date = datetime(2024, 1, 1)
        sales_data = []
        
        for i in range(100):
            order_id = f"ORD{str(i+1).zfill(6)}"
            customer_id = random.randint(1, 5)
            product_id = random.randint(1, 5)
            sale_date = base_date + timedelta(days=random.randint(0, 365))
            quantity = random.randint(1, 10)
            unit_price = random.uniform(299, 5999)
            total_amount = quantity * unit_price
            discount_rate = random.uniform(0, 0.2)
            sales_person = random.choice(['张销售', '李销售', '王销售', '赵销售', '陈销售'])
            region = random.choice(['华北', '华东', '华南', '西南', '东北'])
            
            sales_data.append((order_id, customer_id, product_id, sale_date.strftime('%Y-%m-%d'),
                             quantity, unit_price, total_amount, discount_rate, sales_person, region))
        
        cursor.executemany('''
            INSERT INTO sales_records (order_id, customer_id, product_id, sale_date, quantity, 
                                     unit_price, total_amount, discount_rate, sales_person, region)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sales_data)
        
        # 插入员工绩效数据
        performance_data = []
        employees = [
            ('EMP001', '张三', '销售部', '销售经理'),
            ('EMP002', '李四', '销售部', '销售代表'),
            ('EMP003', '王五', '客服部', '客服主管'),
            ('EMP004', '赵六', '技术部', '技术支持'),
            ('EMP005', '陈七', '销售部', '销售代表')
        ]
        
        for emp in employees:
            for month in range(1, 13):
                perf_date = datetime(2024, month, 1)
                sales_target = random.uniform(50000, 200000)
                sales_actual = sales_target * random.uniform(0.7, 1.3)
                achievement_rate = (sales_actual / sales_target) * 100
                customer_satisfaction = random.uniform(3.5, 5.0)
                call_volume = random.randint(50, 200)
                work_hours = random.uniform(160, 200)
                
                performance_data.append((emp[0], emp[1], emp[2], emp[3], perf_date.strftime('%Y-%m-%d'),
                                       sales_target, sales_actual, achievement_rate, customer_satisfaction,
                                       call_volume, work_hours))
        
        cursor.executemany('''
            INSERT INTO employee_performance (employee_id, employee_name, department, position, 
                                            performance_date, sales_target, sales_actual, achievement_rate,
                                            customer_satisfaction, call_volume, work_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', performance_data)
        
        # 插入客户投诉数据
        complaint_data = []
        complaint_types = ['产品质量', '服务态度', '物流配送', '售后服务', '价格问题']
        priorities = ['低', '中', '高', '紧急']
        statuses = ['待处理', '处理中', '已解决', '已关闭']
        
        for i in range(50):
            complaint_id = f"COMP{str(i+1).zfill(4)}"
            customer_id = random.randint(1, 5)
            complaint_date = base_date + timedelta(days=random.randint(0, 365))
            complaint_type = random.choice(complaint_types)
            priority = random.choice(priorities)
            status = random.choice(statuses)
            assigned_to = random.choice(['客服A', '客服B', '客服C'])
            satisfaction_score = random.randint(1, 5) if status == '已解决' else None
            
            complaint_data.append((complaint_id, customer_id, complaint_date.strftime('%Y-%m-%d'),
                                 complaint_type, complaint_type, f'关于{complaint_type}的投诉',
                                 priority, status, assigned_to, satisfaction_score))
        
        cursor.executemany('''
            INSERT INTO customer_complaints (complaint_id, customer_id, complaint_date, complaint_type,
                                           complaint_category, description, priority_level, status,
                                           assigned_to, satisfaction_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', complaint_data)
        
        # 提交事务
        conn.commit()
        print(f"✅ 成功创建增强版 SQLite 测试数据库: {db_path}")
        
        # 显示统计信息
        tables = ['data_sources', 'data_source_columns', 'analysis_templates', 
                 'template_required_columns', 'template_optional_columns',
                 'template_execution_steps', 'template_output_files',
                 'sales_records', 'customers', 'products', 
                 'employee_performance', 'customer_complaints']
        
        print("\n📊 数据库表统计:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} 条记录")
        
        return db_path
        
    except Exception as e:
        print(f"❌ 创建数据库时出错: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 开始创建增强版 SQLite 测试数据库...")
    db_path = create_enhanced_test_database()
    
    if db_path:
        print(f"\n✅ 数据库创建完成!")
        print(f"📁 数据库文件位置: {os.path.abspath(db_path)}")
        print("\n📋 包含的表:")
        print("  配置表:")
        print("    - data_sources (数据源)")
        print("    - data_source_columns (数据源列)")
        print("    - analysis_templates (分析模板)")
        print("    - template_required_columns (模板必需列)")
        print("    - template_optional_columns (模板可选列)")
        print("    - template_execution_steps (模板执行步骤)")
        print("    - template_output_files (模板输出文件)")
        print("  业务表:")
        print("    - sales_records (销售记录)")
        print("    - customers (客户信息)")
        print("    - products (产品信息)")
        print("    - employee_performance (员工绩效)")
        print("    - customer_complaints (客户投诉)")
        print("\n🔧 使用方法:")
        print("  1. 运行 switch_database.py 切换到 SQLite 数据库")
        print("  2. 运行 verify_test_database.py 验证数据库")
        print("  3. 启动 API 服务进行测试")