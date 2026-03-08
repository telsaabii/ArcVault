#-----------------------------------------
"""
curl -X POST "http://127.0.0.1:8000/ingest" \
     -H "Content-Type: application/json" \
     -d '{
           "message": "Hi, I tried logging in this morning and keep getting a 403 error. My account is arcvault.io/user/jsmith. This started after your update last Tuesday.",
           "source": "email",
           "sender": "jsmith@example.com"
         }'
"""

#-----------------------------------------
"""
curl -X POST "http://127.0.0.1:8000/ingest" \
     -H "Content-Type: application/json" \
     -d '{
           "message": "We'\''d love to see a bulk export feature for our audit logs. We'\''re a compliance-heavy org and this would save us hours every month.",
           "source": "web_form",
           "sender": "compliance_officer@fintech.com"
         }'
"""
#-----------------------------------------
"""
curl -X POST "http://127.0.0.1:8000/ingest" \
     -H "Content-Type: application/json" \
     -d '{
           "message": "Invoice #8821 shows a charge of $1,240 but our contract rate is $980/month. Can someone look into this?",
           "source": "support_portal",
           "sender": "billing@clientcorp.com"
         }'
"""
#-----------------------------------------
"""
curl -X POST "http://127.0.0.1:8000/ingest" \
     -H "Content-Type: application/json" \
     -d '{
           "message": "I'\''m not sure if this is the right place to ask, but is there a way to set up SSO with Okta? We'\''re evaluating switching our auth provider.",
           "source": "email",
           "sender": "it_admin@evaluator.com"
         }'
"""
#-----------------------------------------
"""
curl -X POST "http://127.0.0.1:8000/ingest" \
     -H "Content-Type: application/json" \
     -d '{
           "message": "Your dashboard stopped loading for us around 2pm EST. Checked our end — it'\''s definitely on yours. Multiple users affected.",
           "source": "web_form",
           "sender": "angry_customer@techcorp.com"
         }'
"""