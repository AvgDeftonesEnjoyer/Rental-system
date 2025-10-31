from re import L
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_API_KEY

def ensure_customer(user) -> str:
    """Ensure a Stripe customer exists for the user."""
    customer = stripe.Customer.create(
        email = user.email,
        name = user.get_username() or f'User {user.id}'
        metadata = {
            'app_user_id': str(user.id)
        }
    )

    return customer['id']

def create_hold_intent(customer_id: str, amount_minor: int) -> str:
    """Create a Stripe hold intent for the customer."""
    intent = stripe.PaymentIntent.create(
        amount = amount_minor,
        currency = settings.RENTAL_CURRENCY,
        customer = customer_id,
        setup_future_usage = 'off_session',
        automatic_payment_methods = {'enabled': True},
    )
    return intent

def cancel_hold_intent(intent_id: str) -> bool:
    return stripe.PaymentIntent.cancel(intent_id)

def charge_final_amount(customer_id: str, payment_method_id: str, amount_minor: int, currency: str, idempotency_key: str):
    intent = stripe.PaymentIntent.create(
        amount = amount_minor,
        currency = currency,
        customer = customer_id,
        payment_method = payment_method_id,
        confirm = True,
        off_session = True,
        automatic_payment_methods = {'enabled':True}
        idempotency_key = idempotency_key,
    )
    return intent