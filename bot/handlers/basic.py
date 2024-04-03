import os

import aiogram
from aiogram import Router, types, F
from aiogram.enums import ChatMemberStatus
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InputMediaPhoto
from django.conf import settings
from django.contrib.auth import get_user_model

from bot.db.orm_quires import (
    async_get_by_id,
    async_create_user,
    async_filter_category_by_parent,
    async_filter_items_by_subcategory,
    async_get_parent_categories,
    async_add_to_basket,
    async_get_total_basket_price,
)
from bot.keyboards.inline import get_inline_keyboard
from bot.callback.menu import get_menu_by_level, DeliveryState
from bot.keyboards.inline import MenuCallback
from bot.config import SHOP_IMAGE_URL
from items.models import Item, Category

basic_router = Router()
User = get_user_model()


class BasketContext(StatesGroup):
    quantity = State()


@basic_router.message(CommandStart())
async def start_command_handler(message: types.Message):

    await message.answer_photo(
            photo=SHOP_IMAGE_URL,
            caption='Добро пожаловать в магазин!\n'
                    'Для начала подпишись на тг канал:\n\n some_link',
            reply_markup=get_inline_keyboard(
                buttons={
                    'Проверить': 'check',
                })
        )

    await async_create_user(message)


@basic_router.callback_query(F.data == 'check')
async def subscriptions_checker(callback: types.CallbackQuery):
    # result = await callback.bot.get_chat_member(
    #     chat_id=6145206276, user_id=callback.from_user.id
    # )
    # if result.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
    #     await callback.answer('Подпишись на все каналы', show_alert=True)
    # else:
    message, reply_markup = await get_menu_by_level(level=0, menu_name='main')
    await callback.message.edit_caption(
            caption='✅ Готово! Выбери категорию',
            reply_markup=reply_markup
        )


@basic_router.callback_query(MenuCallback.filter())
async def callback_user_actions(
        callback: types.CallbackQuery,
        callback_data: MenuCallback,
        state: FSMContext
):
    if callback_data.menu_name == 'add_to_basket':
        user = await async_get_by_id(User, obj_id=callback.from_user.id, external=True)
        item = await async_get_by_id(Item, obj_id=callback_data.item_id)
        await async_add_to_basket(user, item)
        await callback.answer(
            f'Товар «{item.name}» успешно добавлен в корзину',
            show_alert=True
        )

    message, reply_markup = await get_menu_by_level(
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category_id=callback_data.category_id,
        subcategory_id=callback_data.subcategory_id,
        item_id=callback_data.item_id,
        page_number=callback_data.page_number,
        user_id=callback.from_user.id,
        state=state,
    )

    await callback.message.edit_media(
            media=message,
            caption=message.caption,
            reply_markup=reply_markup,
        )


@basic_router.message(DeliveryState.address)
async def order_product(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.clear()

    price = await async_get_total_basket_price(message.from_user.id)
    await message.answer_invoice(
        'Покупка',
        'Оплата товаров из корзины',
        'invoice',
        os.getenv('PAYMENT_TOKEN'),
        'RUB',
        [types.LabeledPrice(
            label='Товары из корзины',
            amount=price * 100,
        )]

    )


@basic_router.message(F.content_type == types.ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment_handler(message: types.Message):
    await message.answer('Оплата прошла успешно ✔!')
#
#
# @basic_router.callback_query(MenuCallback.filter())
# async def subcategories_callback(callback: types.CallbackQuery, callback_data: MenuCallback):
#     category_id = MenuCallback.category_id
#     category = await async_get_by_id(Category, obj_id=category_id)
#     subcategories = await async_filter_category_by_parent(
#         parent_category=category
#     )
#
#     reply_markup = await get_menu_by_level(
#         level=MenuCallback.level,
#         menu_name='subcategories',
#         categories=subcategories,
#     )
#
#     await callback.message.edit_reply_markup(
#         reply_markup=reply_markup
#     )


@basic_router.callback_query(F.data.startswith('sub_cat_'))
async def subcategory_items_callback(callback: types.CallbackQuery):
    subcategory_id = int(callback.data.split('_')[-1])
    subcategory = await async_get_by_id(Category, obj_id=subcategory_id)
    items = await async_filter_items_by_subcategory(subcategory=subcategory)

    await callback.message.edit_text(
        text=f'Выбери товар из категории {subcategory.name}',
        reply_markup=get_inline_keyboard(
            buttons={item.name: f'item_{item.id}' for item in items},
            sizes=(2, 1)
        )
    )


@basic_router.callback_query(F.data.startswith('item_'))
async def item_callback(callback: types.CallbackQuery):
    item_id = int(callback.data.split('_')[-1])
    item = await async_get_by_id(Item, obj_id=item_id)
    await callback.message.edit_text(
        text=(
            f'{item.image}\n\n'
            f''f'<b>Название: </b>«{item.name}»\n\n'
            f'<b>Описание: </b> \n<i>{item.description}</i>\n\n'
            f'<b>Цена: </b> {item.price}руб.\n '
        ), parse_mode='HTML',
        reply_markup=get_inline_keyboard(
            buttons={'Добавить в корзину': f'add_to_basket_{item.id}_{item.name}'},
        )
    )


@basic_router.callback_query(F.data.startswith('add_to_basket_'))
async def add_item_to_basket(callback: types.CallbackQuery):
    item_id = int(callback.data.split('_')[-2])
    item_name = callback.data.split('_')[-1]

    await callback.message.edit_text(
        text=(
            f'Перед добавлением в корзину товар <i>«{item_name}»</i>,'
            f'нажмите кнопку "Подтвердить" \n\n'
        ), parse_mode='HTML',
        reply_markup=get_inline_keyboard(
            buttons={'Подтвердить': f'consider_{item_id}'},
        )
    )


@basic_router.callback_query(F.data.startswith('consider_'))
async def add_item_to_basket(callback: types.CallbackQuery):
    item_id = int(callback.data.split('_')[-1])
    item = await async_get_by_id(Item, obj_id=item_id)
    user = await async_get_by_id(User, obj_id=callback.from_user.id, external=True)
    basket = await async_add_to_basket(user, item, quantity=1)

    await callback.message.edit_text(
        text=(
            f'Товар «{item.name}» успешно добавлен в корзину!\n\n'
        ), parse_mode='HTML',
    )
