BOT do Telegram responsável por gerar relatórios gerenciais do sistema Industry Care

## Configuração do ambiente de desenvolvimento:

- [Instalar Webhook]

--> Ngrok (https://ngrok.com/download).
  
- [Configurar Túnel]

--> Ao instalar o Ngrok, um diretório .ngrok2 será criado na pasta raiz do sistema, contendo o arquivo de configuração ngrok.yml. Abra este arquivo em um editor de texto, exclua todo o conteúdo e cole e o seguinte conteúdo (a idendação deve ser respeitada) e salve o arquivo:

authtoken: #######

region: sa

tunnels:
  testbot: 
    proto: http
    hostname: #########
    addr: 127.0.0.1:8500
    inspect: true

--> Instalar o snap do Ngrok
```
$ sudo snap install ngrok
```

--> Registrar webhook na API do Telegram


--> Rodar aplicação

A aplicação deve ser executada no local host, porta 8500, que é o caminho para o qual o Webhook está apontando.
```
$ python3 manage.py runserver 127.0.0.1:8500
```


Unzip to uninstall: unzip /path/to/ngrok.zip (ideal colocar na pasta raiz do software e adicioná-lo ao .gitignore)
Connect your account: ./ngrok authtoken 1oWJRTXONGJINIZGyAosh8omM5Q_5yUXjAb8SYxh7KPTQwCm9
Start a HTTP Tunnel: ./ngrok http 80 (ideal abrir em um terminal fora do editor de texto)

-------------------------------------- Exemplo de interface ngrok --------------------------------------

Web Interface http://127.0.0.1:4040
Forwarding http://9876115b8c2d.ngrok.io -> http://localhost:80 Forwarding https://9876115b8c2d.ngrok.io -> http://localhost:80

A URL https deverá ser adicionada em seu Allowed Hosts (settings) sempre que for atualizada.

-------------------------------------- Exemplo de Allowed Hosts --------------------------------------

ALLOWED_HOSTS = ['industryca###########']

Feito isto, agora é necessário setar o webhook junto a API do Telegram.

Em um navegador, digite:

https://api.telegram.org/bot{TOKEN}/setWebHook?url={URL WEBHOOK}/ Lembrando que a URL Webhook é a mesma gerada pelo ngrok e permitida em Settings.

-------------------------------------- Exemplo de Set Webhook --------------------------------------

https://api.telegram.org/bot1991213103:AAHyK__vA0AygIXk8KfQ0Z4oALXgYEFhEFM/setWebHook?url=https://industrycaretestbot.sa.ngrok.io/event/


-------------------------------------- Configuração ngrok --------------------------------------
authtoken: ###############
region: sa

tunnels:
  testbot: 
    proto: http
    hostname: industry###########
    addr: 127.0.0.1:8500
    inspect: true