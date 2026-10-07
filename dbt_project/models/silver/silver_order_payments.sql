select
    order_id,
    payment_sequential,
    payment_type,
    cast(payment_installments as integer) as payment_installments,
    cast(payment_value as double) as payment_value
from {{ source('bronze', 'olist_order_payments') }}
where order_id is not null