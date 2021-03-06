import asyncio

from aiogram import Dispatcher, types
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled


class AntiFloodThrottlingMiddleware(BaseMiddleware):
    """Анти флуд мидлвара."""

    def __init__(self, limit=2, key_prefix='antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(AntiFloodThrottlingMiddleware, self).__init__()

    async def on_process_message(
            self,
            message: types.Message,
            data: dict,
    ) -> None:
        """
        Этот хэндлер вызывается, когда бот получает сообщение.

        :param message: объект Message
        :type message: Message
        :param data: данные пользователя
        :type data: dict

        :return: None
        :rtype: NoneType
        """

        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()
        if handler:
            limit: int = getattr(
                handler, 'throttling_rate_limit', self.rate_limit
            )
            key: str = getattr(
                handler, 'throttling_key', f"{self.prefix}_{handler.__name__}"
            )
        else:
            limit = self.rate_limit
            key = f"{self.prefix}_message"
        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            await self.message_throttled(message, t)
            raise CancelHandler()

    async def message_throttled(
            self,
            message: types.Message,
            throttled: Throttled
    ) -> None:
        """
        уведомляет юзера только о первом превышении лимита, и затем уведомляет
        о разблокировке.

        :param message: объект Message
        :type message: Message
        :param throttled: объект Throttled
        :type throttled: Throttled

        :return: None
        :rtype: NoneType
        """

        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()
        if handler:
            key: str = getattr(
                handler,
                'throttling_key',
                f"{self.prefix}_{handler.__name__}"
            )
        else:
            key: str = f"{self.prefix}_message"
        delta = throttled.rate - throttled.delta
        if throttled.exceeded_count <= 2:
            await message.reply(
                text='Слишком много запросов! Отправка сообщений ограничена.'
            )
        await asyncio.sleep(delta)
        thr = await dispatcher.check_key(key)
        if thr.exceeded_count == throttled.exceeded_count:
            await message.reply(text='Разблокировано.')
