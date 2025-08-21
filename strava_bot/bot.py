import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from stravalib import Client
import datetime
import os

# Configura tu token de Telegram y credenciales de Strava aquí o usa variables de entorno
TELEGRAM_TOKEN = '8385186099:AAFGTOZFIG95hGrLbbFkZVbqBgyIVf66jNA'
STRAVA_CLIENT_ID = '173735'
STRAVA_CLIENT_SECRET = '32c6798f5a08290ba837a67e73e41afb0893df89'
STRAVA_ACCESS_TOKEN = '520f556f63644e887fc32b56ada924f0e573a2b0'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

strava_client = Client(access_token=STRAVA_ACCESS_TOKEN)

def get_today_activities():
    today = datetime.datetime.now().date()
    after = datetime.datetime.combine(today, datetime.time.min)
    before = datetime.datetime.combine(today, datetime.time.max)
    activities = strava_client.get_activities(after=after, before=before)
    return list(activities)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('¡Hola! Usa /hoy para ver tus actividades de Strava de hoy.')

async def hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        activities = get_today_activities()
        if not activities:
            await update.message.reply_text('No hay actividades registradas hoy.')
            return
        msg = 'Actividades de hoy en Strava:\n'
        for act in activities:
            msg += f"- {act.name}: {act.distance/1000:.2f} km en {act.moving_time}\n"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f'Error al obtener actividades: {e}')

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('hoy', hoy))
    print('Bot iniciado. Presiona Ctrl+C para detener.')
    app.run_polling()
