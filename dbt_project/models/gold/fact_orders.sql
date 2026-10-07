with items as (
    select order_id,
           sum(price) as items_value,
           sum(freight_value) as freight_value
    from {{ ref('silver_order_items') }}
    group by 1
),
payments as (
    select order_id, sum(payment_value) as paid_value
    from {{ ref('silver_order_payments') }}
    group by 1
)
select
    o.order_id,
    o.customer_id,
    o.order_status,
    o.purchased_at,
    o.delivered_at,
    coalesce(i.items_value, 0) as items_value,
    coalesce(i.freight_value, 0) as freight_value,
    coalesce(p.paid_value, 0) as paid_value
from {{ ref('silver_orders') }} o
left join items i using (order_id)
left join payments p using (order_id)