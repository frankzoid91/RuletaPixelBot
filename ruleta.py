import httpx
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext
from telegram.ext import filters
import random
from httpx import Timeout, ReadTimeout

class RouletteBot:
    def __init__(self, token):
        self.token = token
        self.application = Application.builder().token(self.token).build()
        self.user_balances = {}  # Diccionario para almacenar el saldo de cada usuario
        self.current_bet_type = None  # Añadir esto para almacenar el tipo de apuesta actual
        self.photo_path = 'C:/Users/Asus/Desktop/Proyectos/RuletaBot/images/croupier.webp'  # Definir la ruta de la foto aquí
        # Definir los números rojos
        self.numeros_rojos = {32, 19, 21, 25, 34, 27, 36, 30, 23, 5, 16, 1, 14, 9, 18, 7, 12, 3}
        # Definir el color de los números
        self.colores = {0: 'verde'}
        for num in range(1, 37):
            if num in self.numeros_rojos:
                self.colores[num] = 'rojo'
            else:
                self.colores[num] = 'negro'
        
        # Configura un tiempo de espera más largo
        timeout_config = Timeout(10.0, connect=60.0)

        # Crea el cliente HTTP con el tiempo de espera configurado
        self._client = httpx.AsyncClient(timeout=timeout_config)
        
        # Handlers
        start_handler = CommandHandler('start', self.start)
        bet_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message)
        
        self.application.add_handler(start_handler)
        self.application.add_handler(bet_handler)

    async def start(self, update: Update, context: CallbackContext) -> None:
        user_id = update.message.from_user.id
        if user_id not in self.user_balances:
            self.user_balances[user_id] = 1000  # Inicializar saldo
        reply_keyboard = [
            ['🔴 Rojo', '⚫ Negro', '⚖️ Par', '⚖️ Impar'],
            ['1️⃣ Primera Docena', '2️⃣ Segunda Docena', '3️⃣ Tercera Docena'],
            ['🔢 Número Específico'],
            ['💰 Consultar Saldo', '🔙 Regresar al Casino']
        ]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_photo(
            photo=open(self.photo_path, 'rb'),
            caption="Bienvenido al juego de la ruleta! ¿Qué tipo de apuesta deseas hacer?",
            reply_markup=markup
        )

    async def handle_message(self, update: Update, context: CallbackContext) -> None:
        user_id = update.message.from_user.id
        text = update.message.text

        if text == '💰 Consultar Saldo':
            balance = self.user_balances.get(user_id, 0)
            await update.message.reply_text(f"Tu saldo actual es: {balance}")
            # Mostrar nuevamente los botones de apuestas después de mostrar el saldo
            reply_keyboard = [
                ['🔴 Rojo', '⚫ Negro', '⚖️ Par', '⚖️ Impar'],
                ['1️⃣ Primera Docena', '2️⃣ Segunda Docena', '3️⃣ Tercera Docena'],
                ['🔢 Número Específico'],
                ['💰 Consultar Saldo', '🔙 Regresar al Casino']
            ]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text("Selecciona el tipo de apuesta:", reply_markup=markup)
        elif text == '🔙 Regresar al Casino':
            # Por ahora no hace nada, pero aquí puedes añadir funcionalidad en el futuro
            await update.message.reply_text("Regresando al menú principal...")
        elif text == '🔢 Número Específico':
            self.current_bet_type = text
            await update.message.reply_text("Por favor, ingresa el número específico por el que deseas apostar (0-36).")
        elif self.current_bet_type == '🔢 Número Específico':
            try:
                specific_number = int(text.strip())
                if 0 <= specific_number <= 36:
                    await update.message.reply_text(f"Has seleccionado apostar por el número {specific_number}. Por favor, envía la cantidad que deseas apostar.")
                    self.current_bet_type = f"Número {specific_number}"
                else:
                    await update.message.reply_text("Por favor, ingresa un número válido entre 0 y 36.")
            except ValueError:
                await update.message.reply_text("Por favor, ingresa un número entero válido.")
        elif text in ['🔴 Rojo', '⚫ Negro', '⚖️ Par', '⚖️ Impar', '1️⃣ Primera Docena', '2️⃣ Segunda Docena', '3️⃣ Tercera Docena']:
            self.current_bet_type = text
            await update.message.reply_text(f"Has seleccionado apostar por {text}. Por favor, envía la cantidad que deseas apostar.")
        else:
            if self.current_bet_type:
                try:
                    amount = int(text.strip())  # Intentar convertir el texto a un número entero
                    user_balance = self.user_balances.get(user_id, 0)
                    if amount > user_balance:
                        await update.message.reply_text("Saldo insuficiente para realizar esta apuesta.")
                    elif amount > 0:
                        await self.process_bet(self.current_bet_type, amount, update, context)
                        self.current_bet_type = None  # Resetear el tipo de apuesta después de procesar
                    else:
                        await update.message.reply_text("Por favor, ingresa un número mayor que cero para la cantidad a apostar.")
                except ValueError:
                    await update.message.reply_text("Por favor, ingresa un número válido para la cantidad a apostar.")
            else:
                # Mostrar botones de tipo de apuesta si no se ha seleccionado uno
                reply_keyboard = [
                    ['🔴 Rojo', '⚫ Negro', '⚖️ Par', '⚖️ Impar'],
                    ['1️⃣ Primera Docena', '2️⃣ Segunda Docena', '3️⃣ Tercera Docena'],
                    ['🔢 Número Específico'],
                    ['💰 Consultar Saldo', '🔙 Regresar al Casino']
                ]
                markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
                await update.message.reply_text(
                    "Por favor, selecciona un tipo de apuesta primero.",
                    reply_markup=markup
                )

    async def process_bet(self, bet_type, amount, update, context):
        user_id = update.message.from_user.id
        result = random.randint(0, 36)
        color = self.colores[result]
        docena = (result - 1) // 12 + 1 if result != 0 else 0
        par_impar = "Par" if result % 2 == 0 else "Impar"

        if bet_type.startswith("Número"):
            specific_number = int(bet_type.split()[1])
            if result == specific_number:
                win_amount = amount * 32  # Pago de 32 a 1 para número específico
                self.user_balances[user_id] = self.user_balances.get(user_id, 0) + win_amount
                caption = f"¡Ganaste! El número resultante fue **{result}**. Apostaste **{amount}** y ganas **{win_amount}**. Tu nuevo saldo es **{self.user_balances[user_id]}**."
            else:
                self.user_balances[user_id] = self.user_balances.get(user_id, 0) - amount
                caption = f"Perdiste. El número resultante fue **{result}**. Apostaste **{amount}**. Tu nuevo saldo es **{self.user_balances[user_id]}**."
        elif bet_type in ['🔴 Rojo', '⚫ Negro']:
            if (bet_type == '🔴 Rojo' and color == 'rojo') or (bet_type == '⚫ Negro' and color == 'negro'):
                win_amount = amount * 2  # Pago de 2 a 1 para color
                self.user_balances[user_id] = self.user_balances.get(user_id, 0) + win_amount
                caption = f"¡Ganaste! El número **{result}** es {color}. Apostaste **{amount}** y ganas **{win_amount}**. Tu nuevo saldo es **{self.user_balances[user_id]}**."
            else:
                self.user_balances[user_id] = self.user_balances.get(user_id, 0) - amount
                caption = f"Perdiste. El número resultante fue **{result}** ({color}). Apostaste **{amount}**. Tu nuevo saldo es **{self.user_balances[user_id]}**."
        elif bet_type in ['⚖️ Par', '⚖️ Impar']:
            if (bet_type == '⚖️ Par' and par_impar == 'Par') or (bet_type == '⚖️ Impar' and par_impar == 'Impar'):
                win_amount = amount * 2  # Pago de 2 a 1 para par/impar
                self.user_balances[user_id] = self.user_balances.get(user_id, 0) + win_amount
                caption = f"¡Ganaste! El número **{result}** es {par_impar}. Apostaste **{amount}** y ganas **{win_amount}**. Tu nuevo saldo es **{self.user_balances[user_id]}**."
            else:
                self.user_balances[user_id] = self.user_balances.get(user_id, 0) - amount
                caption = f"Perdiste. El número resultante fue **{result}** ({par_impar}). Apostaste **{amount}**. Tu nuevo saldo es **{self.user_balances[user_id]}**."
        elif bet_type in ['1️⃣ Primera Docena', '2️⃣ Segunda Docena', '3️⃣ Tercera Docena']:
            if (bet_type == '1️⃣ Primera Docena' and docena == 1) or \
               (bet_type == '2️⃣ Segunda Docena' and docena == 2) or \
               (bet_type == '3️⃣ Tercera Docena' and docena == 3):
                win_amount = amount * 3  # Pago de 3 a 1 para docena
                self.user_balances[user_id] = self.user_balances.get(user_id, 0) + win_amount
                caption = f"¡Ganaste! El número **{result}** cae en la {docena}ª docena. Apostaste **{amount}** y ganas **{win_amount}**. Tu nuevo saldo es **{self.user_balances[user_id]}**."
            else:
                self.user_balances[user_id] = self.user_balances.get(user_id, 0) - amount
                caption = f"Perdiste. El número resultante fue **{result}** y cae en la {docena}ª docena. Apostaste **{amount}**. Tu nuevo saldo es **{self.user_balances[user_id]}**."
        else:
            caption = "Tipo de apuesta no reconocido o entrada inválida."

        try:
            await update.message.reply_photo(
                photo=open(self.photo_path, 'rb'),
                caption=caption,
                parse_mode='Markdown'
            )
        except ReadTimeout:
            print("La solicitud ha excedido el tiempo máximo de espera. Intentando nuevamente...")
            # Aquí puedes implementar una lógica para reintentar la solicitud o manejar el error de otra manera.

        # Preguntar si quiere volver a apostar
        reply_keyboard = [['✅ Sí', '❌ No']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            "¿Quieres hacer otra apuesta?",
            reply_markup=markup
        )

        # Añadir un manejador para la respuesta a esta pregunta
        response_handler = MessageHandler(filters.Regex('^(✅ Sí|❌ No)$'), self.handle_rebet_decision)
        self.application.add_handler(response_handler)

    async def handle_rebet_decision(self, update: Update, context: CallbackContext):
        text = update.message.text
        if text == '✅ Sí':
            reply_keyboard = [
                ['🔴 Rojo', '⚫ Negro', '⚖️ Par', '⚖️ Impar'],
                ['1️⃣ Primera Docena', '2️⃣ Segunda Docena', '3️⃣ Tercera Docena'],
                ['🔢 Número Específico'],
                ['💰 Consultar Saldo', '🔙 Regresar al Casino']
            ]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text("Selecciona el tipo de apuesta:", reply_markup=markup)

if __name__ == '__main__':    
    token = '6427622386:AAGVAApQxWi8dBVFzFqXLy_FNx8aRjvO-F8'
    bot = RouletteBot(token)
    bot.application.run_polling()  # Cambia bot.run() a bot.application.run_polling()