# 🔄 Workflow Hệ Thống AI Mô Tả Sản Phẩm

```mermaid
flowchart LR
    A[Người dùng] --> B[Frontend]
    B --> C[Backend FastAPI]
    C --> D[Google Gemini]
    C --> E[CSDL SQLite]
    D --> C
    E --> C
    C --> B
    B --> A
```
