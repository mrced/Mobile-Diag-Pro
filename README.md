# 📱 Mobile-Diag-Pro

<p align="center">
  <img src="https://raw.githubusercontent.com/mrced/Mobile-Diag-Pro/main/assets/icons/app_icon.png" alt="Mobile-Diag-Pro Logo" width="120" onerror="this.style.display='none'"/>
</p>

<p align="center">
  <b>Ferramenta Profissional de Diagnóstico Avançado, Telemetria e Manutenção Android</b><br>
  <i>Interface moderna e elegante com design sóbrio inspirado no macOS (Dark & Light Mode).</i>
</p>

<p align="center">
  <a href="https://github.com/mrced/Mobile-Diag-Pro/stargazers"><img src="https://img.shields.io/github/stars/mrced/Mobile-Diag-Pro?style=for-the-badge&color=0a84ff" alt="Stars"></a>
  <a href="https://github.com/mrced/Mobile-Diag-Pro/issues"><img src="https://img.shields.io/github/issues/mrced/Mobile-Diag-Pro?style=for-the-badge&color=30d158" alt="Issues"></a>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/GUI-PySide6-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PySide6">
  <img src="https://img.shields.io/badge/OS-Windows%20|%20macOS%20|%20Linux-000000?style=for-the-badge" alt="OS Support">
</p>

---

## 🚀 Sobre o Projeto

O **Mobile-Diag-Pro** foi desenvolvido para atender à demanda de técnicos e entusiastas por uma ferramenta de diagnóstico profundo e reparo de celulares Android. Muitas soluções proprietárias no mercado cobram assinaturas elevadas — o Mobile-Diag-Pro entrega uma suíte completa, de alto desempenho e extensível, com preparação arquitetural para suportar dispositivos Apple (iOS) no futuro.

### 🌟 Destaques
- **🎨 Design Sóbrio & Elegante**: Interface inspirada no design language do macOS, com alternância instantânea entre **Dark Mode** e **Light Mode** e botões refinados.
- **🔌 Comunicação Híbrida**: Cliente de socket TCP nativo direto no servidor ADB (`:5037`) para telemetria de altíssima velocidade (latência de 2~5ms) + `QProcess` assíncrono para operações pesadas (Flash/Sideload).
- **🔬 Diagnóstico Profundo**: Mais de 50 testes automatizados cobrindo bateria (capacidade real vs design, contagem de ciclos, degradação), CPU por core, RAM/ZRAM, sensores, throttling térmico e integridade de partição.
- **⚡ Flasher & Recovery**: Suporte a partições físicas (Legacy/A-B) e dinâmicas (`super` container no `fastbootd`), desbloqueio de bootloader e ADB Sideload.
- **📈 Telemetria em Tempo Real**: Gráficos com aceleração gráfica (`pyqtgraph`) e buffers circulares sem travamentos na interface.
- **📦 Executável Portátil**: Pode ser distribuído como um único `.exe` ou instalador completo, trazendo os binários oficiais do `platform-tools` embutidos sem exigir que o cliente final instale Python ou ADB.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python 3.11+
- **Interface Gráfica**: PySide6 (Qt 6)
- **Gráficos e Sensores**: PyQtGraph
- **Motor de Comunicação**: Socket ADB Nativo + Android Platform Tools (ADB & Fastboot)
- **Arquitetura**: MVVM (Model-View-ViewModel) com threads em segundo plano

---

## 💻 Instalação e Execução (Desenvolvimento)

### Pré-requisitos
- Python 3.11 ou superior
- Git

### 1. Clonar o Repositório
```bash
git clone https://github.com/mrced/Mobile-Diag-Pro.git
cd Mobile-Diag-Pro
```

### 2. Criar e Ativar Ambiente Virtual
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Executar a Aplicação
```bash
python main.py
```

Você também pode iniciar diretamente com um tema específico:
```bash
python main.py --theme light
# ou
python main.py --theme dark --debug
```

---

## 📦 Como Gerar o Executável (.exe)

Para compilar a aplicação em um executável autônomo para Windows:

```bash
pip install pyinstaller

pyinstaller --noconfirm --onedir --windowed `
  --name "Mobile-Diag-Pro" `
  --add-data "assets;assets" `
  --hidden-import "pyqtgraph" `
  main.py
```

O executável final estará pronto dentro da pasta `dist/Mobile-Diag-Pro/`.

---

## 👨‍💻 Desenvolvedor

Desenvolvido por **[Onyalan S. Almeida](https://github.com/mrced/Mobile-Diag-Pro)**.

Se você gostou deste projeto ou ele foi útil para o seu trabalho, não se esqueça de deixar uma **⭐ Star** no repositório!
