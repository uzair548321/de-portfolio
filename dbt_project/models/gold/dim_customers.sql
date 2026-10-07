select
    customer_id,
    customer_unique_id,
    customer_city,
    customer_state
from {{ ref('silver_customers') }}