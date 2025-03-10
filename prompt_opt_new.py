import json
from re import I
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

    #print('////////////////following is a message and a response/////////////')
    #print(f'message:{messages}\nresponse:{response.choices[0].message.content.strip()}')
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
        
        # 使用用户的第一句话作为场景的名字
        scene_name = user_input
        
        scene_responses = {}
        
        for topic_data in possible_topics:
            topic = topic_data["topic"]
            user_input_for_topic = topic_data["user"]
            
            # 第一轮对话：用户的输入和AI的回应
            first_round = {
                "user": user_input,
                "ai": ai_input,  # 直接使用输入中固定的AI回复
                topic: None  # 初始化第二轮对话为空
            }
            
            # 创建API调用消息（第一轮）
            messages_for_user_first_round = [{"role": "system", "content": system_prompt1.format(topic=topic)}]
            messages_for_ai_first_round = [{"role": "system", "content": system_prompt2.format(topic=topic)}]
            
            # 添加用户的第一轮输入
            messages_for_user_first_round.append({"role": "user", "content": user_input})
            messages_for_ai_first_round.append({"role": "user", "content": user_input})  
            
            # 第二轮对话：用户根据AI的回应进行回答
            messages_for_user_second_round = messages_for_user_first_round.copy()
            messages_for_user_second_round.append({"role": "user", "content": ai_input})  # 使用固定的AI回复
            messages_for_user_second_round.append({"role": "assistant", "content": user_input_for_topic})
            
            # 获取AI的第二轮回应
            response_ai_second_round = call_api(messages_for_ai_first_round + [
                {"role": "assistant", "content": ai_input},
                {"role": "user", "content": user_input_for_topic}
            ])
            ai_response_second_round = response_ai_second_round.choices[0].message.content.strip()
            
            # 第二轮对话
            second_round = {
                "user": user_input_for_topic,
                "ai": ai_response_second_round,
                topic: None  # 初始化第三轮对话为空
            }
            
            # 第三轮对话：继续根据话题生成对话
            for topic_data_third_round in possible_topics:
                topic_third_round = topic_data_third_round["topic"]
                user_input_for_topic_third_round = topic_data_third_round["user"]
                
                # 创建API调用消息（第三轮，针对用户）
                messages_for_user_third_round = [
                    {"role": "system", "content": system_prompt1.format(topic=topic_third_round)},  # 替换为当前topic
                    {"role": "assistant", "content": user_input},
                    {"role": "user", "content": ai_input},
                    {"role": "assistant", "content": user_input_for_topic},
                    {"role": "user", "content": ai_response_second_round}
                ]
                
                # 生成用户的第三轮输入
                response_user_third_round = call_api(messages_for_user_third_round)
                user_input_third_round = response_user_third_round.choices[0].message.content.strip()
                
                # 创建API调用消息（第三轮，针对AI）
                messages_for_ai_third_round = [
                    {"role": "system", "content": system_prompt2.format(topic=topic_third_round)},  # 替换为当前topic
                    {"role": "user", "content": user_input},  # 第一轮用户输入
                    {"role": "assistant", "content": ai_input},  # 第一轮AI回应
                    {"role": "user", "content": user_input_for_topic},  # 第二轮用户输入
                    {"role": "assistant", "content": ai_response_second_round},  # 第二轮AI回应
                    {"role": "user", "content": user_input_third_round}  # 第三轮用户输入
                ]
                
                # 获取AI的第三轮回应
                response_ai_third_round = call_api(messages_for_ai_third_round)
                ai_response_third_round = response_ai_third_round.choices[0].message.content.strip()
                
                # 第三轮对话
                third_round = {
                    "user": user_input_third_round,
                    "ai": ai_response_third_round
                }
                
                # 将第三轮对话嵌套到第二轮对话中
                second_round[topic_third_round] = third_round
            
            # 将第二轮对话嵌套到第一轮对话中
            first_round[topic] = second_round
            
            # 将第一轮对话嵌套到话题中
            scene_responses[topic] = first_round
        
        # 将话题嵌套到场景中
        template[scene_name] = scene_responses
    
    return json.dumps(template, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    # 输入场景数据文本文件路径
    scenes_file_path = "/mnt/afs/chenyun/zhangjing/prompt_opt/topic_option.txt"  
    
    # 输入系统提示文件路径
    system_prompt1_file = "/mnt/afs/chenyun/zhangjing/prompt_opt/system_prompt1.txt"  
    system_prompt2_file = "/mnt/afs/chenyun/zhangjing/prompt_opt/system_prompt2.txt"  

    # 从文件读取场景数据
    scenes_input = read_scenes_from_file(scenes_file_path)
    
    # 生成JSON模板
    conversation_json = extract_topics_and_generate_template(scenes_input, system_prompt1_file, system_prompt2_file)
    
    #print(conversation_json)

    # 将生成的JSON保存到文件
    output_file_path = "/mnt/afs/chenyun/zhangjing/prompt_opt/output_template_new.json"  # 输出文件路径
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(conversation_json)
    
    print(f"JSON 模板已保存到文件: {output_file_path}")