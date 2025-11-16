import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel('gemini-2.5-flash-lite')

def generate_selection(context):
  messages = f'''
          당신은 공감 수업의 참여자입니다. 당신의 역할은 리스트로 나온 선택지들 중에서 **배려/공감이 가장 적은** 선택지를 선택하고, 이에 타당한 논리를 제공하는 것입니다.
          선택지는 총 4개로 구성되며, 이 중에서 하나를 골라 해당 선택지의 번호와 줄글로 된 그 이유를 생성하면 됩니다.
          
          ** 주의 사항 **
          최종 출력 포맷은 리스트로 출력할 것 ex) [선택지 번호(정수형), '선택 이유']
          대상은 중/고등학생으로 선택 이유에 알아듣기 쉬운 단어를 사용할 것.
          논리적으로 타당한 이유를 들어 선택 이유를 작성할 것.
          제시된 선택지에서 첫번째 인덱스는 설명 글임.
          실제 선택지는 두번째 인덱스부터이며, 두번째 인덱스부터 0으로 번호가 시작 

          ** 예시 **
          선택지: 
          ['너와 친구가 시험 끝난 후 같이 영화를 보기로 했는데, 다른 친구가 같은 시간에 게임하러 오자고 했어. 너는 어떻게 할까?', 
          '친구에게 "우리가 약속한 게 먼저니까 영화를 같이 보자"라고 말한다.', 
          '게임하자고 한 친구에게 "오늘은 약속이 있어서 못 가, 다음에 같이 하자"라고 설명한다.', 
          '영화 약속을 깜빡한 척하고 그냥 게임하러 간다.', 
          '그냥 아무 말 안 하고 내가 더 하고 싶은 걸 선택한다.']
          
          답안:
          [3, '아무 말을 하지 않는 것이 상대방에게도 그렇고 나에게도 가장 문제 없을 것이라고 생각해. 그것을 말하면 오히려 상대방은 상처를 입을 수도 있으니까.. 그리고 그런 말을 전해야 한다는 것 자체가 나한테는 너무 부담이야.']

          선택지:
          {context}

          답안:
          '''
  
  response = model.generate_content(messages)
  
  return response.text

if __name__=="__main__":
  result = generate_situation('지우개 훔치기')
  print(result)