import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel('gemini-2.5-flash-lite')

def generate_situation(topic):
  messages = f'''
          당신은 공감 수업의 훌륭한 보조자입니다. 당신의 역할은 특정 주제에 맞는 간단한 갈등상황을 제시하고, 이에 적합한 공감적 대안들을 선택지로 생성하는 것입니다.
          선택지는 총 4개로 구성되며, 2개는 공감적 판단이 많이 포함된, 나머지 2개는 개인 위주 판단이 약간 더 포함된 선택지를 생성하면 됩니다.
          
          ** 주의 사항 **
          최종 출력 포맷은 리스트로 출력할 것 ex) ['상황', '선택지1', '선택지2', '선택지3', '선택지4']
          대상은 중/고등학생으로 알아듣기 쉬운 단어를 사용할 것.
          교수자가 요구한 주제에 맞춘 상황을 제시할 것.

          ** 예시 **
          주제 : 친구와의 약속\n
          ['너와 친구가 시험 끝난 후 같이 영화를 보기로 했는데, 다른 친구가 같은 시간에 게임하러 오자고 했어. 너는 어떻게 할까?', 
          '친구에게 "우리가 약속한 게 먼저니까 영화를 같이 보자"라고 말한다.', 
          '게임하자고 한 친구에게 "오늘은 약속이 있어서 못 가, 다음에 같이 하자"라고 설명한다.', 
          '영화 약속을 깜빡한 척하고 그냥 게임하러 간다.', 
          '그냥 아무 말 안 하고 내가 더 하고 싶은 걸 선택한다.']


          주제 : {topic}\n
          '''
  
  response = model.generate_content(messages)
  
  return response.text

if __name__=="__main__":
  result = generate_situation('지우개 훔치기')
  print(result)