from config import yml
from utils import pt

def main():
    try:
        pt.Pinit()
        yml.InitConf("/Users/bytedance/Documents/project/ffdusd/etc/ffdusd/ffdusd.yml")
        print(yml.CONF)
    except Exception as e:
        print(e)
        exit(1)

if __name__ == "__main__":
    main()
