import stripe

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from billing.models import Payment

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events."""
    payload = request.body
    sig = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400, content=f'Webhook verification failed: {e}')
    
    # Handle payment_intent.succeeded event
    if event['type'] == 'payment_intent.succeeded':
        pi = event['data']['object']
        pi_id = pi['id']
        pm_id = pi.get('payment_method')
        
        # Find payment by hold_intent_id (when hold is confirmed)
        payment = Payment.objects.filter(stripe_hold_intent_id=pi_id).first()
        if payment and pm_id and not payment.stripe_payment_method_id:
            payment.stripe_payment_method_id = pm_id
            payment.status = Payment.Status.AUTHORIZED
            payment.save(update_fields=['stripe_payment_method_id', 'status'])
        
        # Find payment by final_intent_id (when final charge succeeds)
        payment = Payment.objects.filter(stripe_final_intent_id=pi_id).first()
        if payment:
            payment.status = Payment.Status.CAPTURED
            payment.save(update_fields=['status'])
    
    # Handle payment_intent.payment_failed event
    elif event['type'] == 'payment_intent.payment_failed':
        pi = event['data']['object']
        pi_id = pi['id']
        
        # Update payment status if hold or final payment failed
        payment = Payment.objects.filter(stripe_hold_intent_id=pi_id).first()
        if not payment:
            payment = Payment.objects.filter(stripe_final_intent_id=pi_id).first()
        
        if payment:
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=['status'])
        
    return HttpResponse(status=200, content='Webhook processed')