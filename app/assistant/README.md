# app/assistant (Judgment Assist)

- 목적: 메인 코어/사람의 판단 시간을 줄이는 "보조 엔진"
- 금지: 결론/집행/판단 (Read / Propose Only)
- 역할(role):
  - summarize: 요약/정리
  - risk_countercase: 리스크/반례 정렬
  - evidence_priority: 근거 압축/우선순위화
- 향후: 외부 LLM/API를 붙여도 contract.py는 SSOT로 고정
