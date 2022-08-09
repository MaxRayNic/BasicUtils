default_config = {
    'html_template': 'templates/invoice_style_1/index.html',
    'css_template': 'templates/invoice_style_1/style1.css',
    'file_name_format': 'output_dir/Invoice_{user_name}.pdf',
}

csv_sample_config = {
    'datasource_configuration': {
        'file_name': 'static/sample.csv',
        'separator': '|'
    }, 'datasource_type': 'csv',
    **default_config
}
