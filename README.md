# BotOLX

Um bot de Discord que monitora anúncios de motociclos no OLX Portugal e posta automaticamente os novos anúncios em um canal do Discord.

---

## Funcionalidades

- Busca anúncios de marcas específicas no OLX (Famel, Kreidler, Sachs, Zundapp e anúncios até 50cc).
- Filtra apenas os anúncios publicados **hoje**.
- Posta os novos anúncios em um canal do Discord com título, preço, data, link e imagem.
- Evita repostar anúncios já enviados utilizando um arquivo JSON (`anuncios.json`) para armazenamento local.
- Roda continuamente, verificando novos anúncios a cada 5 minutos.

---

## Requisitos

- Python 3.10+
- Bibliotecas Python:
  - `discord.py`
  - `requests`
  - `beautifulsoup4`
  - `pytz`
  - `asyncio` (built-in)
  - `logging` (built-in)
  - `json` (built-in)

Instalação rápida das dependências:

```bash
pip install discord.py requests beautifulsoup4 pytz
