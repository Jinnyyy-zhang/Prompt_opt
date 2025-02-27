import json
from openai import OpenAI

# 调用 OpenAI API 获取响应
def call_api(messages, frequency_penalty=0, presence_penalty=0):
    client = OpenAI(
        api_key='',  # 你的 OpenAI API 密钥
        base_url="https://api.deepseek.com"
    )
    
    response = client.chat.completions.create(
        model="deepseek-chat",  # 模型名称
        messages=messages,
        max_tokens=4096,
        temperature=0.5,
        stream=False,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        top_p=1,
    )
    return response

# 读取系统提示内容
def read_system_prompt(file_path):
    """读取系统提示内容"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()

# 读取并解析话题选项文本文件
def read_topic_options(file_path):
    """解析 topic_option.txt 文件，返回话题树"""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    conversation_tree = {}
    current_scene = None
    current_topic = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("场景"):
            # 新场景
            scene_id = line.split(":")[0].strip()
            conversation_tree[scene_id] = {
                "user": "",
                "ai": "待生成",
                "responses": []
            }
            current_scene = scene_id
            current_topic = None
        
        elif line.startswith("user:"):
            # 用户对话
            conversation_tree[current_scene]["user"] = line.split(":", 1)[1].strip()
        
        elif line.startswith("AI:"):
            # AI对话
            conversation_tree[current_scene]["ai"] = line.split(":", 1)[1].strip()
        
        elif line.startswith("可能话题:"):
            # 开始话题的部分
            current_topic = []
            conversation_tree[current_scene]["responses"] = []
        
        elif line.startswith("-"):
            # 话题内容
            topic_name = line.split(":")[0].strip().strip("-")
            user_reply = line.split(":")[1].strip()
            conversation_tree[current_scene]["responses"].append({
                "topic": topic_name,
                "user": user_reply
            })
    
    return conversation_tree

# 生成对话树
def generate_conversation_tree(initial_question, system_prompt1_file, system_prompt2_file, rounds=2, branches=2):
    system_prompt1 = read_system_prompt(system_prompt1_file)
    system_prompt2 = read_system_prompt(system_prompt2_file)
    
    # 初始化消息
    messages_for_tester = [
        {"role": "system", "content": system_prompt1},
        {"role": "user", "content": initial_question},
    ]
    
    messages_for_bot = [
        {"role": "system", "content": system_prompt2},
        {"role": "assistant", "content": initial_question},
    ]
    
    # 对话树
    conversation_tree = {
        "scene1": {
            "user": initial_question,
            "ai": "待生成",
            "responses": []
        }
    }

    def recursive_dialogue(messages_for_tester, messages_for_bot, current_depth, branch_limit, parent_node):
        """递归生成对话树"""
        if current_depth >= branch_limit:
            return
        
        # 获取AI的回复
        response = call_api(messages_for_tester)
        print(response)  # 查看实际的返回结构
        ai_reply = response['choices'][0]['message']['content'].strip()
        #ai_reply = response.choices[0].message.content.strip() 
        
        # 更新对话树
        conversation_tree[parent_node]["ai"] = ai_reply
        
        # 获取用户的回复
        for i in range(branches):  # 控制分支数量
            response = call_api(messages_for_bot)
            user_reply = response['choices'][0]['message']['content'].strip()
            print(f"用户: {user_reply}")
            
            # 每个分支的主题和用户回复
            topic_name = f"话题{current_depth + 1}_{i + 1}"
            conversation_tree[parent_node]["responses"].append({
                "topic": topic_name,
                "user": user_reply,
                "responses": []  # 可以根据后续生成更深层的分支
            })
            
            # 更新对话历史
            messages_for_tester.append({"role": "assistant", "content": user_reply})
            messages_for_bot.append({"role": "user", "content": user_reply})

            # 递归处理用户回复生成下一层分支
            recursive_dialogue(messages_for_tester, messages_for_bot, current_depth + 1, branch_limit, f"{parent_node}_{topic_name}")

    # 启动对话树生成
    recursive_dialogue(messages_for_tester, messages_for_bot, 0, rounds, "scene1")
    
    return conversation_tree

# 保存对话树为JSON文件
def save_conversation_tree_to_json(conversation_tree, output_file):
    """将对话树保存为JSON文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(conversation_tree, f, ensure_ascii=False, indent=2)

# 主程序
if __name__ == '__main__':
    initial_question = "今天我超级开心！"  # 用户说的第一句话
    system_prompt1_file = "/mnt/afs/chenyun/zhangjing/prompt_opt/system_prompt1.txt"  # 系统提示1文件路径
    system_prompt2_file = "/mnt/afs/chenyun/zhangjing/prompt_opt/system_prompt2.txt"  # 系统提示2文件路径
    topic_option_file = "/mnt/afs/chenyun/zhangjing/prompt_opt/topic_test.txt"  # 话题选项文件路径

    # 读取并解析话题选项文件
    conversation_tree = read_topic_options(topic_option_file)
    
    # 打印解析的对话树
    print(json.dumps(conversation_tree, ensure_ascii=False, indent=2))
    
    # 生成对话树
    conversation_tree = generate_conversation_tree(initial_question, system_prompt1_file, system_prompt2_file, rounds=3, branches=2)
    
    # 保存对话树到 JSON 文件
    save_conversation_tree_to_json(conversation_tree, "conversation_tree_output.json")
    print("对话树已保存为 JSON 文件。")
