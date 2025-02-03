import yaml

# ffdusd configure file by default
DEFAULT_CONFIG = "/etc/ffdusd/ffdusd.yml"

# config content
CONF = dict()

def InitConf(path=DEFAULT_CONFIG):
    try:
        with open(path, 'r') as f:
            global CONF
            CONF = yaml.safe_load(f)
    except FileNotFoundError as e:
        print(f"配置文件不存在:%s" % path)
        raise e

## 获取配置项
#username = config['DEFAULT']['username']
#password = config['DEFAULT']['password']
#db_name = config['DATABASE']['db_name']
#log_level = config['LOGGING']['level']
#
## 打印配置项
#print(f"Username: {username}")
#print(f"Password: {password}")
#print(f"Database Name: {db_name}")
#print(f"Log Level: {log_level}")
