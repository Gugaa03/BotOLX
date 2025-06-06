import discord
import requests
import json
import asyncio
from bs4 import BeautifulSoup
import os
import logging
from datetime import datetime, timedelta
import pytz

#TOKEN = ''  Substitua com o ID do seu Token
#CANAL_ID =   # Substitua com o ID do seu canal

JSON_FILE = "anuncios.json"

# Setup de logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# URLs das marcas
marcas = {
    'Famel': 'https://m.olx.pt/carros-motos-e-barcos/motociclos-scooters/famel/?search%5Border%5D=created_at:desc',
    'Kreidler': 'https://m.olx.pt/carros-motos-e-barcos/motociclos-scooters/kreidler/?search%5Border%5D=created_at:desc',
    'Sachs': 'https://m.olx.pt/carros-motos-e-barcos/motociclos-scooters/sachs/?search%5Border%5D=created_at:desc',
    'Zundapp': 'https://m.olx.pt/carros-motos-e-barcos/motociclos-scooters/zundapp/?search%5Border%5D=created_at:desc',
    'Cilindrado': 'https://www.olx.pt/carros-motos-e-barcos/motociclos-scooters/?search%5Border%5D=created_at:desc&search%5Bfilter_enum_cilindrada%5D%5B0%5D=ate-50-cc'
}

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def normalizar_link(link):
    return link.replace("/d/", "/")

def carregar_anuncios_json():
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def salvar_anuncios_json(novos_anuncios):
    dados_existentes = carregar_anuncios_json()
    links_existentes = {normalizar_link(item["link"]) for item in dados_existentes}
    anuncios_unicos = [a for a in novos_anuncios if normalizar_link(a["link"]) not in links_existentes]

    if anuncios_unicos:
        dados_existentes.extend(anuncios_unicos)
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(dados_existentes, f, indent=4, ensure_ascii=False)
        logging.info(f"{len(anuncios_unicos)} novos anúncios salvos no JSON.")
    else:
        logging.info("Nenhum novo anúncio para salvar.")

def buscar_anuncios(marca, url, anuncios_anteriores):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        anuncios = []
        lista_anuncios = soup.find_all('div', class_='css-1apmciz')

        for item in lista_anuncios:
            titulo_tag = item.find('h4')
            link_tag = item.find('a', href=True)
            imagem_tag = item.find('img')

            # Agora vamos procurar especificamente pelo parágrafo com a data
            preco = 'Preço não disponível'
            data = 'Data não disponível'
            
            # Procurar pela data no parágrafo específico
            data_tag = item.find('p', {'data-testid': 'location-date'})
            if data_tag:
                data = data_tag.text.strip()

            for p in item.find_all('p'):
                texto = p.text.strip()
                if '€' in texto and preco == 'Preço não disponível':
                    preco = texto

            titulo = titulo_tag.text.strip() if titulo_tag else 'Título não disponível'
            link = f"https://m.olx.pt{link_tag['href']}" if link_tag else 'Sem link'
            imagem = imagem_tag['src'] if imagem_tag else None

            link_normalizado = normalizar_link(link)
            if "Para o topo" in data:
                continue

            if link_normalizado not in anuncios_anteriores:
                # Agora, só adicionar o anúncio se a data contiver "Hoje"
                if "Hoje" in data:
                    anuncios.append({
                        'marca': marca,
                        'titulo': titulo,
                        'preco': preco,
                        'link': link_normalizado,
                        'imagem': imagem,
                        'data': data
                    })
                    logging.info(f"Novo anúncio encontrado: {titulo} ({marca})")

        return anuncios
    except requests.exceptions.RequestException as e:
        logging.error(f"Falha ao buscar anúncios para {marca}: {e}")
        return []


# Função para formatar a data
def formatar_data(data_texto):
    # Data e hora atual
    timezone = pytz.timezone('Europe/Lisbon')
    agora = datetime.now(timezone)
    
    logging.info(f"Data recebida para formatação: {data_texto}")  # Log da data recebida
    
    # Verificar se é "Hoje" ou "Ontem"
    if "Hoje" in data_texto:
        hora = agora.strftime('%H:%M')
        return f"Hoje às {hora}"
    elif "Ontem" in data_texto:
        ontem = agora - timedelta(days=1)
        hora = ontem.strftime('%H:%M')
        return f"Ontem às {hora}"
    else:
        # Caso a data seja diferente (caso do formato dd/mm/yyyy)
        try:
            data = datetime.strptime(data_texto, "%d/%m/%Y")
            return data.strftime("%d/%m/%Y")
        except ValueError:
            logging.warning(f"Data com formato inesperado: {data_texto}")  # Log para datas inesperadas
            return data_texto  # Caso a data não tenha o formato esperado

async def postar_anuncios():
    canal = client.get_channel(CANAL_ID)
    if not canal:
        logging.error("Canal do Discord não encontrado.")
        return

    todos_anuncios = []
    anuncios_anteriores = {normalizar_link(item["link"]) for item in carregar_anuncios_json()}

    for marca, url in marcas.items():
        anuncios = buscar_anuncios(marca, url, anuncios_anteriores)
        novos = [a for a in anuncios if normalizar_link(a["link"]) not in anuncios_anteriores]

        for anuncio in novos:
            # Verificar se a data contém a palavra "Hoje"
            logging.info(f"Data do anúncio: {anuncio['data']}")  # Log da data do anúncio
            if "Hoje" not in anuncio['data']:
                continue  # Ignorar se não for "Hoje"

            embed = discord.Embed(
                title=anuncio['titulo'],
                description=f"💰 Preço: {anuncio['preco']}\n📅 Data: {anuncio['data']}\n🔗 [Ver anúncio]({anuncio['link']})",
                color=discord.Color.blue()
            )
            if anuncio['imagem']:
                embed.set_image(url=anuncio['imagem'])

            await canal.send(f"🆕 **NOVO ANÚNCIO PARA {anuncio['marca'].upper()}**", embed=embed)
            logging.info(f"Anúncio postado: {anuncio['titulo']} ({anuncio['marca']})")

            anuncios_anteriores.add(normalizar_link(anuncio["link"]))
            todos_anuncios.append(anuncio)

    if todos_anuncios:
        salvar_anuncios_json(todos_anuncios)
    else:
        logging.info("Nenhum novo anúncio para postar.")

@client.event
async def on_ready():
    logging.info(f'Bot conectado como {client.user}')
    canal = client.get_channel(CANAL_ID)
    if canal:
        await canal.send("🤖 Bot OLX está online e pronto para buscar anúncios!")

    await postar_anuncios()
    while True:
        await postar_anuncios()
        await asyncio.sleep(300)  # Verifica a cada 5 minutos

if not TOKEN:
    logging.error("Token do Discord não definido! Define a variável de ambiente DISCORD_BOT_TOKEN.")
else:
    client.run(TOKEN)
