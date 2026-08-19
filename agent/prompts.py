from pathlib import Path

import yaml


def load_yaml(file_path):
    """
    加载yaml文件

    :param file_path:
    :return:
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:

            #只会加载 不会触发
            #可能发生脚本注入
            return yaml.safe_load(f)
    except Exception as e:
        print(f"yaml 格式解析错误：{e}")

#根地址
root_path=Path(__file__).parent.parent
config=load_yaml(root_path/'prompt'/'prompts.yml')
print(config)

main_agent_content=config['main_agent']
sub_agents_content=config['sub_agents']