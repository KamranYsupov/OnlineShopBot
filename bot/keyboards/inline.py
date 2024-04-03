from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import InputMediaPhoto

from bot.db.orm_quires import async_get_by_id, async_get_subcat_parent_id
from bot.config import SHOP_IMAGE_URL
from items.models import Category


class MenuCallback(CallbackData, prefix='level'):
    level: int
    menu_name: str
    category_id: int | None = None
    subcategory_id: int | None = None
    item_id: int | None = None
    page_number: int | None = 1


async def get_default_kbd(level: int, subcategory: Category):
    keyboard = InlineKeyboardBuilder()

    parent_id = await async_get_subcat_parent_id(subcategory)

    keyboard.add(InlineKeyboardButton(
        text='Назад◀',
        callback_data=MenuCallback(
            level=level - 1,
            menu_name=subcategory.parent_category.name,
            category_id=parent_id,
        ).pack()
    ))

    keyboard.add(InlineKeyboardButton(
        text='Корзина 🛒',
        callback_data=MenuCallback(level=4, menu_name='Корзина 🛒').pack()
    ))

    return keyboard.as_markup()


async def get_items_buttons(
        level: int,
        item_id: int,
        subcategory_id: int,
        page_number: int,
        pagination_btns: dict,
        sizes: tuple[int] = (2,)):
    subcategory = await async_get_by_id(Category, obj_id=subcategory_id)

    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(
        text='Назад◀',
        callback_data=MenuCallback(
            level=level - 1,
            menu_name='main',
            category_id=subcategory.parent_category_id
        ).pack()
    ))
    keyboard.add(InlineKeyboardButton(
        text='Корзина 🛒',
        callback_data=MenuCallback(level=4, menu_name='Корзина 🛒').pack()
    ))

    keyboard.add(InlineKeyboardButton(
        text='Купить 💳',
        callback_data=MenuCallback(level=level, menu_name='add_to_basket', item_id=item_id).pack()
    ))

    row = []

    for text, menu_name in pagination_btns.items():
        if menu_name == 'next':
            row.append(InlineKeyboardButton(
                text=text,
                callback_data=MenuCallback(
                    level=level,
                    menu_name=menu_name,
                    item_id=item_id,
                    subcategory_id=subcategory_id,
                    page_number=page_number + 1,
                ).pack()
            ))
        elif menu_name == 'previous':
            row.append(InlineKeyboardButton(
                text=text,
                callback_data=MenuCallback(
                    level=level,
                    menu_name=menu_name,
                    item_id=item_id,
                    subcategory_id=subcategory_id,
                    page_number=page_number - 1,
                ).pack()
            ))

    keyboard.adjust(*sizes)
    return keyboard.row(*row).as_markup()


async def get_subcategories_menu(level: int, subcategories: list[Category], sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(
        text='Назад◀',
        callback_data=MenuCallback(
            level=level - 1,
            menu_name='parent_category.name',
            category_id=subcategories[0].parent_category_id if len(subcategories) else None).pack()
    ))
    keyboard.add(InlineKeyboardButton(
        text='Корзина 🛒',
        callback_data=MenuCallback(level=4, menu_name='Корзина 🛒').pack()
    ))

    for sub_cat in subcategories:
        keyboard.add(InlineKeyboardButton(
            text=sub_cat.name,
            callback_data=MenuCallback(
                level=level + 1,
                menu_name=sub_cat.name,
                subcategory_id=sub_cat.id,
            ).pack()
        ))

    message = InputMediaPhoto(
        media=SHOP_IMAGE_URL,
        caption='<b>Выберите категорию</b>'
    )

    return message, keyboard.adjust(*sizes).as_markup()


async def get_categories_menu(level: int, categories: list[Category], sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(
        text='Назад◀',
        callback_data=MenuCallback(level=level - 1, menu_name='main').pack()
    ))
    keyboard.add(InlineKeyboardButton(
        text='Корзина 🛒',
        callback_data=MenuCallback(level=4, menu_name='Корзина 🛒').pack()
    ))

    for cat in categories:
        keyboard.add(InlineKeyboardButton(
            text=cat.name,
            callback_data=MenuCallback(
                level=level + 1,
                menu_name=cat.name,
                category_id=cat.id,
            ).pack()
        ))

    message = InputMediaPhoto(
        media=SHOP_IMAGE_URL,
        caption='<b>Выберите категорию</b>'
    )

    return message, keyboard.adjust(*sizes).as_markup()


async def get_main_menu(level: int, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    buttons = {
        'Каталог 📇': 'catalog',
        'Корзина 🛒': 'basket',
        'FAQ': 'FAQ',
    }
    for text, menu_name in buttons.items():
        if menu_name == 'catalog':
            keyboard.add(InlineKeyboardButton(
                text=text,
                callback_data=MenuCallback(level=level + 1, menu_name=text).pack()
            ))
        elif menu_name == 'basket':
            keyboard.add(InlineKeyboardButton(
                text=text,
                callback_data=MenuCallback(level=4, menu_name=text).pack()
            ))
        else:
            keyboard.add(InlineKeyboardButton(
                text=text,
                callback_data=MenuCallback(level=level, menu_name=text).pack()
            ))

    message = InputMediaPhoto(
        media=SHOP_IMAGE_URL,
        caption='✅ Готово! Выбери категорию'
    )

    return message, keyboard.adjust(*sizes).as_markup()


def get_user_basket(
        *,
        level: int,
        page_number: int | None,
        pagination_btns: dict | None,
        item_id: int | None,
        sizes: tuple[int] = (3,)
):
    keyboard = InlineKeyboardBuilder()

    main_button = InlineKeyboardButton(
        text='На главную 🏠',
        callback_data=MenuCallback(level=0, menu_name='main').pack()
    )

    if page_number:
        keyboard.add(InlineKeyboardButton(
            text='Удалить',
            callback_data=MenuCallback(
                level=level,
                menu_name='delete',
                item_id=item_id,
                page_number=page_number
            ).pack()))
        keyboard.add(InlineKeyboardButton(
            text='-1',
            callback_data=MenuCallback(
                level=level,
                menu_name='decrement',
                item_id=item_id,
                page_number=page_number
            ).pack()))
        keyboard.add(InlineKeyboardButton(
            text='+1',
            callback_data=MenuCallback(
                level=level,
                menu_name='increment',
                item_id=item_id,
                page_number=page_number
            ).pack()))

        keyboard.adjust(*sizes)

        row = []
        for text, menu_name in pagination_btns.items():
            page = page_number
            if menu_name == 'next':
                page += 1
            elif menu_name == 'previous':
                page -= 1
            row.append(InlineKeyboardButton(
                text=text,
                callback_data=MenuCallback(
                    level=level,
                    menu_name=menu_name,
                    page_number=page
                ).pack()))

        keyboard.row(*row)

        row2 = [
            main_button,
            InlineKeyboardButton(
                text='Заказать 🚚',
                callback_data=MenuCallback(level=0, menu_name='delivery').pack()),
        ]
        return keyboard.row(*row2).as_markup()

    keyboard.add(main_button)

    return keyboard.adjust(*sizes).as_markup()


async def get_delivery_menu():
    message = InputMediaPhoto(
        media=SHOP_IMAGE_URL,
        caption='Отправьте адрес для доставки'
    )

    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(
        text='Отмена ❌',
        callback_data=MenuCallback(level=0, menu_name='cancel').pack()
    ))

    return message, keyboard.as_markup()



def get_inline_keyboard(*, buttons: dict[str, str], sizes: tuple = (1, 1)):
    keyboard = InlineKeyboardBuilder()

    for text, data in buttons.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()
