# -*- coding: utf-8 -*-
{
    'name': "Reporting for climbing gym",
    # climbing_gym_report
    'summary': """
        Reporting for the climbing gym""",

    'description': """
        Reporting for the climbing gym
    """,

    'author': "Miguel Hatrick",
    'website': "http://www.dacosys.com",

    'category': 'Climbing Gym',
    'version': '12.0.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'climbing_gym', 'mass_mailing'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/digest_data.xml',
        'data/mass_mail.xml',
        'views/email_report.xml',
        'views/dashboard.xml',
        'views/report/email_report.xml',
        'views/menu.xml'


    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
