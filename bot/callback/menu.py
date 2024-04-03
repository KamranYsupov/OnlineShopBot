from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InputMediaPhoto

from bot.db.orm_quires import (
    async_get_parent_categories,
    async_get_by_id,
    async_filter_category_by_parent,
    async_filter_items_by_subcategory,
    async_delete_basket,
    async_decrement_basket_quantity,
    async_increment_basket_quantity, async_get_user_baskets
)
from bot.keyboards.inline import (
    get_items_buttons,
    get_main_menu,
    get_categories_menu,
    get_subcategories_menu,
    get_default_kbd, get_user_basket, get_delivery_menu
)
from bot.utils.pagination import Paginator
from bot.config import ADMIN_SERVER_URL, SHOP_IMAGE_URL
from items.models import Category


class DeliveryState(StatesGroup):
    address: str = State()


def get_pages(paginator: Paginator):
    pagination_btns = dict()
    if paginator.has_previous():
        pagination_btns['◀ Пред.'] = 'previous'
    if paginator.has_next():
        pagination_btns['След. ▶'] = 'next'

    return pagination_btns


async def get_items_menu(level, subcategory, page_number):
    items = await async_filter_items_by_subcategory(subcategory=subcategory)
    paginator = Paginator(items, page_number=page_number)
    message = '<b>Нет товаров<b>'
    keyboard = await get_default_kbd(level, subcategory)

    if len(paginator.get_page()):
        item = paginator.get_page()[0]

        message = InputMediaPhoto(
            media=ADMIN_SERVER_URL + item.image.url,
            caption=
            f''f'<b>Название: </b>«{item.name}»\n\n'
            f'<b>Описание: </b> \n<i>{item.description}</i>\n\n'
            f'<b>Цена: </b> {item.price}руб.\n '
        )

        pagination_btns = get_pages(paginator)

        keyboard = await get_items_buttons(
            level=level,
            subcategory_id=subcategory.id,
            page_number=page_number,
            pagination_btns=pagination_btns,
            item_id=item.id
        )

    return message, keyboard


async def get_basket(level, menu_name, page_number, user_id, item_id):
    if menu_name == 'delete':
        await async_delete_basket(user_id, item_id)
        if page_number > 1: page_number -= 1
    elif menu_name == 'decrement':
        is_basket_exist = await async_decrement_basket_quantity(user_id, item_id)
        if page_number > 1 and not is_basket_exist: page_number -= 1
    elif menu_name == 'increment':
        await async_increment_basket_quantity(user_id, item_id)

    baskets = await async_get_user_baskets(user_id)

    if not baskets:
        message = InputMediaPhoto(
            media=SHOP_IMAGE_URL,
            caption=f'<strong>В корзине ничего нет</strong>'
        )

        keyboard = get_user_basket(
            level=level,
            page_number=None,
            pagination_btns=None,
            item_id=None,
        )
        return message, keyboard

    paginator = Paginator(baskets, page_number=page_number)
    basket = paginator.get_page()[0]

    basket_price = round(basket.quantity * basket.item.price)
    total_price = sum(basket.quantity * basket.item.price for basket in baskets)

    message = InputMediaPhoto(
        media=ADMIN_SERVER_URL + basket.item.image.url,
        caption=f'<strong>{basket.item.name}</strong>\n'
                f'{basket.item.price}руб. x {basket.quantity} = {basket_price}руб.'
                f'\nТовар {paginator.page_number} из {paginator.pages} в корзине.\n'
                f'Общая стоимость товаров в корзине {total_price} рублей',
    )

    pagination_btns = get_pages(paginator)

    keyboard = get_user_basket(
        level=level,
        page_number=page_number,
        pagination_btns=pagination_btns,
        item_id=basket.item.id,
    )

    return message, keyboard


async def get_delivery(state: FSMContext):
    await state.set_state(DeliveryState.address)

    return await get_delivery_menu()


async def cancel_delivery(state: FSMContext):
    await state.clear()

    return await get_main_menu(level=0)


async def get_menu_by_level(
        level: int,
        menu_name: str,
        category_id: str = None,
        subcategory_id: int | None = None,
        item_id: int | None = None,
        page_number: int | None = None,
        user_id: int | None = None,
        state: FSMContext = None,
):

    if menu_name == 'delivery':
        return await get_delivery(state)
    if menu_name == 'cancel':
        return await cancel_delivery(state)

    if level == 0:
        return await get_main_menu(level)

    elif level == 1:
        categories = await async_get_parent_categories()
        return await get_categories_menu(level, categories)

    elif level == 2:
        category = await async_get_by_id(Category, obj_id=category_id)
        subcategories = await async_filter_category_by_parent(
            parent_category=category
        )
        return await get_subcategories_menu(level, subcategories)

    elif level == 3:
        subcategory = await async_get_by_id(Category, obj_id=subcategory_id)
        return await get_items_menu(level, subcategory, page_number)
    elif level == 4:
        return await get_basket(level, menu_name, page_number, user_id, item_id)

