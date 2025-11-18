# 배려와 공감 프로젝트 with AI

<p align="center">
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask Badge">
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5 Badge">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL Badge">
  <img src="https://img.shields.io/badge/Google%20Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini Badge">
</p>

## 프로젝트 개요
  이 프로젝트는 인공지능(AI)을 활용하여 학교 교육 현장에서 배려와 공감의 가치를 학습하고 실천하는 데 중점을 둔 웹 기반 상호작용 플랫폼입니다. 교사는 AI의 도움을 받아 몰입도 높은 역할극 투표 상황을 쉽게 생성하고, 학생들은 이 상황에 투표하고 의견을 제시하며 능동적으로 학습에 참여합니다. AI가 제공하는 '배려와 공감이 부족한' 시나리오에 직접 피드백하며 올바른 의사소통 방법을 체득하는 것이 목표입니다.

## 기술 스택
  웹 프레임워크: Flask (Python)
  프론트엔드: HTML / CSS / JavaScript
  데이터베이스: PostgreSQL
  AI: Gemini Flash 2.5 Lite

## 프로그램 구조 및 주요 기능
  프로그램은 교사용과 학생용 두 가지 주요 사용자 그룹의 상호작용으로 구성됩니다.
  1. 교사용 워크플로우
    1) 클래스룸 관리
      수업을 위한 독립적인 클래스룸을 생성하고 관리합니다.
    2) 투표 주제 생성
      교사가 원하는 주제를 입력하면, AI가 자동으로 해당 주제에 맞는 역할극 상황과 4가지 선택지를 생성하여 제공합니다.
    3) AI 투표 진행
      AI는 배려와 공감이 적게 나타나는 방식으로 투표를 진행합니다. 이 과정을 학생들이 관찰하고 AI에게 직접적인 피드백을 제공할 수 있도록 유도합니다.
    4) 결과 및 피드백 확인
      학생들이 투표한 내용, 투표 이유, AI에게 남긴 한마디 등을 실시간으로 확인하고 수업 자료로 활용합니다.
  2. 학생용 워크플로우
    1) 클래스룸 입장
      교사가 생성한 클래스룸 코드 등을 입력하여 해당 투표 페이지에 입장합니다.
    2) 투표 및 의견 제시
      역할극 선택지 투표를 진행합니다. -> 투표 이유를 간략하게 작성합니다. -> **"AI에게 한마디"**를 입력하여 배려와 공감에 대한 자신의 생각을 표현합니다.
    3) 상호 간 의사소통
      투표 결과를 바탕으로 교수자에게 자신의 의견을 발표하며 반 친구들과 생각을 공유합니다.

## 실행 방법
  웹사이트: www.sanhakieum.com
  회원가입 후 로그인하여 사용하시면 됩니다.
