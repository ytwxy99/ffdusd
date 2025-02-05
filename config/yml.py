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
