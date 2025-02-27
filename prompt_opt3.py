from openai import OpenAI
import json

# 调用 OpenAI API 获取响应
def call_api(messages, frequency_penalty=0, presence_penalty=0):
    client = OpenAI(
        api_key='sk-5d2d303c83bf46949ca6e003b3a57072',  # 你的 OpenAI API 密钥
        base_url="https://api.deepseek.com"
    )
    
    response = client.chat.completions.create(
        model="deepseek-chat",  # 使用的模型
        messages=messages,
        max_tokens=4096,
        temperature=0.7,  # 提高创造性
        stream=False,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        top_p=1,
    )
    
    # 返回 AI 的回复
    return response.choices[0].message.content.strip()

# 读取系统提示内容
def read_system_prompt(file_path):
    """读取系统提示内容"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()

# 读取并解析话题选项文本文件
def read_topic_options(file_path):
    """解析话题文件，返回每个场景及其话题"""
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
def generate_conversation_tree(initial_question, system_prompt1_file, system_prompt2_file, topic_option_file, rounds=3):
    system_prompt1 = read_system_prompt(system_prompt1_file)
    system_prompt2 = read_system_prompt(system_prompt2_file)
    
    # 读取并解析话题选项文件
    conversation_tree = read_topic_options(topic_option_file)
    
    # 检查 conversation_tree 是否为空，并打印一下它的内容
    print("Conversation Tree Loaded:")
    print(json.dumps(conversation_tree, ensure_ascii=False, indent=4))
    
    # 初始化消息
    messages_for_tester = [
        {"role": "system", "content": system_prompt1},
        {"role": "user", "content": initial_question},
    ]


    messages_for_tester = [
        {"role": "system", "content": system_prompt1},
        {"role": "user", "content": initial_question},
        {"role": "assistant", "content": system_prompt2},
        {"role": "user", "content": initial_question},
        
    ]

    m1

    m2
    
    messages_for_bot = [
        {"role": "system", "content": system_prompt2},
        {"role": "assistant", "content": initial_question},
    ]

    # 生成对话树
    dialog_tree = {}

    for i in range(rounds):
        # 创建 scene 标识符
        scene_id = f"scene{i+1}"

        if scene_id not in conversation_tree:
            print(f"场景 {scene_id} 不存在，跳过")
            continue
        
        # AI 生成问题（每轮开始时）
        ai_question = call_api(messages_for_tester)
        print(f"bot: {ai_question}")
        
        # 添加到消息历史
        messages_for_tester.append({"role": "assistant", "content": ai_question})
        messages_for_bot.append({"role": "user", "content": ai_question})

        # 获取当前场景的用户回复和AI回复
        user_reply = conversation_tree[scene_id]["user"]
        ai_reply = call_api(messages_for_tester)
        
        # 将场景信息保存
        dialog_tree[scene_id] = {
            "user": user_reply,
            "ai": ai_reply,
            "responses": []
        }

        # 对每个话题生成多个分支
        for topic_data in conversation_tree[scene_id]["responses"]:
            topic = topic_data["topic"]
            
            # 根据 AI 的回复生成多个用户回复
            user_replies = []
            for _ in range(3):  # 生成3个用户回复
                messages_for_bot.append({"role": "user", "content": ai_reply})
                
               
                user_reply = call_api(messages_for_bot)
                user_replies.append(user_reply)
            
            # 存储该话题的回复分支
            topic_responses = []
            for user_reply in user_replies:
                # 获取每个用户回复后的 AI 回复
                messages_for_bot.append({"role": "user", "content": user_reply})
                ai_reply = call_api(messages_for_tester)
                
                # 保存该分支的结果
                topic_responses.append({
                    "ai": ai_reply
                })
            
            dialog_tree[scene_id]["responses"].append({
                "topic": topic,
                "user": user_reply,
                "responses": topic_responses
            })
        
    return dialog_tree


if __name__ == '__main__':
    initial_question = "你怎么看待巴黎奥运会的开幕式？"  # 用户的第一句话
    system_prompt1_file = "/mnt/afs/chenyun/zhangjing/prompt_opt/system_prompt1.txt"  # 系统提示1文件路径
    system_prompt2_file = "/mnt/afs/chenyun/zhangjing/prompt_opt/system_prompt2.txt"  # 系统提示2文件路径
    topic_option_file = "/mnt/afs/chenyun/zhangjing/prompt_opt/topic_test.txt"  # 话题选项文件路径

    conversation_tree = generate_conversation_tree(initial_question, system_prompt1_file, system_prompt2_file, topic_option_file, rounds=3)
    
    # 输出为 JSON 格式
    print(json.dumps(conversation_tree, ensure_ascii=False, indent=4))
