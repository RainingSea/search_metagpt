import json
import jsonlines
import time
import os
import openai
from openai import OpenAI
# 读取 JSONL 文件并提取每条数据中的 prompt 字段
def read_task_id_and_prompt(jsonl_file):
    task_ids_and_prompts = []
    with jsonlines.open(jsonl_file, 'r') as reader:
        for obj in reader:
            task_id = obj.get('task_id', None)
            prompt = obj.get('prompt', None)
            if task_id is not None and prompt is not None:
                task_ids_and_prompts.append((task_id, prompt))  
    return task_ids_and_prompts


def create_jsonl_from_py(task_id, py_file_path, jsonl_file_path):
    with open(py_file_path, 'r') as file:
        py_content = file.read()

    data = {'task_id':task_id,'completion': py_content}
    json_str = json.dumps(data)

    with open(jsonl_file_path, "a") as file:
        file.write(json_str + "\n")

# JSONL 文件路径
file_path = './dataset_gpt.jsonl'
save_path1 = './gpt3_5.jsonl'
save_path2 = './gpt3_5_fix.jsonl'
# 读取 JSONL 文件并提取 prompt 字段
task_ids_and_prompts = read_task_id_and_prompt(file_path)

#gpt API 调用
client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")

    # chatanywhere 接口和url
    # api_key="sk-INtPx15nQ1ap6V2O58o521QVGD15dA7zE4hLF4hma7d0UqEs",
    # api_key="sk-iWbh1fFyIJMHfjYHBCtuUI8dLmu6K0juuIAqztHftYtJpyFN",
    # base_url="https://api.chatanywhere.com.cn/v1"

    # 另一组 gpt-3.5 接口和url
    # api_key="sk-2vVkbI58nNaM2nil87D35c74F8424f75Bd6d35A717A8BeAf",
    # base_url="https://ai-yyds.com/v1"

    # 另一组 gpt-3.5 接口和url
    api_key="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",
    base_url="https://api.openai-forward.com"
)
# 打印每条数据中的 prompt 字段
for task_id, prompt in task_ids_and_prompts:
    response = client.chat.completions.create(
    model='gpt-3.5-turbo',
    messages=[
        {
            "role": "user",
            "content": prompt,
        },
    ],
)
    print(task_id)
    completion = prompt + response.choices[0].message.content
    data1 = {'task_id':task_id,'completion': completion}
    json_str = json.dumps(data1)
    with open(save_path1, "a") as file:
        file.write(json_str + "\n")

        