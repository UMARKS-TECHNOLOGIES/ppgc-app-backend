import random
from ppgc_backend.app.utils.store import (
    send_email,
    substituted_string,
    read_email_from_html_template_name,
)

async def send_email_verification_code(
    user_name: str,
    email_address: str, 
):
    code = '{:04d}'.format(random.randint(0, 9999))
    # call the email function and send the email
    # extract the email content from the template
    email_template_content = read_email_from_html_template_name('email_verification_code_template')
    property_street_address = "Port Harcourt"
    
    email_string = substituted_string(
        email_template_content,
        {
            "user_name":user_name,
            "verification_code":code,
            "prince_paradise_address": property_street_address
        }
    )
    from_address="team@stackfinancialsolutions.com"
    subject="PPGC Verification Code"
    from_name="Prince Paradise"
    #to_name="Customer"

    send_email(
        from_email=from_address,
        to_email=email_address,
        from_name=from_name,
        subject=subject,
        html_email=email_string
    )

    return code

async def send_password_reset_code(
    email_address: str, 
):
    # Generate a new five-digit code
    code = '{:05d}'.format(random.randint(0, 9999))

    # call the email function and send the email
    # extract the email content from the template
    email_template_content = read_email_from_html_template_name('password_reset_template')
    prince_paradise_address = "Port Harcourt"
    
    email_string = substituted_string(
        email_template_content,
        {
            "reset_code":code,
            "prince_paradise_address": prince_paradise_address
        }
    )
    from_address="team@stackfinancialsolutions.com"
    subject="PPGC Verification Code"
    from_name="Prince Paradise"
    #to_name="Customer"

    send_email(
        from_email=from_address,
        to_email=email_address,
        from_name=from_name,
        subject=subject,
        html_email=email_string
    )

    return code