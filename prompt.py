from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

def generate_situation(model_name, topic):
  messages = [
    {
      'role' : 'user',
      'content' : [
        {
          'type' : 'input_text',
          'text' : f'''
          당신은 공감 수업의 훌륭한 보조자입니다. 당신의 역할은 특정 주제에 맞는 간단한 갈등상황을 제시하고, 이에 적합한 공감적 대안들을 선택지로 생성하는 것입니다.
          선택지는 총 4개로 구성되며, 2개는 공감적 판단이 많이 포함된, 나머지 2개는 개인 위주 판단이 많이 포함된 선택지를 생성하면 됩니다.
          
          ** 주의 사항 **
          최종 출력 포맷은 리스트, 각각은 줄글로 출력할 것 ex) ['상황', '선택지1', '선택지2', '선택지3', '선택지4']
          대상은 중/고등학생으로 알아듣기 쉬운 단어를 사용할 것.
          교수자가 요구한 주제에 맞춘 상황을 제시할 것.

          주제 : {topic}\n
          '''
        }
      ]
    }
  ]

  response = client.responses.create(
        model = model_name,
        input = messages
    )
  
  return response.output_text