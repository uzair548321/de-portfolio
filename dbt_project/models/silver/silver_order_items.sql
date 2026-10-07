select
    order_id,
    order_item_id,
    product_id,
    seller_id,
    cast(price as double) as price,
    cast(freight_value as double) as freight_value
from {{ source('bronze', 'olist_order_items') }}
where order_id is not null