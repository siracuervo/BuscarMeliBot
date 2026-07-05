# Bot de búsqueda: Chevrolet Onix en Mercado Libre

Busca cada 30 minutos publicaciones de Chevrolet Onix en Mercado Libre Argentina
con transmisión automática, entre 10.000 y 55.000 km, año 2020 en adelante,
y te avisa por Telegram cuando aparece una nueva.

## 1. Crear el bot de Telegram (2 minutos)

1. Abrí Telegram y buscá **@BotFather**.
2. Enviale `/newbot`, elegí un nombre y un usuario (debe terminar en `bot`).
3. Te va a dar un **token** parecido a `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxx`. Guardalo.
4. Iniciá una conversación con tu bot recién creado (buscalo por su usuario y tocá "Start").

## 2. Obtener tu Chat ID

1. Enviale cualquier mensaje a tu bot (por ejemplo "hola").
2. Abrí en el navegador (reemplazando `<TOKEN>` por el tuyo):
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Buscá el campo `"chat":{"id": ...}` en la respuesta. Ese número es tu `TELEGRAM_CHAT_ID`.

## 3. Subir este proyecto a GitHub

1. Creá un repositorio nuevo en GitHub (puede ser privado).
2. Subí todos estos archivos (`ml_bot.py`, `requirements.txt`, `seen_ids.json`,
   la carpeta `.github/workflows/ml_bot.yml`, y este README).

```bash
git init
git add .
git commit -m "Bot de búsqueda Onix Mercado Libre"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

## 4. Configurar los secrets en GitHub

En el repo: **Settings → Secrets and variables → Actions → New repository secret**

- `TELEGRAM_BOT_TOKEN` → el token del paso 1
- `TELEGRAM_CHAT_ID` → el número del paso 2

## 5. Activar el workflow

- Andá a la pestaña **Actions** del repo.
- Si te pide habilitar Actions, aceptá.
- Podés correrlo manualmente con el botón **Run workflow** para probarlo,
  o esperar a que corra solo cada 30 minutos según el cron configurado.

## Ajustar los filtros

Todo lo que es criterio de búsqueda (modelo, año, km, transmisión, frecuencia)
está al principio de `ml_bot.py` y en el `cron` de `.github/workflows/ml_bot.yml`.
No hace falta tocar el resto del código para cambiar esos valores.

## Notas importantes

- Mercado Libre puede cambiar su API sin aviso; si el bot deja de traer
  resultados, revisá los logs en la pestaña Actions → click en la corrida → "Ejecutar bot".
- El bot evita mandarte la misma publicación dos veces gracias a `seen_ids.json`,
  que se actualiza y commitea solo en cada corrida.
- Si en algún momento el volumen de búsquedas crece mucho, Mercado Libre podría
  pedir autenticación (OAuth) para la API pública de búsqueda. Si eso pasa,
  avisame y adaptamos el bot para usar un access token de la app de Mercado Libre.
