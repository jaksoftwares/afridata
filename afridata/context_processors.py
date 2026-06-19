def contact_info(request):
    """
    Global context processor to provide consistent contact information
    across the entire AfriData platform.
    """
    return {
        'CONTACT_EMAIL': 'info.jhub@jkuat.ac.ke',
        'CONTACT_PHONE': '+254 67 52181/4 LAN Ext 2814',
        'CONTACT_ADDRESS': 'Jomo Kenyatta University of Agriculture and Technology, P.O. BOX: 62000-00200, Nairobi, Kenya',
        'CONTACT_OFFICE': 'Jomo Kenyatta University of Agriculture and Technology',
        'CONTACT_PO_BOX': 'P.O. BOX: 62000-00200, Nairobi, Kenya',
        'BUSINESS_HOURS': 'Mon-Fri, 8:00 AM - 5:00 PM (EAT)',
        'SOCIAL_FACEBOOK': 'https://www.facebook.com/JHUBAfrica/',
        'SOCIAL_TWITTER': 'https://x.com/JHUBAfrica',
        'SOCIAL_LINKEDIN': 'https://ke.linkedin.com/company/jhubafrica',
        'SOCIAL_TIKTOK': 'https://www.tiktok.com/@jhubafrica',
    }
