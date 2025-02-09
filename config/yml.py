import yaml

# ffdusd configure file by default
DEFAULT_CONFIG = "/etc/ffdusd/ffdusd.yml"

# config content
CONF = dict()

try:
    with open(DEFAULT_CONFIG, 'r') as f:
        CONF = yaml.safe_load(f)
except FileNotFoundError as e:
    print(f"配置文件不存在:%s" % path)
    raise e
