# Black Stories GenAI

## Extractor

O extractor lê as cartas-fonte em `content/cartas-enigma/run-extractor/`,
envia uma carta por vez à API Gemini e grava uma cópia enriquecida em
`content/cartas-enigma/facil/`, `medio/` ou `dificil/`, conforme o nível indicado
na carta.

### Configuração local

No PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Preencha `GEMINI_API_KEY` no `.env` com uma chave criada no Google AI Studio.
O arquivo `.env` é ignorado pelo Git. O acesso Google One/Plus não deve ser
considerado quota adicional da API; confirme no AI Studio o modelo e os limites
vigentes do nível gratuito.

### Execução

```powershell
.\.venv\Scripts\Activate.ps1
python src\extractor.py
```

O prompt utilizado está em `prompts/classificar-descobertas.md` e pode ser
revisado sem alterar o código. O modelo e o intervalo entre chamadas podem ser
alterados:

```powershell
python src\extractor.py --model gemini-3.1-flash-lite --delay 2
```

As cartas processadas mantêm o Markdown original e recebem a classificação ao
final. Compare-as manualmente com `docs/anotacoes-dev/descobertas-minimas.txt`.
