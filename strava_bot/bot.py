import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
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

def get_activities_by_date(date_str):
    try:
        # Convertir string de fecha a objeto datetime
        target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        after = datetime.datetime.combine(target_date, datetime.time.min)
        before = datetime.datetime.combine(target_date, datetime.time.max)
        activities = strava_client.get_activities(after=after, before=before)
        return list(activities)
    except ValueError:
        raise ValueError("Formato de fecha inválido. Usa YYYY-MM-DD (ej: 2025-08-21)")

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
        '/fecha - Buscar actividades por fecha\n'
        '/start - Mostrar este mensaje'
    )

async def hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        activities = get_today_activities()
        if not activities:
            await update.message.reply_text('No hay actividades registradas hoy en Strava.')
            return
        
        # Crear contenido para el archivo
        content = f'Actividades de hoy ({datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")})\n'
        content += '=' * 50 + '\n\n'
        
        for i, act in enumerate(activities, 1):
            content += f"--- Actividad {i} ---\n"
            # Mostrar toda la información completa del objeto activity
            for attr_name in dir(act):
                if not attr_name.startswith('_'):  # Excluir métodos privados
                    try:
                        attr_value = getattr(act, attr_name)
                        if not callable(attr_value):  # Excluir métodos
                            content += f"{attr_name}: {attr_value}\n"
                    except:
                        pass  # Si hay error al obtener el atributo, continuar
            content += "\n" + "="*50 + "\n\n"
        
        # Guardar en archivo temporal
        filename = f"actividades_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)
        
        # Enviar archivo al usuario
        with open(filepath, 'rb') as file:
            await update.message.reply_document(
                document=file,
                filename=filename,
                caption=f'📋 Actividades de Strava del {datetime.datetime.now().strftime("%d/%m/%Y")}'
            )
        
        # Eliminar archivo temporal después de enviarlo
        os.remove(filepath)
        
    except Exception as e:
        await update.message.reply_text(f'❌ Error al obtener actividades: {e}')

async def fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Verificar si se proporcionó una fecha como argumento
    if context.args and len(context.args) > 0:
        date_str = context.args[0]
        await buscar_por_fecha(update, date_str)
    else:
        # Mostrar selector de fechas recientes
        today = datetime.datetime.now()
        keyboard = []
        
        # Crear botones para los últimos 7 días
        for i in range(7):
            date = today - datetime.timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            display_name = date.strftime('%d/%m/%Y')
            if i == 0:
                display_name += " (Hoy)"
            elif i == 1:
                display_name += " (Ayer)"
            
            keyboard.append([InlineKeyboardButton(display_name, callback_data=f"date_{date_str}")])
        
        # Botón para fecha personalizada
        keyboard.append([InlineKeyboardButton("📅 Otra fecha (YYYY-MM-DD)", callback_data="custom_date")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📅 Selecciona una fecha para buscar actividades:\n\n"
            "También puedes usar: /fecha YYYY-MM-DD\n"
            "Ejemplo: /fecha 2025-08-20",
            reply_markup=reply_markup
        )

async def handle_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("date_"):
        date_str = query.data[5:]  # Remover "date_" prefix
        await buscar_por_fecha(query, date_str)
    elif query.data == "custom_date":
        await query.edit_message_text(
            "📅 Envía la fecha en formato YYYY-MM-DD\n"
            "Ejemplo: 2025-08-20\n\n"
            "Usa /fecha YYYY-MM-DD"
        )

async def buscar_por_fecha(update_or_query, date_str):
    try:
        # Determinar si es un mensaje o callback query
        if hasattr(update_or_query, 'callback_query'):
            # Es un callback query
            chat_id = update_or_query.callback_query.message.chat_id
            send_message = lambda text: update_or_query.callback_query.message.reply_text(text)
            send_document = lambda doc, filename, caption: update_or_query.callback_query.message.reply_document(
                document=doc, filename=filename, caption=caption)
        else:
            # Es un mensaje normal
            chat_id = update_or_query.message.chat_id
            send_message = update_or_query.message.reply_text
            send_document = update_or_query.message.reply_document
        
        activities = get_activities_by_date(date_str)
        
        if not activities:
            await send_message(f'No hay actividades registradas el {date_str} en Strava.')
            return
        
        # Crear contenido para el archivo
        date_formatted = datetime.datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
        content = f'Actividades del {date_formatted}\n'
        content += f'Fecha de consulta: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n'
        content += '=' * 50 + '\n\n'
        
        for i, act in enumerate(activities, 1):
            content += f"--- Actividad {i} ---\n"
            # Mostrar toda la información completa del objeto activity
            for attr_name in dir(act):
                if not attr_name.startswith('_'):  # Excluir métodos privados
                    try:
                        attr_value = getattr(act, attr_name)
                        if not callable(attr_value):  # Excluir métodos
                            content += f"{attr_name}: {attr_value}\n"
                    except:
                        pass  # Si hay error al obtener el atributo, continuar
            content += "\n" + "="*50 + "\n\n"
        
        # Guardar en archivo temporal
        filename = f"actividades_{date_str.replace('-', '')}.txt"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)
        
        # Enviar archivo al usuario
        with open(filepath, 'rb') as file:
            await send_document(
                document=file,
                filename=filename,
                caption=f'📋 Actividades de Strava del {date_formatted}'
            )
        
        # Eliminar archivo temporal después de enviarlo
        os.remove(filepath)
        
    except ValueError as ve:
        await send_message(f'❌ {str(ve)}')
    except Exception as e:
        await send_message(f'❌ Error al obtener actividades: {e}')

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('hoy', hoy))
    app.add_handler(CommandHandler('fecha', fecha))
    app.add_handler(CallbackQueryHandler(handle_date_callback))
    print('Bot iniciado. Presiona Ctrl+C para detener.')
    app.run_polling()
