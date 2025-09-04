# 🎤 Transcrição de Áudio - AssemblyAI

Sistema web para transcrição automática de áudios usando AssemblyAI.

## 🚀 Funcionalidades

- **Upload de áudio** via interface web
- **Conversão automática** de formatos (M4A, AAC, OGG → MP3)
- **Transcrição em tempo real** com AssemblyAI
- **Identificação de falantes** automática
- **Download do resultado** em formato TXT
- **Barras de progresso** em tempo real

## 🎵 Formatos Suportados

- MP3, WAV, M4A, FLAC, AAC, OGG, OPUS

## 🛠️ Tecnologias

- **Backend:** Flask (Python)
- **Frontend:** HTML5, CSS3, JavaScript
- **API:** AssemblyAI
- **Deploy:** Render

## 📋 Pré-requisitos

- Python 3.8+
- FFmpeg (para conversão de áudio)
- API Key do AssemblyAI

## 🚀 Instalação

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/transcricao-audio.git
cd transcricao-audio
```

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Configure a API Key:**
Edite `transcription_service.py` e substitua a API key:
```python
self.api_key = "sua-api-key-aqui"
```

4. **Execute o projeto:**
```bash
python app.py
```

5. **Acesse:** http://localhost:5000

## 🌐 Deploy no Render

1. **Conecte seu repositório** no Render
2. **Configure como Web Service**
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `gunicorn app:app`
5. **Deploy!**

## 📁 Estrutura do Projeto

```
transcricao-audio/
├── app.py                 # Aplicação Flask principal
├── transcription_service.py # Serviço de transcrição
├── templates/
│   └── index.html         # Interface web
├── uploads/               # Arquivos enviados
├── results/               # Transcrições geradas
├── requirements.txt       # Dependências Python
└── README.md             # Este arquivo
```

## 🔧 Configuração

### Variáveis de Ambiente (Opcional)

```bash
ASSEMBLYAI_API_KEY=sua-api-key
MAX_FILE_SIZE=500MB
```

### API Key AssemblyAI

1. Acesse: https://www.assemblyai.com/
2. Crie uma conta gratuita
3. Obtenha sua API key
4. Substitua no código

## 📊 Como Usar

1. **Acesse o site**
2. **Faça upload** do arquivo de áudio
3. **Aguarde** o processamento
4. **Baixe** a transcrição

## 🔒 Limitações

- **Tamanho máximo:** 500MB por arquivo
- **Tempo de processamento:** Depende do tamanho do áudio
- **Formato de saída:** TXT com identificação de falantes

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT.

## 👨‍💻 Autor

André Diamand

## 📞 Suporte

Para dúvidas ou problemas, abra uma issue no GitHub.
# Versão atualizada Wed Sep  3 21:13:01 -05 2025
# Correção de logs e timeline Wed Sep  3 21:23:00 -05 2025
# Reescrever progresso sequencial Wed Sep  3 21:36:53 -05 2025
# FORÇAR DEPLOY - Wed Sep  3 21:41:28 -05 2025
# Desabilitar upload durante processamento Wed Sep  3 21:43:35 -05 2025
