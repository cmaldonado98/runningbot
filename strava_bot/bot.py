import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from stravalib import Client
import datetime
import os
import requests

# Configura tu token de Telegram y credenciales de Strava aquí o usa variables de entorno
TELEGRAM_TOKEN = '8385186099:AAFGTOZFIG95hGrLbbFkZVbqBgyIVf66jNA'
STRAVA_CLIENT_ID = '173735'
STRAVA_CLIENT_SECRET = '32c6798f5a08290ba837a67e73e41afb0893df89'
STRAVA_ACCESS_TOKEN = '0233c0d0c5815a8d4d7b1ed46db538c1d6689f7b'
STRAVA_REFRESH_TOKEN = '39d1b99645e1ad8ba37a486310f48bc026fe5a46'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

strava_client = Client(access_token=STRAVA_ACCESS_TOKEN)

def get_today_activities():
    today = datetime.datetime.now().date()
    after = datetime.datetime.combine(today, datetime.time.min)
    before = datetime.datetime.combine(today, datetime.time.max)
    activities = strava_client.get_activities(after=after, before=before)
    return list(activities)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🏃‍♂️ ¡Hola! Soy tu bot de Strava.\n\n'
        'Comandos disponibles:\n'
        '/hoy - Ver tus actividades de hoy\n'
        '/start - Mostrar este mensaje'
    )

async def hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        activities = get_today_activities()
        if not activities:
            await update.message.reply_text('No hay actividades registradas hoy en Strava.')
            return
        
        msg = f'🏃‍♂️ Actividades de hoy ({datetime.datetime.now().strftime("%d/%m/%Y")}):\n\n'
        
        for i, act in enumerate(activities, 1):
            msg += f"--- Actividad {i} ---\n"
            # Mostrar toda la información completa del objeto activity
            for attr_name in dir(act):
                if not attr_name.startswith('_'):  # Excluir métodos privados
                    try:
                        attr_value = getattr(act, attr_name)
                        if not callable(attr_value):  # Excluir métodos
                            msg += f"{attr_name}: {attr_value}\n"
                    except:
                        pass  # Si hay error al obtener el atributo, continuar
            msg += "\n"
            
        # Telegram tiene límite de 4096 caracteres por mensaje
        if len(msg) > 4000:
            # Dividir en múltiples mensajes
            await update.message.reply_text(msg[:4000] + "...\n(Mensaje cortado - demasiada información)")
            if len(msg) > 4000:
                await update.message.reply_text("..." + msg[4000:8000])
        else:
            await update.message.reply_text(msg)
            
    except Exception as e:
        await update.message.reply_text(f'❌ Error al obtener actividades: {e}')

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('hoy', hoy))
    print('Bot iniciado. Presiona Ctrl+C para detener.')
    app.run_polling()
