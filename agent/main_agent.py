import shutil
from pathlib import Path

from deepagents import create_deep_agent
from langgraph.checkpoint.memory import InMemorySaver

from agent.llm import model
from agent.prompts import main_agent_content
from agent.subagent.database_query import database_query_agent
from agent.subagent.network_search import network_search_agent
from agent.subagent.rag_query import rag_query_agent
from agent.tools.markdown_tools import generate_markdown
from agent.tools.pdf_tools import convert_md_to_pdf
from agent.tools.upload_file_read_tool import read_file_content
from api.context import set_session_context, set_thread_context
from api.monitor import monitor

main_agent=create_deep_agent(
    model=model,
    system_prompt=main_agent_content['system_prompt'],
    tools=[generate_markdown,convert_md_to_pdf,read_file_content],
    subagents=[database_query_agent,network_search_agent,rag_query_agent],
    checkpointer=InMemorySaver(),
)
project_root_path = Path(__file__).parent.parent.resolve()
"""
1.执行主智能体一定要异步，因为对应了多个客户端
2 什么时候触发我们的智能体的调用或者执行
"""
async def run_deep_agent(task_query,session_id):
    """
    异步执行
    :return:
    """
    print(f"当前会话agent开始执行了！ 会话id是：{session_id}")

    session_dir=project_root_path/'output'/f"session_{session_id}"
    #文件夹不存在则创建
    if not session_dir.exists():
        session_dir.mkdir(parents=True, exist_ok=True)
    #  \ \n \t -> /
    session_dir_str=str(session_dir).replace('\\','/')
    #获取相对文件夹
    relative_session_dir_str=str(session_dir.relative_to(project_root_path)).replace('\\','/')

    #处理上传文档
    update_dir_path=project_root_path/"update"/f"session_{session_id}"
    update_info_prompt="" #解析位置的提示词
    if update_dir_path.exists():
        files=[f.name for f in update_dir_path.interdir() if f.is_file()]
        #将上传文件统一赋值到OUTput——dir 方便前端读取
        if files:
            for filename in files:
                #将源文件-》复制 -》目标文件中
                shutil.copy2(update_dir_path/filename,session_dir/filename)
            #构建提示词 告诉大模型，有上传文件，你要读取这些文件
            update_info_prompt=(f"\n [已上传文件]已加载到 工作目录：\n"
                                +"\n".join([f"  -{file}" for file in files])
                                +"\n 请优先使用工具(read_file_content)读取并参考这些文件。")
    #继续准备 1.当前会话对应的session_id session_dir 存储到contextVars[后续工具获取,socket->推送消息]
    session_dir_token=set_session_context(session_dir_str) #存储的当前会话对呀的文件夹地址
    session_id_token=set_thread_context(session_id) #获取当前会话的session_id对应的socket

    monitor.report_session_dir(session_dir_str)

    #执行main_agent

    updated_info_prompt=""
    #go
    # 执行main_agent
    config = {
        "configurable": {
            "thread_id": session_id
        }
    }

    # 构建提示词
    path_instruction = f"""
    【工作环境指令】
    工作目录: {relative_session_dir_str}
    {updated_info_prompt}

    规则:
    1. 新生成文件必须保存到工作目录: '{relative_session_dir_str}/filename'
    2. 读取已上传的文件时, 请直接将文件名 (例如: '开篇.txt') 作为 filename 参数传入 (read_file_content) 读取工具, 不要带上任何目录前缀。
    3. 使用相对路径, 禁止使用绝对路径
    4. 若存在上传文件, 请先分析内容
    """

    # 反馈结果
    try:
    # 执行
        async for chunk in main_agent.astream(
                {
                    "messages":[
                        {
                            "role": "user",
                            "content": task_query + path_instruction
                        }
                    ]
                },config=config):
            for node_name,state in chunk.items():
                if not state in chunk.items():
                    if not state or "messages" not in state: continue
                    messages= state["messages"]
                    if messages in isinstance(messages,list):
                        last_msg= messages[-1]
                        if node_name == 'model':
                            if last_msg.tool_calls:
                                # 工具和子智能体
                                for tool_call in last_msg.tool_calls:
                                    """
                                    tool_call = {
                                        name: task
                                        args:{
                                            subagent_type: 子智能体的名字
                                            description: 子智能体的描述
                                        }
                                    }
                                    """
                                    if tool_call['name'] == 'task':
                                        # 调用某个子智能体
                                        monitor.report_assistant(tool_call['args']['subagent_type'],
                                                                 {'description': tool_call['args']['description']})
                            elif last_msg.content:
                                #最终结果
                                print("最终结果：",last_msg.content[:100])
                                monitor.report_task_result(last_msg.content)

    except Exception as e:
    # 报错推送错误信息给前端
        monitor._emit("error",f"執行主智能体发现异常信息：{str(e)}")
    finally:
        #释放存储的地址和session_id
        res









    # main_agent.ainvoke({
    #     "message": ""
    # })


