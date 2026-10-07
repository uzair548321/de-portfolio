select
    customer_id,
    customer_unique_id,
    customer_city,
    customer_state
from {{ source('bronze', 'olist_customers') }}
where customer_id is not null