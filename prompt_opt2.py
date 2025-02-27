import json
from openai import OpenAI

# 设定API调用
def call_api(messages, frequency_penalty=0, presence_penalty=0):
    client = OpenAI(
        api_key='',  
        base_url="https://api.deepseek.com"
    )
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        max_tokens=4096,
        temperature=0.5,
        stream=False,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        top_p=1,
    )
    return response

# 读取系统提示
def read_system_prompt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()

# 从场景文件中读取场景数据（处理文本格式）
def read_scenes_from_file(file_path):
    scenes = {}
    current_scene = None
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            
            if line.startswith("场景"):  # 场景标识
                current_scene = line.split(":")[0].strip()
                scenes[current_scene] = {
                    "user": "",
                    "AI": "",
                    "可能话题": [],
                    "responses": []  # 初始化 responses 为空列表
                }
                
            elif line.startswith("user:"):  # 用户输入
                scenes[current_scene]["user"] = line[len("user:"):].strip()
                
            elif line.startswith("AI:"):  # AI回应
                scenes[current_scene]["AI"] = line[len("AI:"):].strip()

             # 跳过“可能话题:”这一行，直接进入具体话题行
            elif line.startswith("可能话题:"):
                continue  # 跳过“可能话题:”这一行    

            elif line.startswith("-"):
            # 话题内容
                topic_name = line.split(":")[0].strip().strip("-")
                user_reply = line.split(":")[1].strip()
                scenes[current_scene]["可能话题"].append({
                            "topic": topic_name,
                            "user": user_reply
                        })
    
    return scenes

# 从场景中提取话题并生成模板
def extract_topics_and_generate_template(scenes, system_prompt1_file, system_prompt2_file):
    """
    从场景中提取话题并生成模板
    :param scenes: 输入场景数据，包含用户的对话和可能的讨论话题
    :param system_prompt1_file: 用户的系统提示文件路径
    :param system_prompt2_file: AI的系统提示文件路径
    :return: 返回生成的JSON模板
    """
    system_prompt1 = read_system_prompt(system_prompt1_file)  # 读取用户的系统提示
    system_prompt2 = read_system_prompt(system_prompt2_file)  # 读取AI的系统提示
    
    template = {}
    
    for scene_key, scene_data in scenes.items():
        user_input = scene_data["user"]  # 用户的初始输入
        ai_input = scene_data["AI"]  # AI的初始回应
        possible_topics = scene_data["可能话题"]  # 可能话题
        
        scene_responses = []
        
        for topic_data in possible_topics:
            topic = topic_data["topic"]
            user_input_for_topic = topic_data["user"]
            
            # 第一轮对话：用户的输入和AI的回应
            responses = [
                {
                    "topic": topic,
                    "user": user_input,
                    "responses": [
                        {"ai": ai_input}
                    ]
                }
            ]
            
            # 创建API调用消息
            messages_for_user = [{"role": "system", "content": system_prompt1.format(topic=topic)}]
            messages_for_ai = [{"role": "system", "content": system_prompt2.format(topic=topic)}]
            
            # 第二轮对话：用户根据AI的回应进行回答
            messages_for_user.append({"role": "user", "content": user_input_for_topic})
            
            # 获取AI回应第二轮
            response_ai = call_api(messages_for_ai)
            ai_response = response_ai.choices[0].message.content.strip() 
            
            # 保存第二轮对话
            responses.append({
                "topic": topic,
                "user": user_input_for_topic,
                "responses": [
                    {"ai": ai_response}
                ]
            })
            
            # 第三轮对话：继续根据话题生成对话
            messages_for_user.append({"role": "assistant", "content": ai_response})
            response_user = call_api(messages_for_user)
            user_input_second_round = response_user.choices[0].message.content.strip() 
            
            response_ai_second_round = call_api(messages_for_ai + [{"role": "user", "content": user_input_second_round}])
            ai_response_second_round = response_ai_second_round.choices[0].message.content.strip()
            
            # 保存第三轮对话
            responses.append({
                "topic": topic,
                "user": user_input_second_round,
                "responses": [
                    {"ai": ai_response_second_round}
                ]
            })
            
            scene_responses.append({
                "topic": topic,
                "user": user_input,
                "responses": responses
            })
        
        template[scene_key] = scene_responses
    
    return json.dumps(template, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    # 输入场景数据文本文件路径
    scenes_file_path = "/mnt/afs/chenyun/zhangjing/prompt_opt/topic_test.txt"  
    
    # 输入系统提示文件路径
    system_prompt1_file = "/mnt/afs/chenyun/zhangjing/prompt_opt/system_prompt1.txt"  
    system_prompt2_file = "/mnt/afs/chenyun/zhangjing/prompt_opt/system_prompt2.txt"  

    # 从文件读取场景数据
    scenes_input = read_scenes_from_file(scenes_file_path)
    
    # 生成JSON模板
    conversation_json = extract_topics_and_generate_template(scenes_input, system_prompt1_file, system_prompt2_file)
  
    #print(conversation_json)

    # 将生成的JSON保存到文件
    output_file_path = "/mnt/afs/chenyun/zhangjing/prompt_opt/output_template.json"  # 输出文件路径
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(conversation_json)
    
    print(f"JSON 模板已保存到文件: {output_file_path}")