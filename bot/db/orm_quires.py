from aiogram import types
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db.models import Model, ObjectDoesNotExist

from items.models import Item, Category, Basket

User = get_user_model()


@sync_to_async
def async_get_all(
        model: Model,
        selected_fields: list = None,
        prefetched_fields: list = None
) -> list:
    if selected_fields and prefetched_fields:
        objects = (model.objects
                   .select_related(*selected_fields)
                   .prefetch_related(*prefetched_fields))
    elif selected_fields:
        objects = model.objects.select_related(*selected_fields)
    elif prefetched_fields:
        objects = model.objects.prefetch_related(*prefetched_fields)
    else:
        objects = model.objects.all()

    return list(objects)


@sync_to_async
def async_get_by_id(model: Model, obj_id: int, external: bool = False) -> list:
    if external:
        return model.objects.get(external_id=obj_id)
    return model.objects.get(id=obj_id)


@sync_to_async
def async_create_user(message: types.Message):
    User.objects.get_or_create(
        external_id=message.from_user.id,
        username=message.from_user.username,
    )


@sync_to_async
def async_filter_category_by_parent(parent_category):
    return list(
        Category.objects.filter(parent_category=parent_category)
        .select_related('parent_category')
    )


@sync_to_async
def async_filter_items_by_subcategory(subcategory):
    return list(
        Item.objects.select_related('category').filter(category=subcategory)
    )


@sync_to_async
def async_get_parent_categories():
    return list(
        Category.objects.select_related('parent_category').filter(parent_category=None)
    )


@sync_to_async
def async_add_to_basket(
        user: User,
        item: Item,
        quantity: int = 1
):
    try:
        basket = Basket.objects.get(user=user, item=item)

        basket.quantity += 1
        basket.save()
    except ObjectDoesNotExist:
        basket = Basket.objects.create(
            item=item, user=user, quantity=quantity
        )

    return basket


@sync_to_async
def async_delete_basket(user_external_id, item_id):
    Basket.objects.get(user__external_id=user_external_id, item__id=item_id).delete()


@sync_to_async
def async_decrement_basket_quantity(user_external_id, item_id):
    basket = Basket.objects.get(user__external_id=user_external_id, item__id=item_id)

    if basket.quantity > 1:
        basket.quantity -= 1
        basket.save()
        return True

    basket.delete()
    return False


@sync_to_async
def async_increment_basket_quantity(user_external_id, item_id):
    basket = Basket.objects.get(user__external_id=user_external_id, item__id=item_id)

    basket.quantity += 1
    basket.save()


@sync_to_async
def async_get_user_baskets(user_id):
    return list(Basket.objects.select_related('item').filter(user__external_id=user_id))


@sync_to_async
def async_get_subcat_parent_id(subcategory: Category):
    return subcategory.parent_category.id


async def async_get_total_basket_price(user_id):
    baskets = await async_get_user_baskets(user_id)
    return sum(basket.quantity * basket.item.price for basket in baskets)

