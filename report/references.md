# References

이 파일은 제출용 보고서에서 언급한 평가 방법, RAG 설계, 모델 선정, safety gate 설계의 근거 자료를 한곳에 모은 참고문헌이다. 본 프로젝트는 아래 자료를 직접 구현 라이브러리로 모두 사용한 것이 아니라, 평가 항목과 실험 설계를 정리할 때 방법론적 근거로 참고했다.

## 1. Evaluation Methodology

- Liang, P., Bommasani, R., Lee, T., Tsipras, D., Soylu, D., Yasunaga, M., Zhang, Y., Narayanan, D., Wu, Y., Kumar, A., Newman, B., Yuan, B., Yan, B., Zhang, C., Cosgrove, C., Manning, C. D., Re, C., Acosta-Navas, D., Hudson, D. A., et al. (2022). *Holistic Evaluation of Language Models*. arXiv. https://arxiv.org/abs/2211.09110
  - 평가를 단일 정확도가 아니라 시나리오와 여러 지표의 조합으로 봐야 한다는 관점의 근거로 사용했다.

- Es, S., James, J., Espinosa-Anke, L., & Schockaert, S. (2023). *RAGAS: Automated Evaluation of Retrieval Augmented Generation*. arXiv. https://arxiv.org/abs/2309.15217
  - RAG 평가를 retrieval quality, faithfulness, answer relevance로 분리하는 관점의 근거로 사용했다. 본 프로젝트에서는 RAGAS 라이브러리를 직접 실행하지 않고, RAGAS-style 평가 구조를 참고했다.

- Saad-Falcon, J., Khattab, O., Potts, C., & Zaharia, M. (2023). *ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems*. arXiv. https://arxiv.org/abs/2311.09476
  - context relevance, answer faithfulness, answer relevance를 평가자 모델로 보는 후속 개선 후보의 근거로 사용했다.

- Min, S., Krishna, K., Lyu, X., Lewis, M., Yih, W.-t., Koh, P. W., Iyyer, M., Zettlemoyer, L., & Hajishirzi, H. (2023). *FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation*. arXiv. https://arxiv.org/abs/2305.14251
  - 답변을 원자적 사실 단위로 나누고 근거 지원 여부를 확인하는 평가 방향의 근거로 사용했다.

- Liu, Y., Iter, D., Xu, Y., Wang, S., Xu, R., & Zhu, C. (2023). *G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment*. arXiv. https://arxiv.org/abs/2303.16634
  - LLM-as-a-Judge 방식으로 답변 품질을 평가하는 후속 자동 채점 방향의 근거로 참고했다. 본 프로젝트에서는 직접 구현하지 않고 수동 rubric과 proxy 지표를 우선 사용했다.

- Confident AI. (2026). *DeepEval: The LLM Evaluation Framework*. https://github.com/confident-ai/deepeval
  - RAG/LLM 응답 평가를 테스트 코드처럼 자동화하는 후속 개선 후보로 참고했다. 2026-06 실험에서는 내부 CSV를 DeepEval RAG test case JSONL로 변환하는 어댑터를 추가했고, judge metric 실행은 평가자 모델과 threshold를 정한 뒤 진행할 후속 단계로 남겼다.

## 2. Retrieval and Model Selection

- Chen, J., Xiao, S., Zhang, P., Luo, K., Lian, D., & Liu, Z. (2024). *BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation*. arXiv. https://arxiv.org/abs/2402.03216
  - 한국어 포함 다국어, 긴 문서, dense/sparse/multi-vector retrieval을 지원하는 검색 모델 후보로 BGE-M3를 선정한 근거로 사용했다.

- Yang, A., Yang, B., Zhang, B., Hui, B., Zheng, B., Yu, B., Li, C., Liu, D., Huang, F., Wei, H., Lin, H., Yang, J., Tu, J., Zhang, J., Yang, J., Yang, S., Zhou, J., Lin, J., Dang, K., Lu, K., et al. (2024). *Qwen2.5 Technical Report*. arXiv. https://arxiv.org/abs/2412.15115
  - Qwen 계열 모델을 한국어 문서 QA와 구조화 문서 처리 후보로 검토한 배경 자료로 사용했다.

- Yang, A., Li, A., Yang, B., Zhang, B., Hui, B., Zheng, B., Yu, B., Gao, C., Huang, C., Lv, C., Zheng, C., Liu, D., Zhou, F., Huang, F., Hu, F., Ge, H., Wei, H., Lin, H., Tang, J., Tu, J., et al. (2025). *Qwen3 Technical Report*. arXiv. https://arxiv.org/abs/2505.09388
  - Qwen3의 다국어 지원, thinking/non-thinking 전환, 경량 모델군 구성을 모델 선정 근거로 참고했다.

- DeepSeek-AI, Guo, D., Yang, D., Zhang, H., Song, J., Zhang, R., Xu, R., Zhu, Q., Ma, S., Wang, P., Bi, X., Zhang, X., Yu, X., Wu, Y., Wu, Z. F., Gou, Z., Shao, Z., Li, Z., Gao, Z., et al. (2025). *DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning*. arXiv. https://arxiv.org/abs/2501.12948
  - 답변 생성 메인 모델보다는 오류 분석, reasoning 기반 평가자 후보로 검토한 근거로 사용했다.

## 3. Safety and Prompt Injection

- Chen, S., Piet, J., Sitawarin, C., & Wagner, D. (2024). *StruQ: Defending Against Prompt Injection with Structured Queries*. arXiv. https://arxiv.org/abs/2402.06363
  - instruction과 external data를 분리해야 한다는 관점의 근거로 사용했다.

- Wallace, E., Xiao, K., Leike, R., Weng, L., Heidecke, J., & Beutel, A. (2024). *The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions*. arXiv. https://arxiv.org/abs/2404.13208
  - 시스템 규칙, 답변 규칙, 사용자 질문, 검색 근거 사이의 우선순위를 명시하는 prompt template 개선 근거로 사용했다.

- Inan, H., Upasani, K., Chi, J., Rungta, R., Iyer, K., Mao, Y., Tontchev, M., Hu, Q., Fuller, B., Testuggine, D., & Khabsa, M. (2023). *Llama Guard: LLM-based Input-Output Safeguard for Human-AI Conversations*. arXiv. https://arxiv.org/abs/2312.06674
  - rule-based safety gate 이후 input-output safeguard classifier를 추가하는 후속 개선 방향의 근거로 사용했다.

- OWASP GenAI Security Project. (2024). *OWASP Top 10 for LLM Applications 2025*. https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/
  - prompt injection, data leakage, unsafe output 등 LLM application risk를 정리하는 보안 기준으로 참고했다.

## 4. Observability and Operations

- Datadog. (2026). *LLM Observability Documentation*. https://docs.datadoghq.com/ko/llm_observability/
  - 실제 서비스 운영 단계에서 request trace, latency, token usage, errors, quality/safety evaluation을 관찰해야 한다는 운영 관점의 참고 자료로 사용했다. 본 프로젝트에는 Datadog 연동을 구현하지 않고, logger/observability 후속 개선 방향으로만 반영했다.
