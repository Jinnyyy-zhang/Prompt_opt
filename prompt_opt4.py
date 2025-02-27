from openai import OpenAI
import json

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



def read_system_prompt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()

def multi_round_qa(initial_question, system_prompt1_file, system_prompt2_file, rounds=10):
    system_prompt1 = read_system_prompt(system_prompt1_file)
    system_prompt2 = read_system_prompt(system_prompt2_file)
    
    messages_for_tester = [
        {"role": "system", "content": system_prompt1},
        {"role": "user", "content": initial_question},
    ]
    
    messages_for_bot = [
        {"role": "system", "content": system_prompt2},
        {"role": "assistant", "content": initial_question},
    ]

    for i in range(rounds):
        # bot生成问题
        response = call_api(messages_for_tester)
        question = response.choices[0].message.content.strip()
        print(f"bot: {question}")
    
        messages_for_tester.append({"role": "assistant", "content": question})
        messages_for_bot.append({"role": "user", "content": question})

        # 用户生成回答
        response = call_api(messages_for_bot)
        answer = response.choices[0].message.content.strip()
        print(f"用户: {answer}")
        
        # 将用户的回答添加到对话历史中
        messages_for_bot.append({"role": "assistant", "content": answer})
        messages_for_tester.append({"role":"user","content":answer})
    return messages_for_bot,messages_for_tester


if __name__ == '__main__':
    initial_question = ""  # 用户说的第一句话
    system_prompt1_file = ""  
    system_prompt2_file = ""  

    final_messages = multi_round_qa(initial_question, system_prompt1_file, system_prompt2_file)
    print("对话结束")